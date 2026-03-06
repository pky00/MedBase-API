import logging
import os

import aioboto3
from botocore.config import Config

logger = logging.getLogger("medbase.utility.storage")

BUCKET_NAME = os.getenv("LIGHTSAIL_BUCKET_NAME", "")
ACCESS_KEY = os.getenv("LIGHTSAIL_ACCESS_KEY", "")
SECRET_KEY = os.getenv("LIGHTSAIL_SECRET_KEY", "")
ENDPOINT = os.getenv("LIGHTSAIL_ENDPOINT", "")
REGION = os.getenv("LIGHTSAIL_REGION", "")

S3_CONFIG = Config(signature_version="s3v4")


def _s3_client():
    """Create an async S3 client for Lightsail object storage.

    Uses the LIGHTSAIL_ENDPOINT env var as the S3-compatible endpoint URL,
    matching the configuration used by the test script.
    """
    session = aioboto3.Session()
    endpoint_url = f"https://{ENDPOINT}" if ENDPOINT and not ENDPOINT.startswith("http") else ENDPOINT
    kwargs = {
        "region_name": REGION,
        "aws_access_key_id": ACCESS_KEY,
        "aws_secret_access_key": SECRET_KEY,
        "config": S3_CONFIG,
    }
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return session.client("s3", **kwargs)


async def generate_presigned_url(key: str, expires_in: int = 300, download_filename: str = "") -> str:
    """Generate a presigned URL for a file in the bucket.

    Args:
        key: The S3 object key.
        expires_in: URL expiry time in seconds (default 300 = 5 minutes).
        download_filename: If provided, the browser will download the file with this name.

    Returns:
        A presigned URL string.
    """
    params = {"Bucket": BUCKET_NAME, "Key": key}
    if download_filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{download_filename}"'

    async with _s3_client() as s3:
        url = await s3.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )
    return url


async def upload_file(key: str, content: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload a file to the Lightsail bucket. Returns the file key."""
    async with _s3_client() as s3:
        await s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

    logger.info("Uploaded file key='%s' to bucket='%s'", key, BUCKET_NAME)
    return key


async def delete_file(key: str) -> None:
    """Delete a file from the Lightsail bucket."""
    async with _s3_client() as s3:
        await s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=key,
        )

    logger.info("Deleted file key='%s' from bucket='%s'", key, BUCKET_NAME)
