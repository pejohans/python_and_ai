
import io
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from mapie.regression import SplitConformalRegressor


FEATURE_COLS = ["reco_pos","reco_neg","reco_net","reco_pos_delta"]


def build_trainset(features_df: pd.DataFrame) -> pd.DataFrame:
    """MVP: Skapar en syntetisk label y (return) som placeholder.

    Byt detta till riktig label-byggare baserad på prisdata:
    y = (price_t+7 - price_t) / price_t
    """
    df = features_df.copy()
    rng = np.random.default_rng(42)
    # placeholder y: svagt korrelerad med reco_net
    noise = rng.normal(0, 0.02, size=len(df))
    df["y"] = df["reco_net"].astype(float) * 0.05 + noise
    return df


def train_model(train_df: pd.DataFrame):
    X = train_df[FEATURE_COLS].values
    y = train_df["y"].values

    X_train, X_cal, y_train, y_cal = train_test_split(X, y, test_size=0.2, random_state=42)

    base = RandomForestRegressor(n_estimators=300, random_state=42, min_samples_leaf=3)
    base.fit(X_train, y_train)

    #mapie = MapieRegressor(estimator=base, method="naive")
    #mapie.fit(X_train, y_train)
    #mapie.conformalize(X_cal, y_cal)
    
    mapie = SplitConformalRegressor(
        estimator=base,
        confidence_level=0.95   # motsvarar 95% intervall
    )    
    
    mapie.fit(
        X_train,
        y_train,
        X_calibration=X_cal,
        y_calibration=y_cal
    )

    # simple metric
    preds = base.predict(X_cal)
    rmse = float(np.sqrt(np.mean((preds - y_cal) ** 2)))

    metrics = {
        "rmse_cal": rmse,
        "n_train": int(len(X_train)),
        "n_cal": int(len(X_cal))
    }

    return base, mapie, metrics


def serialize_joblib(obj) -> bytes:
    bio = io.BytesIO()
    joblib.dump(obj, bio)
    return bio.getvalue()
