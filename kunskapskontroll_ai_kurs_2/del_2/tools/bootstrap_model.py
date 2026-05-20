
import argparse
import io
import json
import datetime
from pyexpat import model
import numpy as np
import pandas as pd
import joblib

from lightgbm import LGBMRegressor
from sklearn.model_selection import train_test_split
from mapie.regression import SplitConformalRegressor

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


def account_url(name: str) -> str:
    return f"https://{name}.blob.core.windows.net"


def upload(bs, container, blob, data: bytes):
    bc = bs.get_blob_client(container=container, blob=blob)
    bc.upload_blob(data, overwrite=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--storage-account', required=True)
    ap.add_argument('--container', required=True)
    ap.add_argument('--models-prefix', required=True)
    ap.add_argument('--features-prefix', required=True)
    args = ap.parse_args()

    cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    bs = BlobServiceClient(account_url=account_url(args.storage_account), credential=cred)

    # Create a tiny baseline dataset (synthetic) so API can start.
    symbols = ["ERIC-B.ST","VOLV-B.ST","ATCO-A.ST","ATCO-B.ST","SAND.ST","SEB-A.ST","SWED-A.ST","SHB-A.ST","NDA-SE.ST","TELIA.ST"]
    rng = np.random.default_rng(42)
   
    feats = pd.DataFrame({
        "symbol": symbols,
        "symbol_id": range(len(symbols)), 
        "ret_1d": rng.normal(0, 0.01, len(symbols)),
        "ret_3d": rng.normal(0, 0.02, len(symbols)),
        "ret_7d": rng.normal(0, 0.03, len(symbols)),
        "vol_7d": rng.uniform(0.01, 0.05, len(symbols)),
        "vol_14d": rng.uniform(0.01, 0.06, len(symbols)),
        "price_vs_ma5": rng.uniform(0.95, 1.05, len(symbols)),
        "price_vs_ma10": rng.uniform(0.95, 1.05, len(symbols)),
        "recent_price": rng.uniform(50, 300, len(symbols)), 
        "as_of_date": datetime.date.today().isoformat()
    })

    #feats["y"] = feats["reco_net"] * 0.05 + rng.normal(0, 0.02, len(symbols))
    feats["target_return"] = rng.normal(0, 0.03, len(symbols))

    #X = feats[["reco_pos","reco_neg","reco_net","reco_pos_delta"]].values
    
    features = [
        "symbol_id",
        "ret_1d",
        "ret_3d",
        "ret_7d",
        "vol_7d",
        "vol_14d",
        "price_vs_ma5",
        "price_vs_ma10"
    ]
    X = feats[features].values

    y = feats["target_return"].values

    X_train, X_cal, y_train, y_cal = train_test_split(X, y, test_size=0.2, random_state=42)
    #base = RandomForestRegressor(n_estimators=200, random_state=42)   
    
    base = LGBMRegressor(
        learning_rate=0.01,
        max_depth=5,
        n_estimators=100,
        num_leaves=31,
        random_state=42
    )
    base.fit(X_train, y_train)

    mapie = SplitConformalRegressor(
        estimator=base,
        confidence_level=0.9,   # motsvarar 90% intervall
        prefit=True #Train model first, then conformalize with calibration set
    )
    mapie.conformalize(X_cal, y_cal)

    # Mapping from symbol to symbol_id for later use in API
    symbol_map = {s: i for i, s in enumerate(symbols)}

    # Serialize
    mb = io.BytesIO(); joblib.dump(base, mb)
    pb = io.BytesIO(); joblib.dump(mapie, pb)

    # Upload model
    upload(bs, args.container, f"{args.models_prefix}/model.joblib", mb.getvalue())
    upload(bs, args.container, f"{args.models_prefix}/mapie.joblib", pb.getvalue())
    
    
    sb = io.BytesIO(); joblib.dump(symbol_map, sb)
    upload(bs, args.container, f"{args.models_prefix}/symbol_map.joblib", sb.getvalue())

    fb2 = io.BytesIO(); joblib.dump(features, fb2)
    upload(bs, args.container, f"{args.models_prefix}/features.joblib", fb2.getvalue())


    metadata = {
        "run_date": datetime.date.today().isoformat(),
        "horizon_days": 7,
        "model_type": "LGBM + SplitConformalRegressor",
        "features": features,
        "confidence_level": 0.9,
        "note": "bootstrap baseline model using synthetic financial features - replace with nightly trained model"
    }
    upload(bs, args.container, f"{args.models_prefix}/metadata.json", json.dumps(metadata, indent=2).encode('utf-8'))

    # Upload features parquet + latest pointer
    fb = io.BytesIO(); feats.drop(columns=['target_return']).to_parquet(fb, index=False)
    features_blob = f"{args.features_prefix}/latest/features.parquet"
    upload(bs, args.container, features_blob, fb.getvalue())

    latest_ptr = {
        "features_blob": features_blob,         
        #"model_blob": f"{MODELS_PREFIX}/model.joblib", #TODO: Need to pass prefix from azure-pipelines.yml file. Implement later if needed to load model from same place, right now we hard code the path to blob storage, which might not be a problem
        #"mapie_blob": f"{MODELS_PREFIX}/mapie.joblib", #TODO: Need to pass prefix from azure-pipelines.yml file. Implement later if needed to load model from same place, right now we hard code the path to blob storage, which might not be a problem
        "run_date": metadata["run_date"], 
        "horizon_days": 7
        }
    upload(bs, args.container, f"{args.features_prefix}/_latest.json", json.dumps(latest_ptr, indent=2).encode('utf-8'))

    print('Bootstrap complete.')


if __name__ == '__main__':
    main()
