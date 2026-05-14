"""台語工藝詞庫 (via taigikeyboard/kanggesu-data).

Each entry has: entriesBaseId, chineseCharacters, taiwaneseCharacters,
romanizationSystem (台羅), memo (Mandarin prose description), audioPath,
mainTypeName + childTypeName (categories), provider, isHaveImage.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata
from corpus.scrapers.kanggesu import scrape_and_save

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "sources.kanggesu.ingest@v2"
PROCESSOR_VERSION = "corpus.scrapers.kanggesu@v1"


def _compose_text(entry: dict) -> str:
    tw = (entry.get("taiwaneseCharacters") or "").strip()
    zh = (entry.get("chineseCharacters") or "").strip()
    headword = tw or zh
    if not headword:
        return ""
    lines = [headword]
    pn = (entry.get("romanizationSystem") or "").strip()
    if pn:
        lines.append(f"拼音: {pn}")
    if zh and zh != tw:
        lines.append(f"華文: {zh}")
    memo = (entry.get("memo") or "").strip()
    if memo:
        lines.append(f"備註: {memo}")
    return "\n".join(lines)


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        entries = json.load(f)
    logger.info("Loaded %d entries from %s", len(entries), json_path.name)

    now = datetime.now(timezone.utc)

    for entry in entries:
        text = normalize(_compose_text(entry))
        if not text:
            continue
        entry_id = str(entry.get("entriesBaseId") or "noid")
        tags = ["dictionary"]
        for key in ("mainTypeName", "childTypeName"):
            v = (entry.get(key) or "").strip()
            if v:
                tags.append(f"category:{v}")
        provider = (entry.get("provider") or "").strip()

        yield Document(
            id=f"{source.source_id}:{entry_id}",
            text=text,
            metadata=DocumentMetadata.from_source(
                source,
                format="json",
                collected_at=now,
                script=Script.HANLO,
                author=provider,
                tags=tags,
            ),
            provenance=Provenance(
                raw_path=f"{json_path.name}#id={entry_id}",
                extractor=EXTRACTOR_VERSION,
                processor=PROCESSOR_VERSION,
                content_hash=content_hash(text),
            ),
        )
