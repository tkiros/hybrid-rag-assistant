"""Shared test helpers: a fake Messages API (real SDK, mocked HTTP) and database checks."""

import json
import os
from collections.abc import Callable

import anthropic
import httpx2
import psycopg
import pytest

from common import llm


def reply(text: str, stop: str = "end_turn", **extra) -> dict:
    return {"text": text, "stop": stop, **extra}


def fake_api(monkeypatch, replies: list[dict] | Callable[[dict], dict],
             keep_db: bool = False) -> list[dict]:
    """Point llm at a fake API and return the captured requests.

    `replies` is either a list answered in order, or a function from request body to reply.
    No API key, no network, no cost.
    """
    seen: list[dict] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        body = json.loads(request.content)
        seen.append({"headers": request.headers, "body": body})
        r = replies(body) if callable(replies) else replies[len(seen) - 1]
        return httpx2.Response(200, json={
            "id": f"msg_{len(seen)}", "type": "message", "role": "assistant",
            "model": body["model"], "content": [{"type": "text", "text": r["text"]}],
            "stop_reason": r["stop"], "stop_sequence": None,
            "stop_details": r.get("stop_details"),
            "usage": {"input_tokens": 1000, "output_tokens": 100},
        })

    http = anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler))
    fake = anthropic.Anthropic(api_key="test", http_client=http, max_retries=0)
    monkeypatch.setattr(llm, "_client", fake)
    if not keep_db:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    return seen


def _count_chunks() -> int | None:
    """Number of ingested chunks, or None when the database is unreachable."""
    try:
        with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=2) as conn:
            return conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
    except (KeyError, psycopg.Error):
        return None


_CHUNKS = _count_chunks()
needs_db = pytest.mark.skipif(_CHUNKS is None, reason="needs `make up` (DATABASE_URL reachable)")
needs_chunks = pytest.mark.skipif(not _CHUNKS, reason="needs `make up` and `make ingest`")
