
from pydantic import BaseModel
import os

class Settings(BaseModel):
    storage_account_name: str = os.getenv("STORAGE_ACCOUNT_NAME", "")
    blob_container_name: str = os.getenv("BLOB_CONTAINER_NAME", "stockml")
    features_prefix: str = os.getenv("FEATURES_PATH_PREFIX", "curated/omx30/features/horizon=7")
    models_prefix: str = os.getenv("MODELS_PATH_PREFIX", "models/omx30/horizon=7")
    horizon_days: int = int(os.getenv("HORIZON_DAYS", "7"))
    omx30_symbols: str = os.getenv("OMX30_SYMBOLS", "")

    @property
    def symbol_whitelist(self):
        if not self.omx30_symbols.strip():
            # fallback (kort lista) – byt till komplett OMX30 i env
            return {
                "ERIC-B","VOLV-B","ATCO-A","ATCO-B","SAND","SEB-A","SWED-A","SHB-A","NDA-SE","TELIA"
            }
        return {s.strip().upper() for s in self.omx30_symbols.split(",") if s.strip()}

settings = Settings()
