"""Holdout execution accuracy for modes A / B / C."""

from __future__ import annotations

import json
from src.config import ROOT
from src.db import execute_sql, init_database
from src.graph import run_question
from src.llm import get_llm
from src import playbook

QUESTIONS = ROOT / "evals" / "questions.json"
RESULTS = ROOT / "evals" / "results.md"


def _norm_cell(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        return round(value, 2)
    if isinstance(value, int):
        return value
    text = str(value).strip()
    try:
        if "." in text:
            return round(float(text), 2)
        return int(text)
    except ValueError:
        return text.lower()


def result_multiset(sql: str) -> list[tuple]:
    _cols, rows = execute_sql(sql)
    return sorted(tuple(_norm_cell(c) for c in row) for row in rows)


def load_questions() -> list[dict]:
    data = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    return data["questions"]


def score_split(items: list[dict], mode: str) -> dict:
    correct = 0
    retries = 0
    details = []
    for item in items:
        state = run_question(item["question"], mode=mode)
        retries += int(state.get("retries") or 0)
        gold = result_multiset(item["gold_sql"])
        pred_sql = state.get("sql") or ""
        error = state.get("error") or ""
        try:
            pred = result_multiset(pred_sql) if pred_sql and not error else []
        except Exception:
            pred = []
        ok = pred == gold and not error
        if ok:
            correct += 1
        details.append(
            {
                "id": item["id"],
                "ok": ok,
                "error": error,
                "sql": pred_sql,
            }
        )
    n = len(items)
    return {
        "n": n,
        "correct": correct,
        "ex": round(100.0 * correct / n, 1) if n else 0.0,
        "avg_retries": round(retries / n, 2) if n else 0.0,
        "details": details,
    }


def render(results: dict, note: str) -> str:
    lines = [
        "# Eval results",
        "",
        note,
        "",
        "| Mode | Description | Holdout EX% | Correct | Avg retries |",
        "|---|---|---|---|---|",
        f"| A | one-shot, no memory | {results['A']['ex']}% | {results['A']['correct']}/{results['A']['n']} | {results['A']['avg_retries']} |",
        f"| B | retry on error, no playbook | {results['B']['ex']}% | {results['B']['correct']}/{results['B']['n']} | {results['B']['avg_retries']} |",
        f"| C | retry + playbook after learn set | {results['C']['ex']}% | {results['C']['correct']}/{results['C']['n']} | {results['C']['avg_retries']} |",
        "",
        "Holdout is 20 questions. Learn set is 30 questions used only to grow the playbook before C.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    init_database()
    questions = load_questions()
    holdout = [q for q in questions if q["split"] == "holdout"]
    learn = [q for q in questions if q["split"] == "learn"]

    if get_llm() is None:
        note = (
            "LLM not configured. Set GROQ_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY, "
            "or USE_OLLAMA=1 then re-run `make eval`."
        )
        empty = {"n": len(holdout), "correct": 0, "ex": 0.0, "avg_retries": 0.0}
        RESULTS.write_text(
            render({"A": empty, "B": empty, "C": empty}, note),
            encoding="utf-8",
        )
        print(note)
        print(f"Wrote {RESULTS}")
        return

    playbook.reset()
    a = score_split(holdout, "A")
    b = score_split(holdout, "B")
    playbook.reset()
    for item in learn:
        run_question(item["question"], mode="C")
    c = score_split(holdout, "C")
    payload = {"A": a, "B": b, "C": c}
    note = "Numbers from `make eval` on the frozen holdout split."
    RESULTS.write_text(render(payload, note), encoding="utf-8")
    print(render(payload, note))
    failed_c = [d for d in c["details"] if not d["ok"]]
    if failed_c:
        print("Mode C misses:", [d["id"] for d in failed_c])


if __name__ == "__main__":
    main()
