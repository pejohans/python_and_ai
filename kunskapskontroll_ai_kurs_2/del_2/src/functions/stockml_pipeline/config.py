
import os

BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME", "stockml")
STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME", "")

# Prefixes
RAW_PREFIX = os.getenv("RAW_PATH_PREFIX", "raw/omx30")
FEATURES_PREFIX = os.getenv("FEATURES_PATH_PREFIX", "curated/omx30/features/horizon=7")
TRAINSET_PREFIX = os.getenv("TRAINSET_PATH_PREFIX", "curated/omx30/trainset/horizon=7")
MODELS_PREFIX = os.getenv("MODELS_PATH_PREFIX", "models/omx30/horizon=7")

OMX30_SYMBOLS = os.getenv(
    "OMX30_SYMBOLS",
    "ERIC-B,VOLV-B,ATCO-A,ATCO-B,SAND,SEB-A,SWED-A,SHB-A,NDA-SE,TELIA"
)


def get_symbols():
    return [s.strip().upper() for s in OMX30_SYMBOLS.split(",") if s.strip()]
