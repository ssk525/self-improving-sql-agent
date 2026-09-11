from src.db import execute_sql, init_database
from src.guardrails import UnsafeSQLError, ensure_safe_select
from src.playbook import add_bullet, retrieve
from src.sql_tool import execute_select


def test_select_allowed():
    assert ensure_safe_select("SELECT 1").startswith("SELECT")
    assert ensure_safe_select("WITH x AS (SELECT 1 AS n) SELECT n FROM x").upper().startswith("WITH")


def test_drop_rejected():
    try:
        ensure_safe_select("DROP TABLE artists")
        assert False, "expected UnsafeSQLError"
    except UnsafeSQLError:
        pass


def test_insert_rejected():
    try:
        ensure_safe_select("INSERT INTO artists VALUES (99, 'x')")
        assert False, "expected UnsafeSQLError"
    except UnsafeSQLError:
        pass


def test_multi_statement_rejected():
    try:
        ensure_safe_select("SELECT 1; SELECT 2")
        assert False, "expected UnsafeSQLError"
    except UnsafeSQLError:
        pass


def test_executor_select():
    init_database()
    result = execute_select("SELECT COUNT(*) AS n FROM artists")
    assert result["rows"][0][0] == 10


def test_playbook_retrieve(tmp_path, monkeypatch):
    from src import playbook as pb

    monkeypatch.setattr(pb, "DB_PATH", tmp_path / "playbook.db")
    pb.add_bullet("when asked year totals, filter invoice_date with ISO bounds")
    pb.add_bullet("join customers to invoices on customer_id for spend")
    hits = pb.retrieve("total spend by customer")
    assert any("spend" in h.lower() or "customer" in h.lower() for h in hits)


def test_gold_sql_runs():
    import json
    from pathlib import Path

    init_database()
    questions = json.loads(
        Path("evals/questions.json").read_text(encoding="utf-8")
    )["questions"]
    assert len(questions) == 50
    learn = [q for q in questions if q["split"] == "learn"]
    holdout = [q for q in questions if q["split"] == "holdout"]
    assert len(learn) == 30
    assert len(holdout) == 20
    for q in questions:
        cols, rows = execute_sql(q["gold_sql"])
        assert cols, q["id"]
        assert rows is not None
