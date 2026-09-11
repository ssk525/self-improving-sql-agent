# Eval results

Run `make eval` with an LLM configured (`GROQ_API_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`, or `USE_OLLAMA=1`). That command overwrites this file.

| Mode | Description | Holdout EX% | Correct | Avg retries |
|------|-------------|-------------|---------|-------------|
| A | Single generation, no memory | — | — | — |
| B | Retry on errors, no playbook | — | — | — |
| C | Retry + playbook after learn set | — | — | — |

Holdout: 20 questions. Learn set: 30 questions (used only before scoring mode C).
