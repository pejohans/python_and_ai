
import os
import io
import json
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


def _account_url(account_name: str) -> str:
    return f"https://{account_name}.blob.core.windows.net"


def get_blob_service(account_name: str) -> BlobServiceClient:
    # Uses Managed Identity in Azure; locally uses az login / VS Code credential chain.
    cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    return BlobServiceClient(account_url=_account_url(account_name), credential=cred)


def download_bytes(bs: BlobServiceClient, container: str, blob_path: str) -> bytes:
    bc = bs.get_blob_client(container=container, blob=blob_path)
    stream = bc.download_blob()
    return stream.readall()


def download_json(bs: BlobServiceClient, container: str, blob_path: str):
    data = download_bytes(bs, container, blob_path)
    return json.loads(data.decode('utf-8'))


def exists(bs: BlobServiceClient, container: str, blob_path: str) -> bool:
    bc = bs.get_blob_client(container=container, blob=blob_path)
    return bc.exists()
