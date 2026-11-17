"""Dev-only tuning experiments:  python -m evals.tune  ->  evals/results-tuning-dev.md

Two retrieval knobs, compared on the dev split only (the test split is never used for choices):
  1. how many candidates each retriever feeds into RRF (search.CANDIDATES)
  2. the query prefix the BGE model card recommends for short queries
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.search import bm25_ids, rrf, vector_ids
from common import db
from evals import score
from evals.run import ANSWERABLE, RESULTS_DIR, load, load_gold

DEPTHS = [5, 10, 20, 40]
BGE_PREFIX = "Represent this sentence for searching relevant passages: "


def variants():
    """(name, function(conn, question) -> top-10 chunk ids)."""
    yield "bm25", lambda conn, q: bm25_ids(conn, q, 10)
    yield "vector", lambda conn, q: vector_ids(conn, q, 10)
    yield "vector + BGE prefix", lambda conn, q: vector_ids(conn, BGE_PREFIX + q, 10)
    for d in DEPTHS:
        yield (f"hybrid, top {d} of each",
               lambda conn, q, d=d: rrf(bm25_ids(conn, q, d), vector_ids(conn, q, d))[:10])
    for d in (10, 20):
        yield (f"hybrid, top {d} of each + BGE prefix",
               lambda conn, q, d=d: rrf(bm25_ids(conn, q, d),
                                        vector_ids(conn, BGE_PREFIX + q, d))[:10])


def main() -> None:
    rows = [r for r in load("dev", None) if r["type"] != "unanswerable"]
    gold = load_gold(rows)
    groups = [(t, [i for i, r in enumerate(rows) if r["type"] == t]) for t in ANSWERABLE]
    groups.append(("all", list(range(len(rows)))))
    lines = [
        "# Tuning experiments: dev split only",
        "",
        f"Generated {datetime.now(UTC):%Y-%m-%d %H:%M} UTC by `python -m evals.tune`. "
        "Do not edit by hand.",
        "",
        f"{len(rows)} answerable dev questions. Each cell is hit@5 / MRR@10.",
        "",
        "| Variant | " + " | ".join(f"{t} (n={len(idx)})" for t, idx in groups) + " |",
        "|---|" + "---|" * len(groups),
    ]
    with db.connect() as conn:
        for name, fn in variants():
            ranked = [fn(conn, r["question"]) for r in rows]
            cells = []
            for _, idx in groups:
                results, g = [ranked[i] for i in idx], [gold[i] for i in idx]
                cells.append(f"{score.hit_at_k(results, g):.3f} / {score.mrr_at_k(results, g):.3f}")
            lines.append(f"| {name} | " + " | ".join(cells) + " |")
    out = RESULTS_DIR / "results-tuning-dev.md"
    out.write_text("\n".join(lines) + "\n")
    print(out.read_text())


if __name__ == "__main__":
    main()
