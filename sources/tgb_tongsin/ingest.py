"""TGB通訊 — Han-Lo Taiwanese articles with their Mandarin version.

text = the Taiwanese article (Han characters with POJ words inline);
metadata.parallel_zh = the Mandarin version, whose first line is the title,
optionally followed by `@author`. Paragraphs are not aligned across the two.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata
from corpus.scrapers.tgb_tongsin import scrape_and_save

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "sources.tgb_tongsin.ingest@v1"
PROCESSOR_VERSION = "corpus.scrapers.tgb_tongsin@v1"
TAGS = ["script:hanlo-poj", "parallel:zh-unaligned"]


def _title_and_author(zh: str) -> tuple[str, str]:
    first = zh.strip().split("\n", 1)[0].strip()
    title, _, author = first.partition("@")
    return title.strip(), author.strip()


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        articles = json.load(f)
    logger.info("Loaded %d articles from %s", len(articles), json_path.name)

    now = datetime.now(timezone.utc)
    for article in articles:
        text = normalize(article["閩"].strip())
        if not text:
            continue
        number = article["編號"]
        zh = normalize(article["國"].strip())
        title, author = _title_and_author(zh)
        yield Document(
            id=f"{source.source_id}:{number}",
            text=text,
            metadata=DocumentMetadata.from_source(
                source,
                format="txt",
                collected_at=now,
                script=Script.HANLO,
                author=author,
                title=title,
                tags=TAGS,
                parallel_zh=zh,
            ),
            provenance=Provenance(
                raw_path=f"{json_path.name}#編號={number}",
                extractor=EXTRACTOR_VERSION,
                processor=PROCESSOR_VERSION,
                content_hash=content_hash(text),
            ),
        )
