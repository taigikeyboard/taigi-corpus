"""國校仔課本 — elementary-school Taiwanese textbook lessons.

Each upstream volume has 出版者, 年級別, 書名, 書寫系統 (漢字), 來源檔, and
資料 = list of 篇 {篇名, 段}, where 段 is a list of [漢字, 台羅] line pairs.
One Document per 篇 (lesson): text = 漢字 lines, metadata.parallel_poj = 台羅.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata
from corpus.scrapers.kok4hau7 import scrape_and_save

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "sources.kok4hau7.ingest@v1"
PROCESSOR_VERSION = "corpus.scrapers.kok4hau7@v1"


def _build_tags(publisher: str, grade: str, book_title: str) -> list[str]:
    tags = ["subset:kok4hau7"]
    if publisher:
        tags.append(f"publisher:{publisher}")
    if grade:
        tags.append(f"grade:{grade}")
    if book_title:
        tags.append(f"book:{book_title}")
    return tags


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        books = json.load(f)
    logger.info("Loaded %d volumes from %s", len(books), json_path.name)

    now = datetime.now(timezone.utc)
    for book in books:
        volume_id = (book.get("來源檔") or "noid").strip() or "noid"
        publisher = (book.get("出版者") or "").strip()
        grade = (book.get("年級別") or "").strip()
        book_title = (book.get("書名") or "").strip()
        pub_year = (book.get("出版年") or "").strip()
        if pub_year == "0":
            pub_year = ""
        tags = _build_tags(publisher, grade, book_title)

        for lesson_index, lesson in enumerate(book.get("資料") or [], start=1):
            pairs = lesson.get("段") or []
            han_lines = [(p[0] if len(p) > 0 else "") for p in pairs]
            tailo_lines = [(p[1] if len(p) > 1 else "") for p in pairs]

            text = normalize("\n".join(han_lines).strip())
            parallel_poj = normalize("\n".join(tailo_lines).strip())
            if not text:
                continue

            yield Document(
                id=f"{source.source_id}:{volume_id}-{lesson_index}",
                text=text,
                metadata=DocumentMetadata.from_source(
                    source,
                    format="json",
                    collected_at=now,
                    script=Script.HAN,
                    publication_date=pub_year,
                    title=(lesson.get("篇名") or "").strip(),
                    tags=tags,
                    parallel_poj=parallel_poj,
                ),
                provenance=Provenance(
                    raw_path=f"{json_path.name}#{volume_id}/{lesson_index}",
                    extractor=EXTRACTOR_VERSION,
                    processor=PROCESSOR_VERSION,
                    content_hash=content_hash(text),
                ),
            )
