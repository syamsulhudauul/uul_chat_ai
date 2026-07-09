from app.agent.chunking import chunk_markdown

FIXTURE_DOC = """# Resume — syamsulhudauul

## Summary

Applied AI Engineer.

## Current Role

Senior Engineer at Example Co.

- Built RAG pipelines
- Owned agent tooling
"""


def test_chunk_markdown_splits_by_h2_heading():
    chunks = chunk_markdown(FIXTURE_DOC, "resume.md")

    assert len(chunks) == 3


def test_chunk_markdown_preamble_is_first_chunk():
    chunks = chunk_markdown(FIXTURE_DOC, "resume.md")

    assert chunks[0]["metadata"]["heading"] is None
    assert "Resume" in chunks[0]["content"]
    assert chunks[0]["source_doc"] == "resume.md"


def test_chunk_markdown_each_heading_becomes_its_own_chunk():
    chunks = chunk_markdown(FIXTURE_DOC, "resume.md")

    assert chunks[1]["metadata"]["heading"] == "Summary"
    assert "Applied AI Engineer" in chunks[1]["content"]

    assert chunks[2]["metadata"]["heading"] == "Current Role"
    assert "Senior Engineer at Example Co." in chunks[2]["content"]
    assert "Built RAG pipelines" in chunks[2]["content"]


def test_chunk_markdown_skips_empty_sections():
    doc = "## Empty\n\n## Filled\n\nsome content"
    chunks = chunk_markdown(doc, "doc.md")

    headings = [c["metadata"]["heading"] for c in chunks]
    assert "Empty" not in headings
    assert "Filled" in headings


def test_chunk_markdown_no_headings_returns_single_preamble_chunk():
    doc = "Just some plain text, no headings at all."
    chunks = chunk_markdown(doc, "doc.md")

    assert len(chunks) == 1
    assert chunks[0]["metadata"]["heading"] is None
