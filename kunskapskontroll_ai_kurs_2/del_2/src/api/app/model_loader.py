
import io
import joblib
import logging
from functools import lru_cache
from .settings import settings
from .blob_store import get_blob_service, download_bytes

#Fetch correct logger
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_model_bundle():
    if not settings.storage_account_name:
        raise RuntimeError("STORAGE_ACCOUNT_NAME is not set")
    
    logger.warning("Loading model bundle...")
    
    logger.warning(f"Using storage account: {settings.storage_account_name}")
    logger.warning(f"Using blob container: {settings.blob_container_name}")
    logger.warning(f"Using models prefix: {settings.models_prefix}")

    bs = get_blob_service(settings.storage_account_name)
    model_blob = f"{settings.models_prefix}/model.joblib"
    mapie_blob = f"{settings.models_prefix}/mapie.joblib"
    features_blob = f"{settings.models_prefix}/features.joblib"

    model_bytes = download_bytes(bs, settings.blob_container_name, model_blob)
    mapie_bytes = download_bytes(bs, settings.blob_container_name, mapie_blob)
    features_bytes = download_bytes(bs, settings.blob_container_name, features_blob)

    model = joblib.load(io.BytesIO(model_bytes))
    mapie = joblib.load(io.BytesIO(mapie_bytes))
    features = joblib.load(io.BytesIO(features_bytes))
    return model, mapie, features
