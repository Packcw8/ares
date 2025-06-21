from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from uuid import uuid4
from fastapi import UploadFile
import os

# Azure Storage config
account_url = "https://aresvault123.blob.core.windows.net"
container_name = "evidence-vault"

# Use Azure Managed Identity (DefaultAzureCredential)
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)
container_client = blob_service_client.get_container_client(container_name)

# Upload helper
async def upload_file_to_azure(file: UploadFile) -> str:
    try:
        file_id = str(uuid4())
        blob_name = f"{file_id}_{file.filename}"
        blob_client = container_client.get_blob_client(blob_name)

        file_data = await file.read()
        blob_client.upload_blob(file_data, overwrite=True)

        return blob_client.url
    except Exception as e:
        print(f"[ERROR] Azure blob upload failed: {e}")
        raise
