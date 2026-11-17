"""Retrieval metrics, RRF, label resolution and answer grading. Pure functions, no database."""

from types import SimpleNamespace

import pytest

from app.search import rrf
from evals import score
from evals.run import pct


def test_rrf_matches_the_guide():
    assert rrf([1, 2, 3], [3, 1]) == [1, 3, 2]


def test_rrf_rewards_agreement_over_a_single_top_rank():
    # 7 is 2nd in both lists; 1 is 1st in one list only. 2/(60+2) > 1/(60+1).
    assert rrf([1, 7], [9, 7])[0] == 7


def test_hit_and_mrr_match_the_guide():
    assert score.hit_at_k([[5, 1, 2]], [{2}], k=3) == 1.0
    assert abs(score.mrr_at_k([[5, 1, 2]], [{2}]) - 1 / 3) < 1e-9


def test_metrics_cut_at_k():
    assert score.hit_at_k([[5, 1, 2]], [{2}], k=2) == 0.0
    assert score.mrr_at_k([list(range(20))], [{15}], k=10) == 0.0


def test_recall_counts_every_gold_chunk():
    assert score.recall_at_k([[1, 2, 3]], [{1, 9}], k=5) == 0.5
    assert score.recall_at_k([[1, 9]], [{1, 9}], k=5) == 1.0


def test_pct_nearest_rank():
    assert pct([10, 20, 30, 40], 0.5) == 20
    assert pct([10, 20, 30, 40], 0.95) == 40
    assert pct([5], 0.95) == 5


@pytest.mark.parametrize("answer, value, expected", [
    ("Tighten to 46 Nm.", "46", True),
    ("Tighten to 146 Nm.", "46", False),
    ("Tighten to 46.5 Nm.", "46", False),
    ("Tighten to 38.5 Nm.", "38.5", True),
    ("Replace after 15,000 operating hours.", "15000", True),
    ("The unit price is $182.40.", "182.40", True),
    ("It is class w3.", "W3", True),
    ("Replace part VL-2290-C (oil filter).", "VL-2290-C", True),
    ("Replace part VL-2290-CX.", "VL-2290-C", False),
])
def test_contains_value(answer, value, expected):
    assert score.contains_value(answer, value) is expected


def test_resolve_gold_finds_needles_across_line_breaks():
    chunks = [(1, "Part No.\nHX-4471-B\nUnit price: $10.00"), (2, "Error E-1234")]
    rows = [{"id": "q", "gold_needles": ["Part No. HX-4471-B", "E-1234"]}]
    assert score.resolve_gold(rows, chunks) == [{1, 2}]


@pytest.mark.parametrize("chunks", [[(1, "nothing here")], [(1, "E-1234"), (2, "E-1234")]])
def test_resolve_gold_rejects_missing_or_ambiguous_needles(chunks):
    with pytest.raises(ValueError, match="needle"):
        score.resolve_gold([{"id": "q", "gold_needles": ["E-1234"]}], chunks)


def result(answer: str, cited: list[int], declined: bool = False):
    citations = [SimpleNamespace(chunk_id=c) for c in cited]
    return SimpleNamespace(answer=answer, citations=citations, declined=declined)


def test_grade_answer():
    row = {"must_contain": "46"}
    assert score.grade_answer(result("Use 46 Nm.", [3, 8]), row, {3}) == {
        "declined": 0, "correct": 1, "cited": 2, "cited_gold": 1, "error": 0}
    declined = score.grade_answer(result("Not in the documents.", [], declined=True), row, {3})
    assert declined["declined"] == 1 and declined["correct"] == 0
    assert score.grade_answer(None, row, {3})["error"] == 1


def test_unanswerable_is_never_graded_correct():
    graded = score.grade_answer(result("It is 46.", [3]), {"must_contain": None}, set())
    assert graded["correct"] == 0 and graded["declined"] == 0
