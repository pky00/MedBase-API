import logging
import os
from typing import Optional

import aioboto3

logger = logging.getLogger("medbase.utility.storage")

BUCKET_NAME = os.getenv("LIGHTSAIL_BUCKET_NAME", "")
ACCESS_KEY = os.getenv("LIGHTSAIL_ACCESS_KEY", "")
SECRET_KEY = os.getenv("LIGHTSAIL_SECRET_KEY", "")
ENDPOINT = os.getenv("LIGHTSAIL_ENDPOINT", "")
REGION = os.getenv("LIGHTSAIL_REGION", "")


def _get_endpoint_url() -> str:
    """Build the endpoint URL."""
    if not ENDPOINT:
        return ""
    return f"https://{ENDPOINT}" if not ENDPOINT.startswith("http") else ENDPOINT


def get_file_url(key: str) -> str:
    """Get the public URL for a file in the bucket."""
    endpoint_url = _get_endpoint_url()
    if endpoint_url:
        return f"{endpoint_url}/{key}"
    return key


async def upload_file(key: str, content: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload a file to the Lightsail bucket. Returns the file key."""
    endpoint_url = _get_endpoint_url()

    session = aioboto3.Session()
    async with session.client(
        "s3",
        region_name=REGION,
        endpoint_url=endpoint_url,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    ) as s3:
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
    endpoint_url = _get_endpoint_url()

    session = aioboto3.Session()
    async with session.client(
        "s3",
        region_name=REGION,
        endpoint_url=endpoint_url,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    ) as s3:
        await s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=key,
        )

    logger.info("Deleted file key='%s' from bucket='%s'", key, BUCKET_NAME)
