"""PDF chunking (no database) and the generated corpus round-trip through real PDFs."""

import hashlib

import pytest

from app.ingest import HEADING, Chunk, chunk_pages, extract_pages
from data import generate


def test_chunks_split_at_headings_and_keep_page_numbers():
    pages = [
        "6 AIR END\r\n6.1 INLET VALVE\r\n6.1.1 DESCRIPTION\r\nThe inlet valve opens.\r\n"
        "6.1.2 REMOVAL\r\n1. Stop the compressor.\r\nManual | Page 1",
        "2. Remove the panel.\r\n6.2 OIL FILTER\r\nThe oil filter cleans oil.\r\nManual | Page 2",
    ]
    assert chunk_pages(pages) == [
        Chunk(1, "6 AIR END > 6.1 INLET VALVE > 6.1.1 DESCRIPTION",
              "6.1.1 DESCRIPTION\nThe inlet valve opens."),
        Chunk(1, "6 AIR END > 6.1 INLET VALVE > 6.1.2 REMOVAL",
              "6.1.2 REMOVAL\n1. Stop the compressor."),
        # a section that runs onto the next page keeps its heading path there
        Chunk(2, "6 AIR END > 6.1 INLET VALVE > 6.1.2 REMOVAL", "2. Remove the panel."),
        Chunk(2, "6 AIR END > 6.2 OIL FILTER", "6.2 OIL FILTER\nThe oil filter cleans oil."),
    ]


@pytest.mark.parametrize("line, is_heading", [
    ("6.2.3 INSTALLATION", True),
    ("§4.2.1 OPENED ITEMS", True),
    ("14.1.3 GASKET, INLET VALVE", True),
    ("5.2.14 E-1427 INLET VALVE FAILED TO OPEN", True),
    ("1. Stop the compressor, open the main isolator.", False),
    ("38.5 Nm. Replace part HX-4471-B.", False),
    ("4.2.1 opened items", False),
    ("HALVARD RS-SERIES PARTS AND SERVICE MANUAL", False),
])
def test_heading_pattern(line, is_heading):
    assert bool(HEADING.match(line)) is is_heading


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    """The real corpus, built and rendered to PDF in a temp folder."""
    docs, dev, test = generate.build()
    out = tmp_path_factory.mktemp("pdfs")
    for doc_id, blocks in docs.items():
        generate.render(blocks, doc_id.upper(), "subtitle", "Footer", out / f"{doc_id}.pdf")
    return docs, dev, test, out


def test_every_generated_heading_survives_pdf_extraction(rendered):
    docs, _, _, out = rendered
    for doc_id, blocks in docs.items():
        chunks = chunk_pages(extract_pages(out / f"{doc_id}.pdf"))
        wanted = {f"{b[1]} {b[2]}" for b in blocks if b[0] == "heading"}
        found = {h for c in chunks if c.section for h in c.section.split(" > ")}
        assert found == wanted, doc_id


def test_every_needle_lands_in_exactly_one_chunk_with_its_value(rendered):
    """Label integrity: the gold chunk exists after PDF round-trip and holds the answer."""
    docs, dev, test, out = rendered
    texts = [" ".join(c.text.split()) for doc_id in docs
             for c in chunk_pages(extract_pages(out / f"{doc_id}.pdf"))]
    for row in dev + test:
        for needle in row["gold_needles"]:
            assert sum(needle in t for t in texts) == 1, (row["id"], needle)
        if row["must_contain"]:
            last = next(t for t in texts if row["gold_needles"][-1] in t)
            assert row["must_contain"] in last, row["id"]


def test_generation_is_deterministic(tmp_path):
    first, second = generate.build(), generate.build()
    assert first[1:] == second[1:]
    docs = first[0]
    for name in ("a.pdf", "b.pdf"):
        generate.render(docs[generate.HANDBOOK], "T", "S", "F", tmp_path / name)
    digest = [hashlib.sha256((tmp_path / n).read_bytes()).hexdigest() for n in ("a.pdf", "b.pdf")]
    assert digest[0] == digest[1]


def test_question_mix_and_split():
    _, dev, test = generate.build()
    assert len(dev) == 40 and len(test) == 80
    for type_, total in generate.TYPE_COUNTS.items():
        n_dev = sum(q["type"] == type_ for q in dev)
        n_test = sum(q["type"] == type_ for q in test)
        assert n_dev == generate.DEV_COUNTS[type_] and n_dev + n_test == total
    assert not {q["id"] for q in dev} & {q["id"] for q in test}
    assert all(q["gold_needles"] == [] for q in dev + test if q["type"] == "unanswerable")
    assert all(len(q["gold_needles"]) == 2 for q in dev + test if q["type"] == "multi_chunk")
