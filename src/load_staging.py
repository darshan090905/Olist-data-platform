from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from src.config import RAW_DATA_DIR, WAREHOUSE_URL

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


def load_staging() -> dict[str, int]:
    engine = create_engine(WAREHOUSE_URL)
    raw_path = Path(RAW_DATA_DIR)
    row_counts: dict[str, int] = {}

    with engine.begin() as conn:
        for filename, table_name in FILE_TO_TABLE.items():
            csv_file = raw_path / filename
            if not csv_file.exists():
                raise FileNotFoundError(f"Missing raw CSV: {csv_file}")

            df = pd.read_csv(csv_file)
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
            print(f"Loaded {len(df):,} rows into {table_name}")

    return row_counts


if __name__ == "__main__":
    load_staging()
