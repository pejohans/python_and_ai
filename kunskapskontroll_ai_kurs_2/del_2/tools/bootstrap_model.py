
import argparse
import io
import json
import datetime
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from mapie.regression import MapieRegressor

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
    symbols = ["ERIC-B","VOLV-B","ATCO-A","ATCO-B","SAND","SEB-A","SWED-A","SHB-A","NDA-SE","TELIA"]
    rng = np.random.default_rng(42)
    feats = pd.DataFrame({
        "symbol": symbols,
        "reco_pos": rng.uniform(0.3, 0.8, len(symbols)),
        "reco_neg": rng.uniform(0.0, 0.4, len(symbols)),
        "reco_net": rng.uniform(-0.2, 0.4, len(symbols)),
        "reco_pos_delta": rng.normal(0.0, 0.05, len(symbols)),
        "as_of_date": datetime.date.today().isoformat()
    })
    feats["y"] = feats["reco_net"] * 0.05 + rng.normal(0, 0.02, len(symbols))

    X = feats[["reco_pos","reco_neg","reco_net","reco_pos_delta"]].values
    y = feats["y"].values

    X_train, X_cal, y_train, y_cal = train_test_split(X, y, test_size=0.2, random_state=42)
    base = RandomForestRegressor(n_estimators=200, random_state=42)
    base.fit(X_train, y_train)

    mapie = MapieRegressor(estimator=base, method='naive')
    mapie.fit(X_train, y_train)
    mapie.conformalize(X_cal, y_cal)

    # Serialize
    mb = io.BytesIO(); joblib.dump(base, mb)
    pb = io.BytesIO(); joblib.dump(mapie, pb)

    # Upload model
    upload(bs, args.container, f"{args.models_prefix}/model.joblib", mb.getvalue())
    upload(bs, args.container, f"{args.models_prefix}/mapie.joblib", pb.getvalue())

    metadata = {
        "run_date": datetime.date.today().isoformat(),
        "horizon_days": 7,
        "note": "bootstrap synthetic baseline model - replace with nightly trained model"
    }
    upload(bs, args.container, f"{args.models_prefix}/metadata.json", json.dumps(metadata, indent=2).encode('utf-8'))

    # Upload features parquet + latest pointer
    fb = io.BytesIO(); feats.drop(columns=['y']).to_parquet(fb, index=False)
    features_blob = f"{args.features_prefix}/latest/features.parquet"
    upload(bs, args.container, features_blob, fb.getvalue())

    latest_ptr = {"features_blob": features_blob, "run_date": metadata["run_date"], "horizon_days": 7}
    upload(bs, args.container, f"{args.features_prefix}/_latest.json", json.dumps(latest_ptr, indent=2).encode('utf-8'))

    print('Bootstrap complete.')


if __name__ == '__main__':
    main()
