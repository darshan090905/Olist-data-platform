import os

WAREHOUSE_URL = os.getenv(
    "WAREHOUSE_URL",
    "postgresql+psycopg2://dwh:dwh@localhost:5433/olist",
)
RAW_DATA_DIR = os.getenv("RAW_DATA_DIR", "data/raw")
