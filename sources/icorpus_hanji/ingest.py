"""iCorpus Han-character / Tâi-lô edition — word-aligned Taiwanese news.

Each scraped article has 文號, 日期 and three line-aligned lists: 漢字 (Han
words separated by spaces), 音標 (numeric-tone Tâi-lô, one token per 漢字 word)
and 華語 (Mandarin). One Document per article.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata
from corpus.scrapers.icorpus_hanji import scrape_and_save

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "sources.icorpus_hanji.ingest@v1"
PROCESSOR_VERSION = "corpus.scrapers.icorpus_hanji@v1"
TAGS = ["news", "parallel", "script:tl-numerical", "segmented:word", "aligned:word"]


def _aligned(lines: list[str]) -> str:
    """Normalize line by line so the three aligned fields keep one line per sentence."""
    return "\n".join(normalize(line) for line in lines)


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        articles = json.load(f)
    logger.info("Loaded %d articles from %s", len(articles), json_path.name)

    now = datetime.now(timezone.utc)
    for article in articles:
        text = _aligned(article["漢字"])
        if not text.strip():
            continue
        article_id = str(article["文號"])
        zh_lines = article["華語"]
        yield Document(
            id=f"{source.source_id}:{article_id}",
            text=text,
            metadata=DocumentMetadata.from_source(
                source,
                format="txt",
                collected_at=now,
                script=Script.HAN,
                publication_date=article.get("日期") or "",
                title=(zh_lines[0].strip() if zh_lines else ""),
                tags=TAGS,
                parallel_zh=_aligned(zh_lines),
                parallel_poj=_aligned(article["音標"]),
            ),
            provenance=Provenance(
                raw_path=f"{json_path.name}#文號={article_id}",
                extractor=EXTRACTOR_VERSION,
                processor=PROCESSOR_VERSION,
                content_hash=content_hash(text),
            ),
        )
