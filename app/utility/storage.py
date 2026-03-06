import logging
import os

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


async def generate_presigned_url(key: str, expires_in: int = 300, download_filename: str = "") -> str:
    """Generate a presigned URL for a file in the bucket.

    Args:
        key: The S3 object key.
        expires_in: URL expiry time in seconds (default 300 = 5 minutes).
        download_filename: If provided, the browser will download the file with this name.

    Returns:
        A presigned URL string.
    """
    endpoint_url = _get_endpoint_url()
    if not endpoint_url:
        return key

    params = {"Bucket": BUCKET_NAME, "Key": key}
    if download_filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{download_filename}"'

    session = aioboto3.Session()
    async with session.client(
        "s3",
        region_name=REGION,
        endpoint_url=endpoint_url,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    ) as s3:
        url = await s3.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )
    return url


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
