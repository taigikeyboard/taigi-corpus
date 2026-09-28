"""台語文拍字練習 articles — modern Taiwanese prose and poems.

`mapped` articles have line-aligned `hanji` / `tailo` texts: text = Han,
metadata.parallel_poj = Tâi-lô. `single` articles have one `content` text,
whose script (Han, Han-Lo or Tâi-lô) is inferred from its characters.
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata
from corpus.scrapers.taigi_typing import scrape_and_save

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "sources.taigi_typing.ingest@v1"
PROCESSOR_VERSION = "corpus.scrapers.taigi_typing@v1"
_HAN = re.compile(r"[㐀-鿿\U00020000-\U0003134f]")
_LATIN = re.compile(r"[A-Za-z]")


def _script_of(text: str) -> Script:
    han = len(_HAN.findall(text))
    latin = len(_LATIN.findall(text))
    if han == 0:
        return Script.LO
    return Script.HANLO if latin > 0 else Script.HAN


def _aligned(text: str) -> str:
    """Normalize line by line so hanji / tailo keep one line per verse."""
    return "\n".join(normalize(line) for line in text.strip().split("\n"))


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        articles = json.load(f)
    logger.info("Loaded %d articles from %s", len(articles), json_path.name)

    now = datetime.now(timezone.utc)
    for article in articles:
        if article["type"] == "mapped":
            text = _aligned(article["hanji"])
            parallel_poj = _aligned(article["tailo"])
            script = Script.HAN
            tags = ["type:mapped", "script:tl"]
        else:
            text = normalize(article["content"])
            parallel_poj = ""
            script = _script_of(text)
            tags = ["type:single"]
        if not text.strip():
            continue
        tags += [f"topic:{t}" for t in article.get("tags") or []]
        article_id = str(article["id"])
        yield Document(
            id=f"{source.source_id}:{article_id}",
            text=text,
            metadata=DocumentMetadata.from_source(
                source,
                format="js",
                collected_at=now,
                script=script,
                original_url=article.get("url") or "",
                author=(article.get("source") or "").strip(),
                title=(article.get("title") or "").strip(),
                tags=tags,
                parallel_poj=parallel_poj,
            ),
            provenance=Provenance(
                raw_path=f"{json_path.name}#id={article_id}",
                extractor=EXTRACTOR_VERSION,
                processor=PROCESSOR_VERSION,
                content_hash=content_hash(text),
            ),
        )
