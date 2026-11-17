-- Documents and their chunks, with a vector index and a BM25 index on the same table.
-- Runs once, on a fresh volume, after 20_app_schema.sql.

CREATE TABLE IF NOT EXISTS documents (
    doc_id      text        PRIMARY KEY,          -- PDF file name without .pdf
    sha256      text        NOT NULL,             -- a changed hash means "re-index this document"
    pages       int         NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id        bigserial PRIMARY KEY,
    doc_id    text      NOT NULL REFERENCES documents ON DELETE CASCADE,
    page      int       NOT NULL,                 -- 1-based page in the PDF
    section   text,                               -- heading path, e.g. "6 AIR END > 6.2 INLET VALVE"
    text      text      NOT NULL,
    embedding vector(384) NOT NULL                -- BAAI/bge-small-en-v1.5 (app/embeddings.py)
);

-- Vector search: HNSW over cosine distance (pgvector).
CREATE INDEX IF NOT EXISTS chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);

-- Keyword search: BM25 (ParadeDB pg_search 0.26; the first column is the key, key_field is no
-- longer needed). unicode_words keeps "4.2.1" as one token, where the default tokenizer splits
-- it into 4 / 2 / 1 and can't tell §4.2.1 from §2.1.4. English stemming and stopwords help
-- plain-language questions ("returned" matches "return").
-- mutable_segment_rows = 0 writes rows straight into searchable segments. With the default,
-- new rows wait in a "mutable segment" that made every query here ~30x slower (measured with
-- EXPLAIN ANALYZE on the dev machine); app/ingest.py also loads each document with one COPY.
CREATE INDEX IF NOT EXISTS chunks_bm25 ON chunks USING bm25 (
    id, (text::pdb.unicode_words('stemmer=english', 'stopwords_language=english'))
) WITH (mutable_segment_rows = 0);
