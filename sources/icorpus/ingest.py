"""台華平行新聞語料庫 (中研院 陳孟彰; sih4sing5hong5/icorpus).

Each entry has: 台語 (numerical POJ, line-segmented), 華語 (segmented
Mandarin, line-segmented), 文號 (1..N), 日期 (YYYY-MM-DD).
"""

import logging
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata
from corpus.scrapers.icorpus import scrape_and_save

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "sources.icorpus.ingest@v1"
PROCESSOR_VERSION = "corpus.scrapers.icorpus@v1"


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        entries = json.load(f)
    logger.info("Loaded %d entries from %s", len(entries), json_path.name)

    now = datetime.now(timezone.utc)

    for entry in entries:
        tw = normalize((entry.get("台語") or "").strip())
        zh = normalize((entry.get("華語") or "").strip())
        if not tw:
            continue

        article_id = str(entry.get("文號") or "noid")
        pub_date = (entry.get("日期") or "").strip()
        title = zh.split("\n", 1)[0] if zh else tw.split("\n", 1)[0]

        yield Document(
            id=f"{source.source_id}:{article_id}",
            text=tw,
            metadata=DocumentMetadata.from_source(
                source,
                format="json",
                collected_at=now,
                script=Script.LO,
                publication_date=pub_date,
                title=title,
                tags=["news", "parallel", "script:poj-numerical"],
                parallel_zh=zh,
            ),
            provenance=Provenance(
                raw_path=f"{json_path.name}#文號={article_id}",
                extractor=EXTRACTOR_VERSION,
                processor=PROCESSOR_VERSION,
                content_hash=content_hash(tw),
            ),
        )
