from __future__ import annotations

import re
from typing import Any, Literal, TypedDict

from src.config import settings
from src.guardrails import UnsafeSQLError
from src.llm import get_llm
from src import memory, playbook
from src.schema_linker import link_schema
from src.sql_tool import execute_select

Mode = Literal["A", "B", "C"]


class AgentState(TypedDict, total=False):
    question: str
    user_id: str
    mode: Mode
    schema_text: str
    memories: list[str]
    playbook_bullets: list[str]
    sql: str
    error: str
    columns: list[str]
    rows: list[list[Any]]
    retries: int
    reflections: list[str]
    answer: str


def _extract_sql(text: str) -> str:
    fence = re.search(r"```sql\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    if fence:
        return fence.group(1).strip()
    fence = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return text.strip()


def link_schema_node(state: AgentState) -> dict:
    return {"schema_text": link_schema(state["question"])}


def retrieve_memory_node(state: AgentState) -> dict:
    if state.get("mode") != "C":
        return {"memories": []}
    hits = memory.search(state.get("user_id") or settings.agent_user_id, state["question"])
    return {"memories": hits}


def retrieve_playbook_node(state: AgentState) -> dict:
    if state.get("mode") != "C":
        return {"playbook_bullets": []}
    return {"playbook_bullets": playbook.retrieve(state["question"])}


def generate_sql_node(state: AgentState) -> dict:
    llm = get_llm()
    lessons = "\n".join(f"- {b}" for b in state.get("playbook_bullets") or [])
    mems = "\n".join(f"- {m}" for m in state.get("memories") or [])
    prior_error = state.get("error") or ""
    reflections = "\n".join(state.get("reflections") or [])
    prompt = f"""You write SQLite/Postgres-compatible SQL for a music store.

SCHEMA:
{state.get("schema_text")}

PLAYBOOK LESSONS:
{lessons or "(none)"}

USER MEMORIES:
{mems or "(none)"}

PREVIOUS ERROR:
{prior_error or "(none)"}

REFLECTIONS:
{reflections or "(none)"}

QUESTION:
{state["question"]}

Rules:
- Return ONLY SQL, no markdown unless fenced as sql.
- SELECT or WITH only. No INSERT/UPDATE/DELETE/DDL.
- Use ROUND(x, 2) for money. Use ISO date strings like '2023-01-01'.
- Prefer explicit JOINs. Alias columns clearly.
"""
    if llm is None:
        return {"sql": "", "error": "No LLM configured. Set GROQ_API_KEY or USE_OLLAMA=1."}
    resp = llm.invoke(prompt)
    sql = _extract_sql(getattr(resp, "content", str(resp)))
    return {"sql": sql, "error": ""}


def execute_node(state: AgentState) -> dict:
    sql = state.get("sql") or ""
    try:
        result = execute_select(sql)
        rows = result["rows"]
        error = "" if rows or rows == [] else ""
        # empty result is not always a failure; treat executor exceptions only
        return {
            "sql": result["sql"],
            "columns": result["columns"],
            "rows": rows,
            "error": error,
        }
    except (UnsafeSQLError, Exception) as exc:
        return {
            "columns": [],
            "rows": [],
            "error": str(exc),
        }


def reflect_node(state: AgentState) -> dict:
    llm = get_llm()
    retries = int(state.get("retries") or 0) + 1
    if llm is None:
        lesson = f"SQL failed: {state.get('error')}"
        playbook.add_bullet(lesson)
        return {
            "retries": retries,
            "reflections": (state.get("reflections") or []) + [lesson],
        }
    prompt = f"""A Text-to-SQL attempt failed.

QUESTION: {state["question"]}
SQL: {state.get("sql")}
ERROR: {state.get("error")}

Write ONE short playbook rule (under 25 words) so a future query of this kind succeeds.
Do not repeat the SQL. Write the rule only.
"""
    resp = llm.invoke(prompt)
    lesson = str(getattr(resp, "content", resp)).strip()
    if state.get("mode") == "C":
        playbook.add_bullet(lesson)
    return {
        "retries": retries,
        "reflections": (state.get("reflections") or []) + [lesson],
    }


def finalize_node(state: AgentState) -> dict:
    rows = state.get("rows") or []
    cols = state.get("columns") or []
    if state.get("error") and not rows:
        answer = f"Failed: {state.get('error')}"
    else:
        preview = rows[:8]
        answer = f"SQL:\n{state.get('sql')}\n\nColumns: {cols}\nRows ({len(rows)}): {preview}"
        if state.get("mode") == "C":
            memory.add(
                state.get("user_id") or settings.agent_user_id,
                [
                    {"role": "user", "content": state["question"]},
                    {"role": "assistant", "content": state.get("sql") or ""},
                ],
            )
            if state.get("sql") and not state.get("error"):
                for b in state.get("playbook_bullets") or []:
                    playbook.mark(b, helpful=True)
    return {"answer": answer}
