"""The HTTP API with FastAPI's test client. Needs the database; the model API is faked."""

import json

import pytest
from fastapi.testclient import TestClient

from app import answer as answering
from app.main import app
from common import llm
from tests.helpers import fake_api, needs_chunks, reply

pytestmark = needs_chunks
client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_search_returns_cited_chunks():
    chunks = client.get("/search", params={"q": "oil filter", "mode": "bm25", "k": 3}).json()
    assert len(chunks) == 3 and {"chunk_id", "doc_id", "page"} <= set(chunks[0])


@pytest.mark.parametrize("params", [{"q": ""}, {"q": "x", "mode": "fuzzy"}, {"q": "x", "k": 99}])
def test_search_rejects_bad_input(params):
    assert client.get("/search", params=params).status_code == 422


def test_ask_returns_an_answer_with_page_links(monkeypatch):
    def cite_first(body):
        first = int(body["messages"][0]["content"].split('<chunk id="')[1].split('"')[0])
        return reply(json.dumps({"answer": "From the manual.", "citations": [first],
                                 "declined": False}))

    fake_api(monkeypatch, cite_first, keep_db=True)
    body = client.post("/ask", json={"question": "What is the torque for the inlet valve?"}).json()
    assert body["declined"] is False
    url = body["citations"][0]["url"]
    assert url.startswith("/pdf/") and "#page=" in url
    pdf = client.get(url.split("#")[0])
    assert pdf.status_code == 200 and pdf.content[:5] == b"%PDF-"


def test_ask_without_credentials_is_a_clear_503(monkeypatch):
    def no_key(*args, **kwargs):  # what the SDK raises before sending anything
        raise TypeError("Could not resolve authentication method. Expected one of api_key, ...")

    monkeypatch.setattr(answering, "answer", no_key)
    response = client.post("/ask", json={"question": "anything"})
    assert response.status_code == 503 and "ANTHROPIC_API_KEY" in response.json()["detail"]


def test_ask_model_failure_is_a_502(monkeypatch):
    def refused(*args, **kwargs):
        raise llm.LLMError("answer: refused (category=None)")

    monkeypatch.setattr(answering, "answer", refused)
    response = client.post("/ask", json={"question": "anything"})
    assert response.status_code == 502 and "refused" in response.json()["detail"]


def test_ask_rejects_an_empty_question():
    assert client.post("/ask", json={"question": ""}).status_code == 422
