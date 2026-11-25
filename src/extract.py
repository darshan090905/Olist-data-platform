import os
from pathlib import Path
import boto3
from botocore.exceptions import ClientError


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.environ.get("S3_KEY", "minio"),
        aws_secret_access_key=os.environ.get("S3_SECRET", "minio12345"),
    )


def upload_raw() -> list[str]:
    s3 = get_s3_client()
    bucket_name = "raw"

    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError:
        s3.create_bucket(Bucket=bucket_name)

    raw_dir = Path(os.environ.get("RAW_DATA_DIR", "data/raw"))
    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")

    uploaded: list[str] = []
    for f in csv_files:
        s3.upload_file(str(f), bucket_name, f.name)
        uploaded.append(f.name)
        print("uploaded", f.name)

    return uploaded


if __name__ == "__main__":
    upload_raw()
