
import io
import joblib
from functools import lru_cache
from .settings import settings
from .blob_store import get_blob_service, download_bytes


@lru_cache(maxsize=1)
def load_model_bundle():
    if not settings.storage_account_name:
        raise RuntimeError("STORAGE_ACCOUNT_NAME is not set")

    bs = get_blob_service(settings.storage_account_name)
    model_blob = f"{settings.models_prefix}/model.joblib"
    mapie_blob = f"{settings.models_prefix}/mapie.joblib"

    model_bytes = download_bytes(bs, settings.blob_container_name, model_blob)
    mapie_bytes = download_bytes(bs, settings.blob_container_name, mapie_blob)

    model = joblib.load(io.BytesIO(model_bytes))
    mapie = joblib.load(io.BytesIO(mapie_bytes))
    return model, mapie
