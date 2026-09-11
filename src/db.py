from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, unquote

from src.config import ROOT, settings

SCHEMA_PATH = ROOT / "data" / "schema.sql"
SEED_PATH = ROOT / "data" / "seed.sql"


def _sqlite_path() -> Path:
    raw = settings.database_url.removeprefix("sqlite:///")
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def is_postgres() -> bool:
    return settings.database_url.startswith("postgresql")


def connect():
    if is_postgres():
        import psycopg

        return psycopg.connect(settings.database_url, autocommit=True)
    conn = sqlite3.connect(str(_sqlite_path()), timeout=settings.statement_timeout_ms / 1000)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def execute_sql(sql: str) -> tuple[list[str], list[tuple[Any, ...]]]:
    conn = connect()
    try:
        if is_postgres():
            with conn.cursor() as cur:
                cur.execute(f"SET statement_timeout = {int(settings.statement_timeout_ms)}")
                cur.execute(sql)
                if cur.description is None:
                    return [], []
                columns = [d.name for d in cur.description]
                rows = [tuple(r) for r in cur.fetchall()]
                return columns, rows
        cur = conn.cursor()
        cur.execute(sql)
        if cur.description is None:
            conn.commit()
            return [], []
        columns = [d[0] for d in cur.description]
        rows = [tuple(r) for r in cur.fetchall()]
        conn.commit()
        return columns, rows
    finally:
        conn.close()


def exec_script(sql_text: str) -> None:
    conn = connect()
    try:
        if is_postgres():
            statements = [s.strip() for s in sql_text.split(";") if s.strip()]
            with conn.cursor() as cur:
                for stmt in statements:
                    cur.execute(stmt)
        else:
            conn.executescript(sql_text)
            conn.commit()
    finally:
        conn.close()


def init_database() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    seed = SEED_PATH.read_text(encoding="utf-8")
    if is_postgres():
        exec_script(schema)
        exec_script(seed)
    else:
        path = _sqlite_path()
        if path.exists():
            path.unlink()
        exec_script(schema + "\n" + seed)


def schema_ddl() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


def postgres_dsn_parts() -> dict[str, str]:
    parsed = urlparse(settings.database_url)
    return {
        "user": unquote(parsed.username or "sqlagent"),
        "password": unquote(parsed.password or "sqlagent"),
        "host": parsed.hostname or "127.0.0.1",
        "port": str(parsed.port or 5432),
        "dbname": (parsed.path or "/sqlagent").lstrip("/"),
    }
