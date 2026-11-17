# Retrieval eval: dev

Generated 2026-11-17 12:03 UTC by `python -m evals.run --split dev`. Do not edit by hand.

- Questions: 40 (exact_id 13, paraphrased 13, multi_chunk 7, unanswerable 7)
- Labels: synthetic, generated ground truth. Each question comes from a template over a fact planted in the corpus by data/generate.py; its gold chunk ids are found after ingestion by locating the fact's unique needle string
- Retrieval: bm25 = pg_search `|||` over unicode_words + English stemming; vector = `BAAI/bge-small-en-v1.5` (384 dims, HNSW cosine); hybrid = RRF (k=60) over the top 20 of each
- Unanswerable questions have no gold chunk, so they are not in the retrieval tables; see the relevance gate below

## hit@5

share of questions with a gold chunk in the top 5

| Question type | n | bm25 | vector | hybrid |
|---|---|---|---|---|
| exact_id | 13 | 1.000 | 0.385 | 0.923 |
| paraphrased | 13 | 0.308 | 0.692 | 0.692 |
| multi_chunk | 7 | 1.000 | 0.714 | 1.000 |
| all answerable | 33 | 0.727 | 0.576 | 0.848 |

## MRR@10

mean 1/rank of the first gold chunk, 0 if not in the top 10

| Question type | n | bm25 | vector | hybrid |
|---|---|---|---|---|
| exact_id | 13 | 0.923 | 0.378 | 0.857 |
| paraphrased | 13 | 0.195 | 0.564 | 0.531 |
| multi_chunk | 7 | 0.929 | 0.385 | 0.814 |
| all answerable | 33 | 0.637 | 0.453 | 0.719 |

## recall@5

share of all gold chunks in the top 5; differs from hit@5 only for multi_chunk

| Question type | n | bm25 | vector | hybrid |
|---|---|---|---|---|
| exact_id | 13 | 1.000 | 0.385 | 0.923 |
| paraphrased | 13 | 0.308 | 0.692 | 0.692 |
| multi_chunk | 7 | 0.643 | 0.357 | 0.500 |
| all answerable | 33 | 0.652 | 0.500 | 0.742 |

## Search latency

Milliseconds per query, including embedding the query on CPU (top 10, 33 queries per mode).

| Mode | p50 ms | p95 ms |
|---|---|---|
| bm25 | 28 | 43 |
| vector | 49 | 61 |
| hybrid | 60 | 70 |

## Relevance gate

`app/answer.py` declines without calling the model when the closest chunk's cosine similarity is below 0.6.

| Questions | n | declined by the gate | lowest similarity | highest similarity |
|---|---|---|---|---|
| answerable | 33 | 0 | 0.659 | 0.847 |
| unanswerable | 7 | 0 | 0.610 | 0.720 |
