.PHONY: up down psql init test eval run toy

PYTHON ?= python3.12

up:
	docker compose up -d

down:
	docker compose down

psql:
	docker compose exec postgres psql -U $${POSTGRES_USER:-sqlagent} -d $${POSTGRES_DB:-sqlagent}

init:
	$(PYTHON) -m src.init_db

toy:
	$(PYTHON) -m src.toy_graph

test:
	$(PYTHON) -m pytest -q

eval:
	$(PYTHON) -m src.eval_runner

run:
	$(PYTHON) -m streamlit run app/streamlit_app.py
