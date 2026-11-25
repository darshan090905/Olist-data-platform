from sqlalchemy import create_engine, text
from src.config import WAREHOUSE_URL


def run_quality_checks() -> list[dict]:
    engine = create_engine(WAREHOUSE_URL)

    checks = [
        {
            "name": "fact_order_items_non_empty",
            "sql": """
                SELECT COUNT(*) AS bad_count
                FROM (SELECT 1 FROM fact_order_items LIMIT 1) t
                HAVING COUNT(*) = 0
            """,
            "details": "fact_order_items must have at least 1 row",
        },
        {
            "name": "staging_to_fact_row_count_match",
            "sql": """
                SELECT ABS(
                    (SELECT COUNT(*) FROM stg_order_items) -
                    (SELECT COUNT(*) FROM fact_order_items)
                ) AS bad_count
            """,
            "details": "Compare stg_order_items row count against fact_order_items row count",
        },
        {
            "name": "fact_null_foreign_keys",
            "sql": """
                SELECT COUNT(*) AS bad_count
                FROM fact_order_items
                WHERE order_id IS NULL
                   OR order_item_id IS NULL
                   OR customer_key IS NULL
                   OR product_key IS NULL
                   OR seller_key IS NULL
                   OR order_date_key IS NULL
            """,
            "details": "Primary and foreign keys in fact_order_items must not be NULL",
        },
        {
            "name": "fact_non_negative_price_and_freight",
            "sql": """
                SELECT COUNT(*) AS bad_count
                FROM fact_order_items
                WHERE price < 0 OR freight_value < 0
            """,
            "details": "price and freight_value must be >= 0",
        },
        {
            "name": "fact_orphan_date_keys",
            "sql": """
                SELECT COUNT(*) AS bad_count
                FROM fact_order_items f
                LEFT JOIN dim_date d ON f.order_date_key = d.date_key
                WHERE d.date_key IS NULL
            """,
            "details": "Every order_date_key in fact_order_items must exist in dim_date",
        },
    ]

    results: list[dict] = []
    failed_checks: list[str] = []

    with engine.begin() as conn:
        for chk in checks:
            bad_count = int(conn.execute(text(chk["sql"])).scalar() or 0)
            status = "PASS" if bad_count == 0 else "FAIL"

            conn.execute(
                text("""
                    INSERT INTO dq_results (check_name, status, bad_count, details)
                    VALUES (:check_name, :status, :bad_count, :details)
                """),
                {
                    "check_name": chk["name"],
                    "status": status,
                    "bad_count": bad_count,
                    "details": chk["details"],
                },
            )

            entry = {
                "check_name": chk["name"],
                "status": status,
                "bad_count": bad_count,
            }
            results.append(entry)
            print(f"[DQ] {chk['name']}: {status} (bad_count={bad_count})")

            if status == "FAIL":
                failed_checks.append(f"{chk['name']} (bad_count={bad_count})")

    if failed_checks:
        raise RuntimeError(f"Data quality checks failed: {', '.join(failed_checks)}")

    return results


if __name__ == "__main__":
    run_quality_checks()
