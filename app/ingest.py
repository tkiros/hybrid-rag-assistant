"""Ingest the PDFs in data/pdfs into Postgres:  python -m app.ingest [--force]

Text is extracted page by page with pypdfium2, so every chunk knows its page. Each page is cut
at section headings; a section that runs onto the next page continues there under the same
heading path. A document is re-indexed only when its SHA-256 changes.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium

from app import embeddings
from common import db

PDF_DIR = Path(__file__).resolve().parent.parent / "data" / "pdfs"

# A heading is a whole line: a number (6.2.3 or §4.2.1) and an ALL-CAPS title. Body text never
# looks like that, because body lines always contain lowercase words.
HEADING = re.compile(r"^(§?\d+(?:\.\d+)*) ([A-Z0-9][A-Z0-9 ,()/&'-]*)$")
FOOTER = re.compile(r"\| Page \d+$")


@dataclass
class Chunk:
    page: int
    section: str | None  # heading path, e.g. "6 AIR END > 6.2 INLET VALVE > 6.2.3 INSTALLATION"
    text: str


def extract_pages(path: Path) -> list[str]:
    pdf = pdfium.PdfDocument(path)
    try:
        return [page.get_textpage().get_text_bounded() for page in pdf]
    finally:
        pdf.close()


def chunk_pages(pages: list[str]) -> list[Chunk]:
    """Split each page at headings. Chunks never cross a page, so citations stay exact."""
    chunks: list[Chunk] = []
    path: list[str] = []  # the headings we are under, outermost first
    for page_no, page_text in enumerate(pages, start=1):
        lines = [ln.strip() for ln in page_text.splitlines()]
        body: list[str] = []
        for line in lines:
            if not line or FOOTER.search(line):
                continue
            match = HEADING.match(line)
            if match:
                add_chunk(chunks, page_no, path, body)
                level = match.group(1).count(".") + 1
                path = path[: level - 1] + [line]
                body = [line]
            else:
                body.append(line)
        add_chunk(chunks, page_no, path, body)
    return chunks


def add_chunk(chunks: list[Chunk], page: int, path: list[str], lines: list[str]) -> None:
    """Keep lines as a chunk, unless they are just a heading with no text under it."""
    if not lines or (len(lines) == 1 and HEADING.match(lines[0])):
        return
    chunks.append(Chunk(page, " > ".join(path) or None, "\n".join(lines)))


def passage_text(chunk: Chunk) -> str:
    """What gets embedded: the heading path gives "INSTALLATION" its component name."""
    return f"{chunk.section}\n{chunk.text}" if chunk.section else chunk.text


def ingest(pdf_dir: Path = PDF_DIR, force: bool = False) -> dict[str, int]:
    """Index every PDF in pdf_dir. Returns {doc_id: chunks written} for re-indexed documents."""
    paths = sorted(pdf_dir.glob("*.pdf"))
    if not paths:
        raise SystemExit(f"no PDFs in {pdf_dir}; run `make data` first")
    written = {}
    with db.connect() as conn:
        # A PDF that was deleted or renamed takes its chunks with it (ON DELETE CASCADE).
        conn.execute("DELETE FROM documents WHERE doc_id <> ALL(%s)", ([p.stem for p in paths],))
        for path in paths:
            doc_id, sha = path.stem, hashlib.sha256(path.read_bytes()).hexdigest()
            row = conn.execute("SELECT sha256 FROM documents WHERE doc_id = %s", (doc_id,))
            if not force and row.fetchone() == (sha,):
                print(f"{doc_id}: unchanged, skipped")
                continue
            pages = extract_pages(path)
            chunks = chunk_pages(pages)
            vectors = embeddings.embed_passages([passage_text(c) for c in chunks])
            with conn.transaction():
                conn.execute("DELETE FROM documents WHERE doc_id = %s", (doc_id,))
                conn.execute("INSERT INTO documents (doc_id, sha256, pages) VALUES (%s, %s, %s)",
                             (doc_id, sha, len(pages)))
                # One COPY per document: pg_search then builds one compact BM25 segment
                # instead of one per row, which keeps keyword queries fast.
                with conn.cursor() as cur, cur.copy(
                    "COPY chunks (doc_id, page, section, text, embedding) FROM STDIN"
                ) as copy:
                    for chunk, vector in zip(chunks, vectors, strict=True):
                        copy.write_row((doc_id, chunk.page, chunk.section, chunk.text, vector))
            written[doc_id] = len(chunks)
            print(f"{doc_id}: {len(pages)} pages -> {len(chunks)} chunks")
    return written


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--force", action="store_true", help="re-index even if nothing changed")
    ingest(force=ap.parse_args().force)
