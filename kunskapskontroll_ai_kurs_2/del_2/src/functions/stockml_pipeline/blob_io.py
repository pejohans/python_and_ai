
import io
import json
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


def _account_url(account_name: str) -> str:
    return f"https://{account_name}.blob.core.windows.net"


def get_blob_service(account_name: str) -> BlobServiceClient:
    cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    return BlobServiceClient(account_url=_account_url(account_name), credential=cred)


def upload_bytes(bs: BlobServiceClient, container: str, blob_path: str, data: bytes, overwrite: bool = True):
    bc = bs.get_blob_client(container=container, blob=blob_path)
    bc.upload_blob(data, overwrite=overwrite)


def upload_json(bs: BlobServiceClient, container: str, blob_path: str, obj, overwrite: bool = True):
    data = json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8')
    upload_bytes(bs, container, blob_path, data, overwrite)


def upload_parquet(bs: BlobServiceClient, container: str, blob_path: str, df):
    bio = io.BytesIO()
    df.to_parquet(bio, index=False)
    upload_bytes(bs, container, blob_path, bio.getvalue(), overwrite=True)


def download_bytes(bs: BlobServiceClient, container: str, blob_path: str) -> bytes:
    bc = bs.get_blob_client(container=container, blob=blob_path)
    return bc.download_blob().readall()


def exists(bs: BlobServiceClient, container: str, blob_path: str) -> bool:
    bc = bs.get_blob_client(container=container, blob=blob_path)
    return bc.exists()
