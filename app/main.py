"""HTTP API:  uvicorn app.main:app --port 8003

  GET  /health                       database reachable
  GET  /search?q=...&mode=hybrid&k=5 ranked chunks (no API key needed)
  POST /ask {"question": "..."}      cited answer, or "Not in the documents."
  GET  /pdf/<doc>.pdf#page=N         the source PDFs, so citation links open at the page
"""

from typing import Literal

import anthropic
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import answer as answering
from app.ingest import PDF_DIR
from app.search import Chunk, search
from common import db, llm

app = FastAPI(title="Hybrid RAG assistant")
PDF_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/pdf", StaticFiles(directory=PDF_DIR), name="pdf")

Mode = Literal["bm25", "vector", "hybrid"]


class Ask(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    mode: Mode = "hybrid"


@app.get("/health")
def health() -> dict[str, str]:
    with db.connect() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/search")
def search_chunks(q: str = Query(min_length=1, max_length=2000), mode: Mode = "hybrid",
                  k: int = Query(5, ge=1, le=20)) -> list[Chunk]:
    return search(q, mode, k)


@app.post("/ask")
def ask(body: Ask) -> answering.Result:
    try:
        return answering.answer(body.question, mode=body.mode)
    except (llm.LLMError, anthropic.APIError) as e:  # refused, truncated, API down: say so
        raise HTTPException(status_code=502, detail=str(e)) from e
    except TypeError as e:  # how the SDK reports missing credentials, before any request
        if "authentication" not in str(e):
            raise
        raise HTTPException(status_code=503, detail="No model credentials: set "
                            "ANTHROPIC_API_KEY or run `ant auth login`.") from e
