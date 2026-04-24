
import os
import json
import logging
import pandas as pd

from .config import (
    STORAGE_ACCOUNT_NAME, BLOB_CONTAINER_NAME,
    FEATURES_PREFIX, TRAINSET_PREFIX, MODELS_PREFIX,
    get_symbols
)
from .blob_io import get_blob_service, upload_json, upload_parquet, upload_bytes
from .data_sources import fetch_recommendations
from .feature_engineering import compute_features_for_symbol
from .training import build_trainset, train_model, serialize_joblib


def run_nightly_pipeline(run_date: str, horizon_days: int = 7):
    if not STORAGE_ACCOUNT_NAME:
        raise RuntimeError("STORAGE_ACCOUNT_NAME is not set")

    symbols = get_symbols()
    bs = get_blob_service(STORAGE_ACCOUNT_NAME)

    # 1) build features for all symbols
    feature_rows = []
    for sym in symbols:
        reco_df = fetch_recommendations(sym)
        feat = compute_features_for_symbol(sym, reco_df, as_of_date=run_date)
        feature_rows.append(feat)

    features_df = pd.DataFrame(feature_rows)

    # 2) trainset
    train_df = build_trainset(features_df)

    # 3) train model + conformal
    model, mapie, metrics = train_model(train_df)

    # 4) persist curated features
    features_blob = f"{FEATURES_PREFIX}/dt={run_date}/features.parquet"
    upload_parquet(bs, BLOB_CONTAINER_NAME, features_blob, features_df)

    # write latest pointer
    latest_ptr = {
        "features_blob": features_blob,
        "run_date": run_date,
        "horizon_days": horizon_days
    }
    upload_json(bs, BLOB_CONTAINER_NAME, f"{FEATURES_PREFIX}/_latest.json", latest_ptr)

    # 5) persist trainset (single rolling file for MVP)
    upload_parquet(bs, BLOB_CONTAINER_NAME, f"{TRAINSET_PREFIX}/train.parquet", train_df)

    # 6) persist model bundle
    upload_bytes(bs, BLOB_CONTAINER_NAME, f"{MODELS_PREFIX}/model.joblib", serialize_joblib(model), overwrite=True)
    upload_bytes(bs, BLOB_CONTAINER_NAME, f"{MODELS_PREFIX}/mapie.joblib", serialize_joblib(mapie), overwrite=True)
    upload_json(bs, BLOB_CONTAINER_NAME, f"{MODELS_PREFIX}/metadata.json", {"run_date": run_date, "horizon_days": horizon_days})
    upload_json(bs, BLOB_CONTAINER_NAME, f"{MODELS_PREFIX}/metrics.json", metrics)

    logging.info(f"Saved features to {features_blob} and model to {MODELS_PREFIX}")
