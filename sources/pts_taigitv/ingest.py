"""公視台語台 新詞辭典 (via taigikeyboard/kemdict-data-pts-taigitv).

Each entry has: id, title (Han), pn[] (台羅 romanization), zh (華文),
tags[] ({id, title} category objects).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata
from corpus.scrapers.pts_taigitv import scrape_and_save

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "sources.pts_taigitv.ingest@v2"
PROCESSOR_VERSION = "corpus.scrapers.pts_taigitv@v1"


def _compose_text(word: dict) -> str:
    title = (word.get("title") or "").strip()
    if not title:
        return ""
    lines = [title]
    pn = [p.strip() for p in (word.get("pn") or []) if p and p.strip()]
    if pn:
        lines.append(f"拼音: {' / '.join(pn)}")
    zh = (word.get("zh") or "").strip()
    if zh and zh != title:
        lines.append(f"華文: {zh}")
    return "\n".join(lines)


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        words = json.load(f)
    logger.info("Loaded %d entries from %s", len(words), json_path.name)

    now = datetime.now(timezone.utc)

    for word in words:
        text = normalize(_compose_text(word))
        if not text:
            continue
        word_id = str(word.get("id") or "noid")
        tags = ["dictionary"]
        for t in word.get("tags", []):
            title = (t.get("title") or "").strip()
            if title:
                tags.append(f"category:{title}")

        yield Document(
            id=f"{source.source_id}:{word_id}",
            text=text,
            metadata=DocumentMetadata.from_source(
                source,
                format="json",
                collected_at=now,
                script=Script.HANLO,
                tags=tags,
            ),
            provenance=Provenance(
                raw_path=f"{json_path.name}#id={word_id}",
                extractor=EXTRACTOR_VERSION,
                processor=PROCESSOR_VERSION,
                content_hash=content_hash(text),
            ),
        )
