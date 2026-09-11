# Self-Improving SQL Agent

LangGraph agent that turns natural-language questions into SQL over a music-store schema, executes them in a SELECT-only sandbox, and stores lessons from failed queries in a persistent playbook.

Optional [Mem0](https://github.com/mem0ai/mem0) (or a local store) keeps user preferences across sessions. The same execute path is exposed as an [MCP](https://modelcontextprotocol.io/) tool.

## Features

- Schema linking and Text-to-SQL generation
- SELECT / WITH-only execution with statement timeout
- Retry with reflection on executor or guardrail errors
- Playbook memory for cross-query improvement
- Holdout execution-accuracy eval (modes A / B / C)
- Streamlit UI for SQL, results, and playbook inspection

## Quickstart

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set GROQ_API_KEY, GOOGLE_API_KEY, or USE_OLLAMA=1
make init
make test
make run                      # http://localhost:8501
make eval                     # writes evals/results.md
```

PostgreSQL (optional; requires Docker):

```bash
# DATABASE_URL=postgresql://sqlagent:sqlagent@127.0.0.1:5432/sqlagent
make up
make psql
```

## Architecture

```
question
  → schema linker
  → user memory (optional)
  → playbook retrieve
  → generate SQL
  → SELECT-only guardrail
  → sandbox execute
  → on error: reflect → update playbook → retry (max 3)
  → result table
```

| Mode | Behavior |
|------|----------|
| A | Single generation, no memory |
| B | Retry on errors, no playbook |
| C | Retry, playbook, and user memory |

Evaluation uses 30 learn questions (playbook may update) and 20 frozen holdout questions. Primary metric is execution accuracy: result rows match gold SQL, ignoring column names.

## Stack

Python 3.12, LangGraph, PostgreSQL 16 / SQLite, Pydantic, Mem0 (optional), MCP, Streamlit, pytest, Docker Compose.

## License

MIT
