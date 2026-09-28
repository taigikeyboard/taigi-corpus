"""新約臺語聖經 — three New Testament translations, verse-aligned Han-Lo / POJ.

One Document per chapter per translation. text = Han-Lo verses, one per line;
metadata.parallel_poj = diacritic POJ verses. The translation is carried in the
id prefix and a `translation:` tag so consumers can pick one.
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

REPO = "Taiwanese-Corpus/Pakhelke-1916_KoTan-1975_hiantaiekpun-2008_taiwanese-bible"
EXTRACTOR_VERSION = "sources.taigi_bible_nt.ingest@v1"
PROCESSOR_VERSION = "corpus.scrapers.doc2json@v1"
TRANSLATION_YEAR = {
    "1916-Pakhekle": "1916",
    "1975-KoTanVersion": "1975",
    "2008-hiantaiekpun": "2008",
}


def _side(pairs: list[list[str]], index: int) -> str:
    """One normalized line per pair, so text and parallel_poj stay line-aligned."""
    return "\n".join(normalize(pair[index]).replace("\n", " ") for pair in pairs)


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(REPO, source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        works = json.load(f)
    logger.info("Loaded %d chapters from %s", len(works), json_path.name)

    now = datetime.now(timezone.utc)
    for work in works:
        chapter_id = work["來源檔"]
        version_dir, book_dir = chapter_id.split("/")[:2]
        translation = (work.get("文類") or "").strip()
        for piece in work.get("資料") or []:
            pairs = piece.get("段") or []
            text = _side(pairs, 0)
            if not text.strip():
                continue
            yield Document(
                id=f"{source.source_id}:{chapter_id}",
                text=text,
                metadata=DocumentMetadata.from_source(
                    source,
                    format="json",
                    collected_at=now,
                    script=Script.HANLO,
                    publication_date=TRANSLATION_YEAR.get(version_dir, ""),
                    title=(piece.get("篇名") or "").strip(),
                    tags=[f"translation:{translation}", f"book:{book_dir[3:]}", "script:poj"],
                    parallel_poj=_side(pairs, 1),
                ),
                provenance=Provenance(
                    raw_path=f"{json_path.name}#{chapter_id}",
                    extractor=EXTRACTOR_VERSION,
                    processor=PROCESSOR_VERSION,
                    content_hash=content_hash(text),
                ),
            )
