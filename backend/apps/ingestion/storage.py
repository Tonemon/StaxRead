import os
import uuid
from datetime import timedelta
from functools import lru_cache

from django.conf import settings
from minio import Minio


def _extension_from_path(file_path: str) -> str:
    _, ext = os.path.splitext(file_path)
    return ext.lower() if ext else ""


@lru_cache(maxsize=1)
def _get_minio_client() -> Minio:
    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )
    bucket = settings.MINIO_BUCKET
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    return client


def get_minio_client() -> Minio:
    return _get_minio_client()


def upload_file(source_id: uuid.UUID, file_path: str, content_type: str) -> str:
    """
    Upload a file to MinIO under the source's UUID.

    Returns:
        object_name: the MinIO object key (e.g. "documents/<uuid>.pdf")
    """
    client = get_minio_client()
    ext = _extension_from_path(file_path)
    object_name = f"documents/{source_id}{ext}"
    file_size = os.path.getsize(file_path)

    with open(file_path, "rb") as f:
        client.put_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=object_name,
            data=f,
            length=file_size,
            content_type=content_type,
        )
    return object_name


def get_presigned_url(source_id: uuid.UUID, extension: str, expires_hours: int = 1) -> str:
    """
    Generate a presigned GET URL for the source document.

    The MinIO SDK signs the URL with the internal endpoint (e.g. minio:9000).
    We rewrite the origin to /minio so the browser hits nginx, which proxies
    back to minio:9000 with Host: minio:9000 intact — keeping the AWS v4
    signature valid regardless of the public hostname.
    """
    client = get_minio_client()
    ext = extension if extension.startswith(".") else f".{extension}"
    object_name = f"documents/{source_id}{ext}"
    url = client.presigned_get_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=object_name,
        expires=timedelta(hours=expires_hours),
    )
    scheme = "https" if settings.MINIO_USE_SSL else "http"
    internal_origin = f"{scheme}://{settings.MINIO_ENDPOINT}"
    return url.replace(internal_origin, "/minio", 1)
