from __future__ import annotations

import io
import os

from minio import Minio
from minio.error import S3Error

_client: Minio | None = None

BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "ama")


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
        )
        _ensure_bucket(_client)
    return _client


def _ensure_bucket(client: Minio) -> None:
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)


def upload_file(object_key: str, data: bytes, content_type: str = "image/jpeg") -> str:
    client = get_minio_client()
    client.put_object(
        BUCKET_NAME,
        object_key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return object_key


def download_file(object_key: str) -> bytes:
    client = get_minio_client()
    response = client.get_object(BUCKET_NAME, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def delete_file(object_key: str) -> None:
    try:
        client = get_minio_client()
        client.remove_object(BUCKET_NAME, object_key)
    except S3Error:
        pass
