from datetime import datetime, timedelta
from pathlib import Path
import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path("/opt/airflow")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import WAREHOUSE_URL  # noqa: E402
from src.extract import upload_raw  # noqa: E402
from src.load_staging import load_staging  # noqa: E402
from src.quality_checks import run_quality_checks  # noqa: E402


def _run_sql_file(sql_rel_path: str) -> None:
    sql_path = PROJECT_ROOT / sql_rel_path
    sql_text = sql_path.read_text(encoding="utf-8")
    engine = create_engine(WAREHOUSE_URL)
    with engine.begin() as conn:
        conn.execute(text(sql_text))


default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(seconds=15),
}

with DAG(
    dag_id="olist_batch_etl",
    default_args=default_args,
    description="Batch ETL pipeline for Olist e-commerce data warehouse",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["olist", "etl", "warehouse"],
) as dag:
    extract_raw = PythonOperator(
        task_id="extract_to_minio",
        python_callable=upload_raw,
    )

    t_staging = PythonOperator(
        task_id="load_staging",
        python_callable=load_staging,
    )

    t_dims = PythonOperator(
        task_id="load_dimensions",
        python_callable=_run_sql_file,
        op_kwargs={"sql_rel_path": "sql/02_load_dims.sql"},
    )

    t_fact = PythonOperator(
        task_id="load_fact",
        python_callable=_run_sql_file,
        op_kwargs={"sql_rel_path": "sql/03_load_fact.sql"},
    )

    t_dq = PythonOperator(
        task_id="quality_checks",
        python_callable=run_quality_checks,
    )

    extract_raw >> t_staging >> t_dims >> t_fact >> t_dq
