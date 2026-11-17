"""How retrieval and answers are graded. No LLM judge: the facts are planted, so grading is code."""

from __future__ import annotations

import re

# Goes into every results file. Says exactly how the expected answers were made.
LABELS = (
    "synthetic, generated ground truth. Each question comes from a template over a fact planted "
    "in the corpus by data/generate.py; its gold chunk ids are found after ingestion by locating "
    "the fact's unique needle string"
)


# ---------------------------------------------------------------- labels

def normalize(text: str) -> str:
    """Collapse whitespace, so a needle still matches when the PDF wrapped it across lines."""
    return " ".join(text.split())


def resolve_gold(rows: list[dict], chunks: list[tuple[int, str]]) -> list[set[int]]:
    """Gold chunk ids per question: the chunks whose text contains each needle.

    Raises if a needle is in no chunk or in several, so a chunking change can't silently
    corrupt the labels.
    """
    texts = [(chunk_id, normalize(text)) for chunk_id, text in chunks]
    gold = []
    for row in rows:
        ids = set()
        for needle in row["gold_needles"]:
            found = [chunk_id for chunk_id, text in texts if needle in text]
            if len(found) != 1:
                raise ValueError(f"{row['id']}: needle {needle!r} is in {len(found)} chunks")
            ids.add(found[0])
        gold.append(ids)
    return gold


# ---------------------------------------------------------------- retrieval metrics
# results: one ranked list of chunk ids per question; gold: one set of gold ids per question.

def hit_at_k(results: list[list[int]], gold: list[set[int]], k: int = 5) -> float:
    """Share of questions with at least one gold chunk in the top k."""
    return sum(bool(set(r[:k]) & g) for r, g in zip(results, gold, strict=True)) / len(gold)


def mrr_at_k(results: list[list[int]], gold: list[set[int]], k: int = 10) -> float:
    """Mean of 1/rank of the first gold chunk in the top k (0 when none is there)."""
    return sum(
        next((1 / i for i, c in enumerate(r[:k], 1) if c in g), 0.0)
        for r, g in zip(results, gold, strict=True)
    ) / len(gold)


def recall_at_k(results: list[list[int]], gold: list[set[int]], k: int = 5) -> float:
    """Mean share of each question's gold chunks found in the top k (matters for multi-chunk)."""
    return sum(len(set(r[:k]) & g) / len(g) for r, g in zip(results, gold, strict=True)) / len(gold)


# ---------------------------------------------------------------- answer metrics

def contains_value(answer: str, value: str) -> bool:
    """True if the planted value appears as a whole token: "46" matches "46 Nm", not "146" or
    "46.5". Case and thousands separators are ignored ("15,000" matches "15000")."""
    text = re.sub(r"(?<=\d),(?=\d{3})", "", answer.lower())
    pattern = rf"(?<![\w.]){re.escape(value.lower())}(?!\w|\.\d)"
    return re.search(pattern, text) is not None


def grade_answer(result, row: dict, gold: set[int]) -> dict[str, int]:
    """Counts for one question. `result` is an app.answer.Result, or None if the call crashed."""
    if result is None:
        return {"declined": 0, "correct": 0, "cited": 0, "cited_gold": 0, "error": 1}
    cited = [c.chunk_id for c in result.citations]
    correct = (not result.declined and row["must_contain"] is not None
               and contains_value(result.answer, row["must_contain"]))
    return {
        "declined": int(result.declined),
        "correct": int(correct),
        "cited": len(cited),
        "cited_gold": sum(c in gold for c in cited),
        "error": 0,
    }
