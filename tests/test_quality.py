from sqlalchemy import create_engine, text
from src.config import WAREHOUSE_URL
from src.quality_checks import run_quality_checks


def test_quality_checks_pass_and_log():
    results = run_quality_checks()
    assert len(results) == 5
    assert all(r["status"] == "PASS" for r in results)

    engine = create_engine(WAREHOUSE_URL)
    with engine.connect() as conn:
        logged = conn.execute(text("SELECT COUNT(*) FROM dq_results")).scalar()
        assert logged >= 5
