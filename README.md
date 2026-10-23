# Self-Improving SQL Agent

LangGraph **Text-to-SQL** agent over a music-store schema that **learns from its own failures**.

It generates SQL, runs it in a **SELECT-only sandbox**, reflects on errors, and writes durable lessons into a **playbook**. Holdout evals compare three modes (A / B / C) so improvement is measurable — not anecdotal.

Optional [Mem0](https://github.com/mem0ai/mem0) (or a local store) keeps user preferences. The execute path is also exposed as an [MCP](https://modelcontextprotocol.io/) tool.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-agent-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Repo:** https://github.com/ssk525/self-improving-sql-agent

---

## Why this exists

Most Text-to-SQL demos stop at “LLM wrote a query.” Production systems need:

1. **Guardrails** — never run arbitrary SQL
2. **Recovery** — retry with reflection when the executor fails
3. **Memory** — don’t re-learn the same join mistake every session
4. **Measurement** — frozen holdout EX%, not cherry-picked screenshots

This repo is scoped to those four. GitHub Actions runs Pytest on Python 3.11 and 3.12, including a PostgreSQL 16 job that sets `statement_timeout`.

---

## Architecture

```
question
  → schema linker
  → user memory (optional)
  → playbook retrieve
  → generate SQL
  → SELECT / WITH-only guardrail
  → sandbox execute
  → on error: reflect → update playbook → retry (max 3)
  → result table
```

| Mode | Behavior |
|------|----------|
| **A** | One-shot generation, no memory |
| **B** | Retry on errors, no playbook |
| **C** | Retry + playbook (grown on a 30-question learn set) + optional user memory |

**Primary metric:** execution accuracy (EX%) — predicted SQL result rows match gold SQL on a **frozen 20-question holdout** (column names ignored).

---

## Eval results

From `make eval` with **Ollama `gemma4:e4b`** (see [`evals/results.md`](evals/results.md)):

| Mode | Description | Holdout EX% | Correct | Avg retries |
|------|-------------|-------------|---------|-------------|
| A | One-shot, no memory | **75.0%** | 15/20 | 0.0 |
| B | Retry on error, no playbook | **75.0%** | 15/20 | 0.15 |
| C | Retry + playbook after learn set | **70.0%** | 14/20 | 0.15 |

**Takeaway:** On this local model, retries rarely fire — misses are usually wrong-but-valid SQL. Playbook did not lift holdout EX% here (noise risk with small models). The point of the harness is to **measure** that, not to claim magic gains. Re-run with Groq/Gemini/`gpt-4o-mini` before quoting cloud numbers.

---

## Quickstart

```bash
git clone https://github.com/ssk525/self-improving-sql-agent.git
cd self-improving-sql-agent
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set GROQ_API_KEY / GOOGLE_API_KEY / OPENAI_API_KEY, or USE_OLLAMA=1
make init
make test
make run                      # http://localhost:8501
make eval                     # writes evals/results.md
```

PostgreSQL (optional; needs Docker):

```bash
# DATABASE_URL=postgresql://sqlagent:sqlagent@127.0.0.1:5432/sqlagent
make up
```

---

## Design decisions (interview talking points)

1. **SELECT-only sandbox** — Text-to-SQL without a guardrail is a drop-table demo waiting to happen.
2. **Playbook ≠ chat history** — durable, retrieved lessons across queries; Mode C isolates that effect on holdout.
3. **EX% over string-match SQL** — two different SQL strings can be equivalent; comparing result multisets is fairer.
4. **Learn / holdout split** — playbook may train on 30 learn questions; scoring uses 20 frozen holdout IDs only.
5. **Ablations over vibes** — A/B/C exists so you can say *what* helped, and admit when it didn’t.
6. **MCP wrapper** — same execute path callable from MCP clients for tool-use interviews.

---

## Stack

Python 3.12 · LangGraph · PostgreSQL 16 / SQLite · Pydantic · Mem0 (optional) · MCP · Streamlit · pytest · Docker Compose

---

## Resume one-liner

Built a LangGraph Text-to-SQL agent with SELECT-only execution, reflection retries, persistent playbook memory, and holdout execution-accuracy evals (75% EX% on 20 frozen questions with local `gemma4:e4b`; A/B/C ablations reported in-repo).

---

## License

MIT
