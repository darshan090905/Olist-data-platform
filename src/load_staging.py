import os
import boto3
import pandas as pd
from sqlalchemy import create_engine, text
from src.config import WAREHOUSE_URL

FILE_TO_TABLE = {
    "olist_customers_dataset.csv": "stg_customers",
    "olist_geolocation_dataset.csv": "stg_geolocation",
    "olist_order_items_dataset.csv": "stg_order_items",
    "olist_order_payments_dataset.csv": "stg_order_payments",
    "olist_order_reviews_dataset.csv": "stg_order_reviews",
    "olist_orders_dataset.csv": "stg_orders",
    "olist_products_dataset.csv": "stg_products",
    "olist_sellers_dataset.csv": "stg_sellers",
    "product_category_name_translation.csv": "stg_product_category_translation",
}


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.environ.get("S3_KEY", "minio"),
        aws_secret_access_key=os.environ.get("S3_SECRET", "minio12345"),
    )


def load_staging() -> dict[str, int]:
    engine = create_engine(WAREHOUSE_URL)
    s3 = get_s3_client()
    row_counts: dict[str, int] = {}

    with engine.begin() as conn:
        for filename, table_name in FILE_TO_TABLE.items():
            obj = s3.get_object(Bucket="raw", Key=filename)
            df = pd.read_csv(obj["Body"])
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
            df.to_sql(
                name=table_name,
                con=conn,
                if_exists="replace",
                index=False,
                chunksize=5000,
                method="multi",
            )
            row_counts[table_name] = len(df)
            print(f"Loaded {len(df):,} rows from s3://raw/{filename} into {table_name}")

    return row_counts


if __name__ == "__main__":
    load_staging()
