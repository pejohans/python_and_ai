
import io
import pandas as pd
import logging
from functools import lru_cache
from .settings import settings
from .blob_store import get_blob_service, download_bytes

logger = logging.getLogger(__name__)


@lru_cache(maxsize=8)
def load_latest_features_df():
    # For MVP: assume Function writes a "latest" pointer file.
    # If you prefer partitioned by date only, change this to list and pick latest.
    if not settings.storage_account_name:
        raise RuntimeError("STORAGE_ACCOUNT_NAME is not set")
    
    logger.info("Loading latest features...")
    logger.info(f"Using storage account: {settings.storage_account_name}")
    logger.info(f"Using blob container: {settings.blob_container_name}")
    logger.info(f"Using features prefix: {settings.features_prefix}")

    bs = get_blob_service(settings.storage_account_name)
    latest_ptr = f"{settings.features_prefix}/_latest.json"
    ptr = None
    try:
        ptr_bytes = download_bytes(bs, settings.blob_container_name, latest_ptr)
        ptr = pd.read_json(io.BytesIO(ptr_bytes), typ='series').to_dict()
    except Exception:
        # fallback to conventional path
        ptr = {"features_blob": f"{settings.features_prefix}/latest/features.parquet"}

    features_blob = ptr.get("features_blob")
    data = download_bytes(bs, settings.blob_container_name, features_blob)
    return pd.read_parquet(io.BytesIO(data))


def get_features_for_symbol(symbol: str) -> pd.DataFrame:
    df = load_latest_features_df()
    s = symbol.upper()
    row = df[df["symbol"] == s]
    if row.empty:
        raise ValueError(f"No features found for symbol {s}")
    # drop non-feature columns
    return row.drop(columns=[c for c in ["symbol","as_of_date"] if c in row.columns])
