"""The eval harness end to end: real retrieval, fake model API. Needs make up + ingest."""

import json
import os
import re

import psycopg

from evals import run
from tests.helpers import fake_api, needs_chunks, reply

pytestmark = needs_chunks


def cite_first_chunk(body: dict) -> dict:
    """A fake model that answers with the first retrieved chunk's text and cites it."""
    prompt = body["messages"][0]["content"]
    chunk_id, text = re.search(r'<chunk id="(\d+)"[^>]*>\n(.*?)\n</chunk>', prompt, re.S).groups()
    return reply(json.dumps({"answer": text, "citations": [int(chunk_id)], "declined": False}))


def test_answer_eval_runs_against_the_fake_api(monkeypatch, tmp_path):
    monkeypatch.setattr(run, "RESULTS_DIR", tmp_path)
    monkeypatch.setenv("PROJECT_NAME", "pytest")
    seen = fake_api(monkeypatch, cite_first_chunk, keep_db=True)

    assert run.main(["--split", "dev", "--answers", "--limit", "8"]) == 0

    report = (tmp_path / "results-answers-dev-first8.md").read_text()
    assert "| all answerable | 8 |" in report
    assert "citation precision" in report and "Cost / question" in report
    assert len(seen) == 8  # every dev question in the first 8 passes the relevance gate
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
        rows = conn.execute(
            "SELECT run_id, step, cost_usd FROM llm_calls WHERE project = 'pytest'"
            " AND run_id LIKE 'answers-dev-%' ORDER BY id"
        ).fetchall()
        conn.execute("DELETE FROM llm_calls WHERE project = 'pytest'")
    assert len(rows) == 8 and {r[1] for r in rows} == {"answer"}
    assert all(float(r[2]) > 0 for r in rows)  # priced from the fake usage, never NULL here


def test_retrieval_eval_writes_the_per_type_tables(monkeypatch, tmp_path):
    monkeypatch.setattr(run, "RESULTS_DIR", tmp_path)
    assert run.main(["--split", "dev", "--limit", "6"]) == 0
    report = (tmp_path / "results-retrieval-dev-first6.md").read_text()
    for heading in ("## hit@5", "## MRR@10", "## recall@5", "## Search latency",
                    "## Relevance gate"):
        assert heading in report
    assert "| exact_id | 6 |" in report


def test_estimate_needs_no_api(monkeypatch, capsys):
    seen = fake_api(monkeypatch, [], keep_db=True)
    assert run.main(["--split", "dev", "--answers", "--estimate", "--limit", "3"]) == 0
    out = capsys.readouterr().out
    assert seen == [] and "claude-haiku-5-5" in out and "claude-opus-5-5" in out
