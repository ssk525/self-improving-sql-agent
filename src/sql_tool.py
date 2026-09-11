"""SQL execute helper used by LangGraph and the MCP tool server."""

from __future__ import annotations

from src.db import execute_sql
from src.guardrails import ensure_safe_select


def execute_select(sql: str) -> dict:
    safe = ensure_safe_select(sql)
    columns, rows = execute_sql(safe)
    return {"sql": safe, "columns": columns, "rows": [list(r) for r in rows]}
