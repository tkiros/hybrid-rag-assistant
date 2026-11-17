# Retrieval eval: test

Generated 2026-11-17 12:03 UTC by `python -m evals.run --split test`. Do not edit by hand.

- Questions: 80 (exact_id 27, paraphrased 27, multi_chunk 13, unanswerable 13)
- Labels: synthetic, generated ground truth. Each question comes from a template over a fact planted in the corpus by data/generate.py; its gold chunk ids are found after ingestion by locating the fact's unique needle string
- Retrieval: bm25 = pg_search `|||` over unicode_words + English stemming; vector = `BAAI/bge-small-en-v1.5` (384 dims, HNSW cosine); hybrid = RRF (k=60) over the top 20 of each
- Unanswerable questions have no gold chunk, so they are not in the retrieval tables; see the relevance gate below

## hit@5

share of questions with a gold chunk in the top 5

| Question type | n | bm25 | vector | hybrid |
|---|---|---|---|---|
| exact_id | 27 | 1.000 | 0.444 | 1.000 |
| paraphrased | 27 | 0.148 | 0.519 | 0.407 |
| multi_chunk | 13 | 1.000 | 0.692 | 1.000 |
| all answerable | 67 | 0.657 | 0.522 | 0.761 |

## MRR@10

mean 1/rank of the first gold chunk, 0 if not in the top 10

| Question type | n | bm25 | vector | hybrid |
|---|---|---|---|---|
| exact_id | 27 | 0.889 | 0.292 | 0.818 |
| paraphrased | 27 | 0.115 | 0.405 | 0.237 |
| multi_chunk | 13 | 0.910 | 0.391 | 0.685 |
| all answerable | 67 | 0.581 | 0.357 | 0.558 |

## recall@5

share of all gold chunks in the top 5; differs from hit@5 only for multi_chunk

| Question type | n | bm25 | vector | hybrid |
|---|---|---|---|---|
| exact_id | 27 | 1.000 | 0.444 | 1.000 |
| paraphrased | 27 | 0.148 | 0.519 | 0.407 |
| multi_chunk | 13 | 0.500 | 0.346 | 0.500 |
| all answerable | 67 | 0.560 | 0.455 | 0.664 |

## Search latency

Milliseconds per query, including embedding the query on CPU (top 10, 67 queries per mode).

| Mode | p50 ms | p95 ms |
|---|---|---|
| bm25 | 28 | 38 |
| vector | 53 | 62 |
| hybrid | 61 | 67 |

## Relevance gate

`app/answer.py` declines without calling the model when the closest chunk's cosine similarity is below 0.6.

| Questions | n | declined by the gate | lowest similarity | highest similarity |
|---|---|---|---|---|
| answerable | 67 | 0 | 0.673 | 0.833 |
| unanswerable | 13 | 1 | 0.573 | 0.761 |
