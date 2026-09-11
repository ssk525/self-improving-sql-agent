"""Tiny schema linker: keep only tables named in the question, else all tables."""

from __future__ import annotations

import re

from src.db import schema_ddl

TABLES = [
    "artists",
    "albums",
    "tracks",
    "genres",
    "employees",
    "customers",
    "invoices",
    "invoice_lines",
]


def _split_create_statements(ddl: str) -> dict[str, str]:
    parts: dict[str, str] = {}
    for match in re.finditer(
        r"CREATE TABLE (\w+) \((.*?)\);",
        ddl,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        parts[match.group(1).lower()] = match.group(0)
    return parts


def link_schema(question: str) -> str:
    ddl = schema_ddl()
    tables = _split_create_statements(ddl)
    q = question.lower()
    hit = [name for name in TABLES if name.rstrip("s") in q or name in q]
    # common synonyms
    if "song" in q or "track" in q:
        hit.extend(["tracks", "albums", "genres"])
    if "sale" in q or "spend" in q or "revenue" in q or "invoice" in q:
        hit.extend(["invoices", "invoice_lines", "customers", "tracks"])
    if "manager" in q or "employee" in q or "staff" in q or "rep" in q:
        hit.extend(["employees", "customers"])
    chosen = [t for t in TABLES if t in set(hit)]
    if not chosen:
        chosen = TABLES
    return "\n\n".join(tables[t] for t in chosen if t in tables)
