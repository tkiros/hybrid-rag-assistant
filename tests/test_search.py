"""Retrieval against the real ParadeDB container. Needs `make up` and `make ingest`."""

import pytest

from app import ingest
from app.answer import MIN_SIMILARITY
from app.search import MODES, search, top_similarity
from evals.run import load, load_gold
from tests.helpers import needs_chunks

pytestmark = needs_chunks

HOSTILE = [
    "", "   ", "-", "§", '"', "'", ":", "()", "\\", "*", "?", "~", "^2", "{}", "[1 TO 5]",
    'what is "HX-4471', "torque: (HX AND", "AND", "OR OR", "NOT", "text:foo", "+torque -valve",
    "§4.2.1", "E-4127?", "it's 50% off!", "DROP TABLE chunks; --", "x" * 2000, "ünïcödé ✓",
]


@pytest.mark.parametrize("query", HOSTILE)
@pytest.mark.parametrize("mode", MODES)
def test_any_user_text_is_a_valid_query(query, mode):
    results = search(query, mode, k=5)
    assert isinstance(results, list) and len(results) <= 5


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError, match="mode"):
        search("oil filter", "fuzzy")


def test_results_carry_citation_metadata():
    for chunk in search("oil filter replacement interval", "hybrid", k=3):
        assert chunk.doc_id in {"rs-service-manual", "returns-warranty-handbook"}
        assert chunk.page >= 1 and chunk.text


def first_dev_question(type_: str):
    row = next(r for r in load("dev", None) if r["type"] == type_)
    return row, load_gold([row])[0]


def test_planted_part_number_is_bm25s_top_hit():
    row, gold = first_dev_question("exact_id")
    assert search(row["question"], "bm25", k=1)[0].chunk_id in gold


def test_hybrid_finds_both_identifier_and_paraphrase_questions():
    # exact_id-02: vector misses it, bm25 finds it. paraphrased-08: the reverse is closer.
    rows = [r for r in load("dev", None) if r["id"] in ("exact_id-02", "paraphrased-08")]
    for row, gold in zip(rows, load_gold(rows), strict=True):
        assert {c.chunk_id for c in search(row["question"], "hybrid", k=5)} & gold, row["id"]


def test_relevance_gate_separates_off_topic_questions():
    assert top_similarity("What is the capital of France?") < MIN_SIMILARITY
    assert top_similarity("How do I bake sourdough bread?") < MIN_SIMILARITY
    assert top_similarity("What is the torque for the inlet valve?") > MIN_SIMILARITY


def test_every_eval_needle_resolves_to_one_chunk():
    rows = load("dev", None) + load("test", None)
    gold = load_gold(rows)  # raises if any needle is missing or ambiguous
    assert all(g for g, r in zip(gold, rows, strict=True) if r["type"] != "unanswerable")


def test_reingest_skips_unchanged_documents():
    assert ingest.ingest() == {}
