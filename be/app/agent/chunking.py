import re

_HEADING_RE = re.compile(r"(?m)^##\s+(.+)$")


def chunk_markdown(content: str, source_doc: str) -> list[dict]:
    """Split a markdown doc into one chunk per top-level (##) section.

    Content before the first ## heading (if any) becomes its own chunk
    with metadata.heading = None.
    """
    sections = _HEADING_RE.split(content)

    chunks = []
    preamble = sections[0].strip()
    if preamble:
        chunks.append(
            {"content": preamble, "source_doc": source_doc, "metadata": {"heading": None}}
        )

    for i in range(1, len(sections), 2):
        heading = sections[i].strip()
        body = sections[i + 1].strip() if i + 1 < len(sections) else ""
        if not body:
            continue
        chunks.append(
            {
                "content": f"{heading}\n{body}",
                "source_doc": source_doc,
                "metadata": {"heading": heading},
            }
        )

    return chunks
