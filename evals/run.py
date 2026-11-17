"""Eval harness.

  python -m evals.run --split dev                       retrieval metrics, no API key needed
  python -m evals.run --split dev --answers             answer metrics (calls the model API)
  python -m evals.run --split dev --answers --estimate  prompt sizes and cost estimate, no API

Retrieval: hit@5, MRR@10 and recall@5 for bm25, vector and hybrid, per question type, plus
search latency -> evals/results-retrieval-<split>.md
Answers: correctness, citation precision, decline accuracy, p50/p95 latency and cost measured
from llm_calls -> evals/results-answers-<split>.md (a --limit run writes ...-firstN.md)
Tune on dev; run test once you've stopped changing things, and report test.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

import psycopg

from app import answer as answering
from app import embeddings
from app.search import CANDIDATES, MODES, RRF_K, search, top_similarity
from common import db, llm
from evals import score

HERE = Path(__file__).parent
SETS_DIR = HERE / "sets"
RESULTS_DIR = HERE
TYPES = ["exact_id", "paraphrased", "multi_chunk", "unanswerable"]
ANSWERABLE = TYPES[:3]


def load(split: str, limit: int | None) -> list[dict]:
    lines = (SETS_DIR / f"{split}.jsonl").read_text().splitlines()
    rows = [json.loads(line) for line in lines if line.strip()]
    if not rows:
        raise SystemExit(f"evals/sets/{split}.jsonl is empty")
    return rows[:limit] if limit else rows


def load_gold(rows: list[dict]) -> list[set[int]]:
    with db.connect() as conn:
        chunks = conn.execute("SELECT id, text FROM chunks").fetchall()
    if not chunks:
        raise SystemExit("the chunks table is empty; run `make ingest` first")
    return score.resolve_gold(rows, chunks)


def pct(values: list[float], p: float) -> float:
    """Nearest-rank percentile."""
    s = sorted(values)
    return s[max(0, math.ceil(p * len(s)) - 1)]


def header(title: str, command: str, stamp: datetime, rows: list[dict], limit) -> list[str]:
    counts = ", ".join(f"{t} {sum(r['type'] == t for r in rows)}" for t in TYPES)
    return [
        f"# {title}",
        "",
        f"Generated {stamp:%Y-%m-%d %H:%M} UTC by `{command}`. Do not edit by hand.",
        "",
        f"- Questions: {len(rows)} ({counts})" + (f", first {limit} only" if limit else ""),
        f"- Labels: {score.LABELS}",
    ]


def by_type(rows: list[dict], types: list[str]) -> list[tuple[str, list[int]]]:
    """(row label, indexes of the questions in it) for each type present, then the total."""
    groups = [(t, [i for i, r in enumerate(rows) if r["type"] == t]) for t in types]
    groups = [(t, idx) for t, idx in groups if idx]
    everything = [i for _, idx in groups for i in idx]
    return groups + [("all answerable" if types == ANSWERABLE else "all", everything)]


# ---------------------------------------------------------------- retrieval

def timed_search(question: str, mode: str) -> tuple[list[int], float]:
    embeddings.embed_query.cache_clear()  # every timed search pays for its own embedding
    t0 = time.perf_counter()
    ids = [c.chunk_id for c in search(question, mode, k=10)]
    return ids, (time.perf_counter() - t0) * 1000


def retrieval_report(rows: list[dict], gold: list[set[int]]) -> list[str]:
    scored = [i for i, r in enumerate(rows) if r["type"] != "unanswerable"]
    q_rows, q_gold = [rows[i] for i in scored], [gold[i] for i in scored]
    embeddings.embed_query("warm up")  # load the model before timing anything
    ranked: dict[str, list[list[int]]] = {}
    latency: dict[str, list[float]] = {}
    for mode in MODES:
        runs = [timed_search(r["question"], mode) for r in q_rows]
        ranked[mode] = [ids for ids, _ in runs]
        latency[mode] = [ms for _, ms in runs]

    lines = [
        f"- Retrieval: bm25 = pg_search `|||` over unicode_words + English stemming; vector = "
        f"`{embeddings.MODEL}` ({embeddings.DIMENSIONS} dims, HNSW cosine); hybrid = RRF "
        f"(k={RRF_K}) over the top {CANDIDATES} of each",
        "- Unanswerable questions have no gold chunk, so they are not in the retrieval tables; "
        "see the relevance gate below",
        "",
    ]
    metrics = [
        ("hit@5", score.hit_at_k, "share of questions with a gold chunk in the top 5"),
        ("MRR@10", score.mrr_at_k, "mean 1/rank of the first gold chunk, 0 if not in the top 10"),
        ("recall@5", score.recall_at_k,
         "share of all gold chunks in the top 5; differs from hit@5 only for multi_chunk"),
    ]
    for name, fn, meaning in metrics:
        lines += [f"## {name}", "", meaning, "",
                  "| Question type | n | " + " | ".join(MODES) + " |",
                  "|---|---|" + "---|" * len(MODES)]
        for label, idx in by_type(q_rows, ANSWERABLE):
            cells = [f"{fn([ranked[m][i] for i in idx], [q_gold[i] for i in idx]):.3f}"
                     for m in MODES]
            lines.append(f"| {label} | {len(idx)} | " + " | ".join(cells) + " |")
        lines.append("")

    lines += ["## Search latency", "",
              "Milliseconds per query, including embedding the query on CPU (top 10, "
              f"{len(q_rows)} queries per mode).", "",
              "| Mode | p50 ms | p95 ms |", "|---|---|---|"]
    for mode in MODES:
        lines.append(f"| {mode} | {pct(latency[mode], 0.5):.0f} | {pct(latency[mode], 0.95):.0f} |")
    return lines + [""] + gate_report(rows)


def gate_report(rows: list[dict]) -> list[str]:
    """How the relevance gate (decline before any model call) splits the questions."""
    sims = [top_similarity(r["question"]) for r in rows]
    gate = answering.MIN_SIMILARITY
    answerable = [s for s, r in zip(sims, rows, strict=True) if r["type"] != "unanswerable"]
    unanswerable = [s for s, r in zip(sims, rows, strict=True) if r["type"] == "unanswerable"]
    lines = [
        "## Relevance gate",
        "",
        f"`app/answer.py` declines without calling the model when the closest chunk's cosine "
        f"similarity is below {gate}.",
        "",
        "| Questions | n | declined by the gate | lowest similarity | highest similarity |",
        "|---|---|---|---|---|",
    ]
    for label, group in [("answerable", answerable), ("unanswerable", unanswerable)]:
        if group:
            blocked = sum(s < gate for s in group)
            lines.append(f"| {label} | {len(group)} | {blocked} | {min(group):.3f} | "
                         f"{max(group):.3f} |")
    return lines


# ---------------------------------------------------------------- answers

def llm_usage(run_id: str) -> tuple[int, float | None, int] | None:
    """(calls, total cost, calls with unknown cost) for one run; None without a database."""
    try:
        with db.connect() as conn:
            return conn.execute(
                "SELECT count(*), sum(cost_usd), count(*) FILTER (WHERE cost_usd IS NULL)"
                " FROM llm_calls WHERE run_id = %s",
                (run_id,),
            ).fetchone()
    except psycopg.Error as e:  # the paid-for results still get written
        print(f"cost lookup skipped, database unreachable: {e}".strip(), file=sys.stderr)
        return None


def fmt_cost(usage, n: int) -> tuple[str, str]:
    if usage is None:
        return "n/a", "n/a (no database)"
    calls, total, unknown = usage
    if calls == 0:
        return "0", "$0"
    cost = "unknown" if total is None else f"${float(total) / n:.6f}"
    if unknown and total is not None:
        cost += f" (+{unknown} unpriced calls)"
    return str(calls), cost


def answer_report(rows, gold, mode: str, tier: str, run_id: str) -> tuple[list[str], int]:
    grades, latencies = [], []
    os.environ["EVAL_RUN"] = run_id  # common/llm.py tags llm_calls rows with it
    try:
        for row, g in zip(rows, gold, strict=True):
            t0 = time.perf_counter()
            try:
                result = answering.answer(row["question"], mode=mode, tier=tier)
            except Exception:  # a crashed case is a failed case, not a crashed eval
                result = None
                print(f"[{row['id']}] error:\n{traceback.format_exc()}", file=sys.stderr)
            latencies.append((time.perf_counter() - t0) * 1000)
            grades.append(score.grade_answer(result, row, g))
    finally:
        os.environ.pop("EVAL_RUN", None)

    errors = sum(g["error"] for g in grades)
    calls, cost = fmt_cost(llm_usage(run_id), len(rows))
    lines = [
        f"- Retrieval mode: {mode}, top {answering.TOP_K} chunks; model tier: {tier} "
        f"(`{llm.MODELS[tier]}`)",
        "",
        "| Question type | n | answer correct | citation precision | declined | errors |",
        "|---|---|---|---|---|---|",
    ]
    for label, idx in by_type(rows, ANSWERABLE):
        g = [grades[i] for i in idx]
        cited = sum(x["cited"] for x in g)
        precision = f"{sum(x['cited_gold'] for x in g) / cited:.3f}" if cited else "n/a"
        lines.append(f"| {label} | {len(g)} | {mean(g, 'correct'):.3f} | {precision} | "
                     f"{mean(g, 'declined'):.3f} | {sum(x['error'] for x in g)} |")
    unanswerable = [grades[i] for i, r in enumerate(rows) if r["type"] == "unanswerable"]
    if unanswerable:
        lines.append(f"| unanswerable (decline accuracy) | {len(unanswerable)} | - | - | "
                     f"{mean(unanswerable, 'declined'):.3f} | "
                     f"{sum(x['error'] for x in unanswerable)} |")
    lines += [
        "",
        "- answer correct: the answer contains the planted value as a whole token",
        "- citation precision: cited chunks that are gold chunks / all cited chunks",
        "",
        "| Latency p50 ms | Latency p95 ms | LLM calls | Cost / question |",
        "|---|---|---|---|",
        f"| {pct(latencies, 0.5):.0f} | {pct(latencies, 0.95):.0f} | {calls} | {cost} |",
    ]
    return lines, errors


def mean(grades: list[dict], key: str) -> float:
    return sum(g[key] for g in grades) / len(grades) if grades else 0.0


def estimate(rows: list[dict], mode: str, output_tokens: int) -> list[str]:
    """Cost of one answer run from the real prompts (about 4 characters per token)."""
    calls, input_tokens = 0, 0
    for row in rows:
        chunks = search(row["question"], mode, answering.TOP_K)
        if not chunks or top_similarity(row["question"]) < answering.MIN_SIMILARITY:
            continue  # the gate declines it: no model call
        chars = len(answering.SYSTEM) + len(answering.build_prompt(row["question"], chunks))
        input_tokens += chars // 4
        calls += 1
    lines = [
        f"Estimate for {len(rows)} questions: {calls} model calls (the rest are declined by the "
        f"relevance gate), {input_tokens} input tokens (prompt characters / 4), and an assumed "
        f"{output_tokens} output tokens per call (thinking included; not measured).",
        "Excludes the structured-output schema overhead, regenerations and schema retries.",
        "",
        "| Model | input $/MTok | output $/MTok | estimated cost |",
        "|---|---|---|---|",
    ]
    for model in dict.fromkeys(llm.MODELS.values()):
        price_in, price_out = llm.PRICES[model]
        cost = (input_tokens * price_in + calls * output_tokens * price_out) / 1_000_000
        lines.append(f"| `{model}` | {price_in:.2f} | {price_out:.2f} | ${cost:.4f} |")
    return lines


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Retrieval and answer evals")
    ap.add_argument("--split", choices=["dev", "test"], default="dev")
    ap.add_argument("--limit", type=int, help="first N questions only (smoke runs)")
    ap.add_argument("--answers", action="store_true", help="answer eval (calls the model API)")
    ap.add_argument("--estimate", action="store_true", help="with --answers: estimate, no API")
    ap.add_argument("--mode", choices=MODES, default="hybrid", help="retrieval for --answers")
    ap.add_argument("--tier", choices=["small", "large"], default="small")
    ap.add_argument("--output-tokens", type=int, default=300, help="assumption for --estimate")
    args = ap.parse_args(argv)

    rows = load(args.split, args.limit)
    stamp = datetime.now(UTC)
    command = "python -m evals.run " + " ".join(argv if argv is not None else sys.argv[1:])
    if args.answers and args.estimate:
        print("\n".join(estimate(rows, args.mode, args.output_tokens)))
        return 0

    gold = load_gold(rows)
    # A --limit smoke run gets its own file, so it never overwrites a full, reported run.
    suffix = f"-first{args.limit}" if args.limit else ""
    if args.answers:
        run_id = f"answers-{args.split}-{stamp:%Y%m%dT%H%M%SZ}"
        body, errors = answer_report(rows, gold, args.mode, args.tier, run_id)
        lines = header(f"Answer eval: {args.split}", command, stamp, rows, args.limit) + body
        out = RESULTS_DIR / f"results-answers-{args.split}{suffix}.md"
    else:
        lines = (header(f"Retrieval eval: {args.split}", command, stamp, rows, args.limit)
                 + retrieval_report(rows, gold))
        errors = 0
        out = RESULTS_DIR / f"results-retrieval-{args.split}{suffix}.md"
    out.write_text("\n".join(lines) + "\n")
    print(out.read_text())
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
