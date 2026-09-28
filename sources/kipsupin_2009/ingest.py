"""教育部臺灣閩南語字詞頻調查 2009 — paragraph-aligned Han-Lo / romanization pieces.

One Document per 篇. text = Han / Han-Lo paragraphs, metadata.parallel_poj =
numeric-tone romanization (mostly POJ, some Tâi-lô). 書寫系統 names the work's
original writing system; the Han-Lo side exists for every piece.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata
from corpus.scrapers.doc2json import scrape_and_save

logger = logging.getLogger(__name__)

REPO = "Taiwanese-Corpus/Ungian_2009_KIPsupin"
EXTRACTOR_VERSION = "sources.kipsupin_2009.ingest@v1"
PROCESSOR_VERSION = "corpus.scrapers.doc2json@v1"


def _side(pairs: list[list[str]], index: int) -> str:
    """One normalized line per pair, so text and parallel_poj stay line-aligned."""
    return "\n".join(normalize(pair[index]).replace("\n", " ") for pair in pairs)


def _field(piece: dict, work: dict, key: str) -> str:
    value = piece.get(key) or work.get(key) or ""
    value = str(value).strip()
    return "" if value == "0" else value


def _build_tags(collection: str, piece: dict, work: dict) -> list[str]:
    tags = [f"collection:{collection}", "script:poj-numerical"]
    for key, prefix in (("文類", "category"), ("書寫系統", "original-script"), ("年級別", "grade")):
        value = _field(piece, work, key)
        if value:
            tags.append(f"{prefix}:{value}")
    return tags


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(REPO, source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        works = json.load(f)
    logger.info("Loaded %d works from %s", len(works), json_path.name)

    now = datetime.now(timezone.utc)
    for work in works:
        work_id = work["來源檔"]
        collection = work_id.split("/", 1)[0]
        for index, piece in enumerate(work.get("資料") or [], start=1):
            pairs = piece.get("段") or []
            text = _side(pairs, 0)
            if not text.strip():
                continue
            yield Document(
                id=f"{source.source_id}:{work_id}-{index}",
                text=text,
                metadata=DocumentMetadata.from_source(
                    source,
                    format="json",
                    collected_at=now,
                    script=Script.HANLO,
                    publication_date=_field(piece, work, "出版年"),
                    author=_field(piece, work, "作者"),
                    title=(piece.get("篇名") or "").strip() or _field(piece, work, "書名"),
                    tags=_build_tags(collection, piece, work),
                    parallel_poj=_side(pairs, 1),
                ),
                provenance=Provenance(
                    raw_path=f"{json_path.name}#{work_id}/{index}",
                    extractor=EXTRACTOR_VERSION,
                    processor=PROCESSOR_VERSION,
                    content_hash=content_hash(text),
                ),
            )
