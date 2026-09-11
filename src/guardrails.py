"""SELECT-only sandbox. Shared by the LangGraph node and the MCP server."""

from __future__ import annotations

import re

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|"
    r"ATTACH|DETACH|PRAGMA|COPY|VACUUM|REINDEX|EXEC|EXECUTE)\b",
    re.IGNORECASE,
)


class UnsafeSQLError(ValueError):
    pass


def ensure_safe_select(sql: str) -> str:
    if not sql or not sql.strip():
        raise UnsafeSQLError("SQL is empty.")
    cleaned = sql.strip().rstrip(";")
    # strip /* */ and -- comments
    cleaned = re.sub(r"/\*.*?\*/", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"--[^\n]*", " ", cleaned)
    if ";" in cleaned:
        raise UnsafeSQLError("Multiple statements are not allowed.")
    compact = re.sub(r"\s+", " ", cleaned).strip()
    if not re.match(r"^(SELECT|WITH)\b", compact, re.IGNORECASE):
        raise UnsafeSQLError("Only SELECT / WITH queries are allowed.")
    if _FORBIDDEN.search(compact):
        raise UnsafeSQLError("Query contains a forbidden keyword.")
    return compact
