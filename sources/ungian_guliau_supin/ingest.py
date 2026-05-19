"""楊允言 2005 NSC 計畫 — 5,208 篇台文文章 (HL 漢羅 + POJ 全羅，數字調).

Each scraper entry has: subset (HL/POJ), csv_id, luipiat (genre), chokchia
(author), piautoe (title), tongmia (filename stem), nitai (year), rel_path,
text.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from urllib.parse import quote

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata
from corpus.scrapers.ungian_guliau_supin import POJ_GENRE_TO_HAN, scrape_and_save

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "sources.ungian_guliau_supin.ingest@v1"
PROCESSOR_VERSION = "corpus.scrapers.ungian_guliau_supin@v1"

REPO_BLOB_URL = (
    "https://github.com/Taiwanese-Corpus/Ungian_2005_guliau-supin/blob/master/"
)


def _genre_han(subset: str, luipiat: str) -> str:
    if subset == "POJ":
        return POJ_GENRE_TO_HAN.get(luipiat, luipiat)
    return luipiat


def _build_tags(subset: str, genre_han: str) -> list[str]:
    tags = [f"subset:{subset}"]
    if genre_han:
        tags.append(f"category:{genre_han}")
    if subset == "POJ":
        tags.append("script:poj-numerical")
    return tags


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        entries = json.load(f)
    logger.info("Loaded %d entries from %s", len(entries), json_path.name)

    now = datetime.now(timezone.utc)

    for entry in entries:
        text = normalize((entry.get("text") or "").strip())
        if not text:
            continue

        subset = entry["subset"]
        csv_id = (entry.get("csv_id") or "noid").strip() or "noid"
        genre_han = _genre_han(subset, (entry.get("luipiat") or "").strip())
        script = Script.HANLO if subset == "HL" else Script.LO

        yield Document(
            id=f"{source.source_id}:{subset}:{csv_id}",
            text=text,
            metadata=DocumentMetadata.from_source(
                source,
                format="text",
                collected_at=now,
                script=script,
                original_url=REPO_BLOB_URL + quote(entry["rel_path"], safe="/"),
                publication_date=(entry.get("nitai") or "").strip(),
                author=(entry.get("chokchia") or "").strip(),
                title=(entry.get("piautoe") or "").strip(),
                tags=_build_tags(subset, genre_han),
            ),
            provenance=Provenance(
                raw_path=f"{json_path.name}#subset={subset}&id={csv_id}",
                extractor=EXTRACTOR_VERSION,
                processor=PROCESSOR_VERSION,
                content_hash=content_hash(text),
            ),
        )
