.DEFAULT_GOAL := help
RUN := uv run --env-file .env
.PHONY: help up down reset db-check data ingest test lint eval eval-answers tune demo run mcp

.env:
	cp .env.example .env

help:  ## list targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

up: .env  ## start Postgres and wait until it's healthy
	docker compose up -d --wait db

down:  ## stop containers (data kept)
	docker compose down

reset:  ## DELETE the local database volume, then start fresh (dev data only)
	docker compose down -v
	$(MAKE) up

db-check:  ## confirm pg_search, vector and llm_calls exist
	@docker compose exec -T db psql -U app -d app -tAc \
	  "SELECT count(*) FROM pg_extension WHERE extname IN ('pg_search','vector')" | grep -qx 2 \
	  && docker compose exec -T db psql -U app -d app -tAc \
	  "SELECT to_regclass('llm_calls')" | grep -qx llm_calls \
	  && echo "db OK: pg_search, vector, llm_calls" || (echo "db check FAILED"; exit 1)

data:  ## generate the synthetic PDFs and the 120-question eval set (deterministic)
	uv run python -m data.generate

ingest: .env data  ## extract, chunk, embed and index the PDFs (skips unchanged documents)
	$(RUN) python -m app.ingest

test: .env ingest  ## all tests (needs `make up`); the model API is always faked
	$(RUN) pytest -q

lint:  ## ruff
	uv run ruff check .

eval: .env ingest  ## retrieval metrics on dev and test, no API key -> evals/results-retrieval-*.md
	$(RUN) python -m evals.run --split dev
	$(RUN) python -m evals.run --split test

SPLIT ?= dev
eval-answers: .env ingest  ## answer metrics on SPLIT (default dev) -- CALLS THE API
	$(RUN) python -m evals.run --split $(SPLIT) --answers

tune: .env ingest  ## dev-only retrieval tuning experiments -> evals/results-tuning-dev.md
	$(RUN) python -m evals.tune

demo: .env ingest  ## sample queries in all three modes (+ cited answers if a key is set)
	$(RUN) python -m app.demo

run: .env  ## API on http://localhost:8003 with auto-reload
	$(RUN) uvicorn app.main:app --reload --port 8003

mcp: .env  ## MCP server over stdio (for Claude Code / Desktop)
	$(RUN) python -m app.mcp_server
