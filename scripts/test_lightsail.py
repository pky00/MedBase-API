"""Test script to verify Lightsail bucket connectivity by uploading a simple text file."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import aioboto3

load_dotenv()

BUCKET_NAME = os.getenv("LIGHTSAIL_BUCKET_NAME")
ACCESS_KEY = os.getenv("LIGHTSAIL_ACCESS_KEY")
SECRET_KEY = os.getenv("LIGHTSAIL_SECRET_KEY")
ENDPOINT = os.getenv("LIGHTSAIL_ENDPOINT")
REGION = os.getenv("LIGHTSAIL_REGION")


async def test_upload():
    print("Lightsail Bucket Config:")
    print(f"  Bucket:   {BUCKET_NAME}")
    print(f"  Endpoint: {ENDPOINT}")
    print(f"  Region:   {REGION}")
    print()

    session = aioboto3.Session()
    endpoint_url = f"https://{ENDPOINT}" if not ENDPOINT.startswith("http") else ENDPOINT

    async with session.client(
        "s3",
        region_name=REGION,
        endpoint_url=endpoint_url,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    ) as s3:
        # Upload a test file
        test_content = b"Hello from MedBase! This is a test upload."
        test_key = "test/hello.txt"

        print(f"Uploading '{test_key}' to bucket '{BUCKET_NAME}'...")
        await s3.put_object(
            Bucket=BUCKET_NAME,
            Key=test_key,
            Body=test_content,
            ContentType="text/plain",
        )
        print("Upload successful!")

        # Verify by reading it back
        print(f"Reading back '{test_key}'...")
        response = await s3.get_object(Bucket=BUCKET_NAME, Key=test_key)
        body = await response["Body"].read()
        print(f"Content: {body.decode()}")

        # # Clean up
        # print(f"Deleting '{test_key}'...")
        # await s3.delete_object(Bucket=BUCKET_NAME, Key=test_key)
        # print("Deleted.")

    print("\nAll tests passed! Lightsail bucket is working.")


if __name__ == "__main__":
    asyncio.run(test_upload())
