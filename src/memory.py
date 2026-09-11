"""User memory: Mem0 when MEM0_API_KEY is set, otherwise local SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.config import ROOT, settings

DB_PATH = ROOT / "data" / "memory.db"


def _local() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY,
            user_id TEXT NOT NULL,
            text TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def _use_mem0() -> bool:
    return bool(settings.mem0_api_key)


def add(user_id: str, messages: list[dict]) -> None:
    blob = " ".join(m.get("content", "") for m in messages if m.get("content"))
    if not blob.strip():
        return
    if _use_mem0():
        from mem0 import MemoryClient

        MemoryClient(api_key=settings.mem0_api_key).add(messages, user_id=user_id)
        return
    conn = _local()
    try:
        conn.execute(
            "INSERT INTO memories (user_id, text) VALUES (?, ?)",
            (user_id, blob.strip()[:500]),
        )
        conn.commit()
    finally:
        conn.close()


def search(user_id: str, query: str, k: int = 5) -> list[str]:
    if _use_mem0():
        from mem0 import MemoryClient

        hits = MemoryClient(api_key=settings.mem0_api_key).search(
            query, user_id=user_id, limit=k
        )
        results = hits.get("results", hits) if isinstance(hits, dict) else hits
        out: list[str] = []
        for item in results or []:
            if isinstance(item, dict):
                out.append(str(item.get("memory") or item.get("text") or item))
            else:
                out.append(str(item))
        return out[:k]
    tokens = {t for t in query.lower().split() if len(t) > 2}
    conn = _local()
    try:
        rows = conn.execute(
            "SELECT text FROM memories WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()
    scored = []
    for (text,) in rows:
        score = len(tokens & set(text.lower().split()))
        scored.append((score, text))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:k]]


def all_for_user(user_id: str) -> list[str]:
    conn = _local()
    try:
        rows = conn.execute(
            "SELECT text FROM memories WHERE user_id = ? ORDER BY id DESC LIMIT 20",
            (user_id,),
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()
