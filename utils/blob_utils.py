import os
import boto3
import uuid

# Required environment variables (Render)
B2_ENDPOINT_URL = os.getenv("B2_ENDPOINT_URL")        # https://s3.us-east-005.backblazeb2.com
B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APPLICATION_KEY = os.getenv("B2_APPLICATION_KEY")
B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")          # ares-evidence

if not all([B2_ENDPOINT_URL, B2_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME]):
    raise RuntimeError("Missing Backblaze B2 environment variables")

s3 = boto3.client(
    "s3",
    endpoint_url=B2_ENDPOINT_URL,
    aws_access_key_id=B2_KEY_ID,
    aws_secret_access_key=B2_APPLICATION_KEY,
)

def upload_file_to_b2(
    *,
    file_obj,
    original_filename: str,
    content_type: str,
    folder: str = "evidence",
) -> str:
    """
    Uploads a file stream to Backblaze B2 and returns the public file URL.
    """

    ext = os.path.splitext(original_filename)[1]
    filename = f"{folder}/{uuid.uuid4()}{ext}"

    s3.upload_fileobj(
        Fileobj=file_obj,
        Bucket=B2_BUCKET_NAME,
        Key=filename,
        ExtraArgs={"ContentType": content_type},
    )

    return f"{B2_ENDPOINT_URL}/{B2_BUCKET_NAME}/{filename}"
