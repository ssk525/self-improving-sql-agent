# Eval results

Numbers from `make eval` on the frozen 20-question holdout  
(**model:** Ollama `gemma4:e4b`, temperature 0, SQLite Chinook-style store).

| Mode | Description | Holdout EX% | Correct | Avg retries |
|------|-------------|-------------|---------|-------------|
| A | one-shot, no memory | 75.0% | 15/20 | 0.0 |
| B | retry on error, no playbook | 75.0% | 15/20 | 0.15 |
| C | retry + playbook after learn set | 70.0% | 14/20 | 0.15 |

Holdout is 20 questions. Learn set is 30 questions used only to grow the playbook before C.

### How to read this

- **A = B (75%)** — retries barely fire (`avg_retries` 0.15). Most misses are *valid but wrong* SQL, not executor errors, so reflection-on-error does not help much on this model/split.
- **C (70%)** — playbook did **not** improve holdout here. With a small local model, retrieved lessons can add noise. That is still a useful ablation: the harness caught it.
- Re-run after changing model/prompts: `make eval` overwrites this file. Prefer quoting numbers only for the model you actually measured.

Mode C misses (ids): 34, 41, 42, 46, 49, 50.
