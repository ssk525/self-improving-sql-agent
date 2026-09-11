"""Procedural playbook: lessons from failed SQL, reused on later questions."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.config import ROOT

DB_PATH = ROOT / "data" / "playbook.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bullets (
            id INTEGER PRIMARY KEY,
            text TEXT NOT NULL UNIQUE,
            helpful INTEGER NOT NULL DEFAULT 0,
            harmful INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    return conn


def reset() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    _conn().close()


def add_bullet(text: str) -> None:
    text = (text or "").strip()
    if not text:
        return
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO bullets (text) VALUES (?) ON CONFLICT(text) DO UPDATE SET helpful = helpful",
            (text,),
        )
        conn.commit()
    finally:
        conn.close()


def mark(text: str, helpful: bool) -> None:
    conn = _conn()
    try:
        col = "helpful" if helpful else "harmful"
        conn.execute(f"UPDATE bullets SET {col} = {col} + 1 WHERE text = ?", (text,))
        conn.commit()
    finally:
        conn.close()


def delete_bullet(bullet_id: int) -> None:
    conn = _conn()
    try:
        conn.execute("DELETE FROM bullets WHERE id = ?", (bullet_id,))
        conn.commit()
    finally:
        conn.close()


def all_bullets() -> list[dict]:
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT id, text, helpful, harmful FROM bullets ORDER BY id"
        ).fetchall()
        return [
            {"id": r[0], "text": r[1], "helpful": r[2], "harmful": r[3]} for r in rows
        ]
    finally:
        conn.close()


def retrieve(question: str, k: int = 8) -> list[str]:
    tokens = {t for t in question.lower().split() if len(t) > 2}
    scored: list[tuple[int, str]] = []
    for b in all_bullets():
        if b["harmful"] > b["helpful"] + 1:
            continue
        bt = set(b["text"].lower().split())
        score = len(tokens & bt)
        scored.append((score, b["text"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [t for s, t in scored if s > 0][:k]
    if not picked:
        picked = [t for _, t in scored[:k]]
    return picked
