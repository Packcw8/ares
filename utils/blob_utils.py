import boto3
import os
from uuid import uuid4

# 🔐 Backblaze B2 (S3-compatible) ENV VARS — MATCH RENDER
B2_ENDPOINT = os.getenv("B2_ENDPOINT_URL")
B2_BUCKET = os.getenv("B2_BUCKET_NAME")
B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APP_KEY = os.getenv("B2_APPLICATION_KEY")

if not all([B2_ENDPOINT, B2_BUCKET, B2_KEY_ID, B2_APP_KEY]):
    raise RuntimeError("❌ Missing Backblaze B2 environment variables")

s3 = boto3.client(
    "s3",
    endpoint_url=B2_ENDPOINT,
    aws_access_key_id=B2_KEY_ID,
    aws_secret_access_key=B2_APP_KEY,
)

def generate_presigned_upload(filename: str, content_type: str):
    key = f"evidence/{uuid4()}_{filename}"

    upload_url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": B2_BUCKET,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=3600,  # 1 hour
    )

    file_url = f"{B2_ENDPOINT}/{B2_BUCKET}/{key}"

    return {
        "upload_url": upload_url,
        "file_url": file_url,
        "key": key,
    }
