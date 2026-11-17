"""Retrieval. search(query, mode) where mode is one of:

  bm25    keyword match (ParadeDB pg_search): strong on exact identifiers like HX-4471-B
  vector  meaning match (pgvector + bge-small): strong on paraphrased questions
  hybrid  both lists fused with Reciprocal Rank Fusion (RRF)
"""

from __future__ import annotations

import psycopg
from pydantic import BaseModel

from app.embeddings import embed_query
from common import db

MODES = ("bm25", "vector", "hybrid")
# How many results each retriever feeds into RRF. Chosen on dev (evals/results-tuning-dev.md):
# with 40, chunks that are mediocre in BOTH lists outrank a chunk that one retriever ranks
# first. Keep it <= 40: pgvector's HNSW index returns at most hnsw.ef_search (40) rows.
CANDIDATES = 20
RRF_K = 60  # the constant from Cormack et al. (2009); dampens the weight of the top ranks


class Chunk(BaseModel):
    chunk_id: int
    doc_id: str
    page: int
    section: str | None
    text: str


def rrf(*ranked_lists: list[int], k: int = RRF_K) -> list[int]:
    """Reciprocal Rank Fusion: each list adds 1 / (k + rank) to an id's score.

    Only ranks matter, so BM25 scores and cosine distances never need to be put on one scale.
    """
    scores: dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, chunk_id in enumerate(ranked, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)


def bm25_ids(conn: psycopg.Connection, query: str, limit: int) -> list[int]:
    # `|||` means "match any term". The query text goes through the column's tokenizer, never
    # through a query parser, so quotes, colons, AND/OR or "§" in user text can't cause a
    # syntax error. `id` breaks score ties so results are repeatable.
    rows = conn.execute(
        "SELECT id FROM chunks WHERE text ||| %s::text ORDER BY pdb.score(id) DESC, id LIMIT %s",
        (query, limit),
    ).fetchall()
    return [r[0] for r in rows]


def vector_ids(conn: psycopg.Connection, query: str, limit: int) -> list[int]:
    rows = conn.execute(
        "SELECT id FROM chunks ORDER BY embedding <=> %s::vector LIMIT %s",
        (embed_query(query), limit),
    ).fetchall()
    return [r[0] for r in rows]


def ranked_ids(conn: psycopg.Connection, query: str, mode: str, k: int) -> list[int]:
    if mode == "bm25":
        return bm25_ids(conn, query, k)
    if mode == "vector":
        return vector_ids(conn, query, k)
    return rrf(bm25_ids(conn, query, CANDIDATES), vector_ids(conn, query, CANDIDATES))[:k]


def search(query: str, mode: str = "hybrid", k: int = 5) -> list[Chunk]:
    """Top-k chunks for query, best first. An empty query returns no chunks."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, not {mode!r}")
    if not query.strip():
        return []
    with db.connect() as conn:
        ids = ranked_ids(conn, query, mode, k)
        rows = conn.execute(
            "SELECT id, doc_id, page, section, text FROM chunks WHERE id = ANY(%s)", (ids,)
        ).fetchall()
    by_id = {r[0]: Chunk(chunk_id=r[0], doc_id=r[1], page=r[2], section=r[3], text=r[4])
             for r in rows}
    return [by_id[i] for i in ids]


def top_similarity(query: str) -> float:
    """Cosine similarity between the query and its closest chunk (1.0 = same direction)."""
    with db.connect() as conn:
        row = conn.execute(
            "SELECT 1 - (embedding <=> %s::vector) FROM chunks ORDER BY embedding <=> %s::vector"
            " LIMIT 1",
            (embed_query(query), embed_query(query)),
        ).fetchone()
    return float(row[0]) if row else 0.0
