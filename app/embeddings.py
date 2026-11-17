"""Local text embeddings: fastembed runs the model on CPU with ONNX, so no API key and no torch.

The model (~67 MB) downloads from Hugging Face on first use and is cached after that.
"""

from functools import cache, lru_cache

from fastembed import TextEmbedding

MODEL = "BAAI/bge-small-en-v1.5"
DIMENSIONS = 384  # must match vector(384) in db/init/30_chunks.sql


@cache
def model() -> TextEmbedding:
    return TextEmbedding(MODEL)


def embed_passages(texts: list[str]) -> list[str]:
    """Embed chunk texts; returns pgvector literals ready for INSERT."""
    return [to_pgvector(v) for v in model().passage_embed(texts)]


@lru_cache(maxsize=4096)
def embed_query(text: str) -> str:
    """Embed one query. Cached because hybrid search and the relevance gate embed it twice."""
    return to_pgvector(next(iter(model().query_embed(text))))


def to_pgvector(vector) -> str:
    """pgvector's text format ('[0.1,0.2,...]'), so no extra driver package is needed."""
    return "[" + ",".join(f"{x:.6f}" for x in vector) + "]"
