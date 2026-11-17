"""Terminal demo:  python -m app.demo   (make demo runs `make ingest` first)

For a few dev questions, prints the top 5 chunks from each retrieval mode with doc and page,
marking the gold chunk with *. With ANTHROPIC_API_KEY set it also prints the cited answer.
"""

import os

from app.answer import answer
from app.search import MODES, search
from evals.run import load, load_gold

# Picked from the dev split to show where each mode wins and loses (see README).
DEMO_IDS = ["exact_id-02", "exact_id-39", "paraphrased-37", "unanswerable-18"]


def show_ranking(question: str, mode: str, gold: set[int]) -> None:
    print(f"  {mode}:")
    for rank, c in enumerate(search(question, mode, k=5), start=1):
        mark = "*" if c.chunk_id in gold else " "
        where = f"{c.doc_id} p.{c.page}"
        section = (c.section or "").split(" > ")[-1]
        print(f"   {mark}{rank}. [chunk {c.chunk_id}] {where:<32} {section[:44]}")


def show_answer(question: str) -> None:
    result = answer(question)
    print(f"  answer: {result.answer}")
    if result.declined:
        print(f"  (declined: {result.reason})")
    for c in result.citations:
        print(f"  cites [chunk {c.chunk_id}] {c.doc_id} page {c.page}  {c.url}")


def main() -> None:
    rows = [r for r in load("dev", None) if r["id"] in DEMO_IDS]
    gold = load_gold(rows)
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    for row, g in zip(rows, gold, strict=True):
        print(f"\n[{row['type']}] {row['question']}")
        print(f"  planted answer: {row['answer'] or 'none (not in the documents)'}")
        for mode in MODES:
            show_ranking(row["question"], mode, g)
        if has_key:
            show_answer(row["question"])
    print("\n* = gold chunk (contains the planted fact).")
    if not has_key:
        print("Set ANTHROPIC_API_KEY in .env to also see the cited answers (costs money).")


if __name__ == "__main__":
    main()
