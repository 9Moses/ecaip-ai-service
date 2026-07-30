import io

import boto3
from botocore.client import Config

from app.core.config import get_settings

settings = get_settings()


def get_storage_client():
    protocol = "https" if settings.minio_use_ssl else "http"
    return boto3.client(
        "s3",
        endpoint_url=f"{protocol}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
    )


def upload_file(storage_path: str, content: bytes) -> None:
    client = get_storage_client()
    client.put_object(Bucket=settings.minio_bucket, key=storage_path, Body=io.BytesIO(content))


def download_file(storage_path: str) -> bytes:
    client = get_storage_client()
    obj = client.get_object(Bucket=settings.minio_bucket, Key=storage_path)
    return obj["Body"].read()


def file_exists(storage_path: str) -> bool:
    client = get_storage_client()
    try:
        client.head_object(Bucket=settings.minio_bucket, Key=storage_path)
        return True
    except client.exceptions.ClientError:
        return False
