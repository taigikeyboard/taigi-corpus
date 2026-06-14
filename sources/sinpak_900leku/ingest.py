"""900例句 — example sentences from the 新北市 2015 字音字形 workshop.

minnan900.json is a dict keyed by 編號; each value carries 例句漢字 (Han text),
例句臺羅 (Tâi-lô diacritic), and the 詞條漢字 headword the sentence illustrates.
One Document per 例句: text = 例句漢字, metadata.parallel_poj = 例句臺羅.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata
from corpus.scrapers.sinpak_900leku import scrape_and_save

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "sources.sinpak_900leku.ingest@v1"
PROCESSOR_VERSION = "corpus.scrapers.sinpak_900leku@v1"
PUBLICATION_DATE = "2015"


def _starts_with_han(text: str) -> bool:
    """True if the first non-space character is a CJK Han ideograph."""
    stripped = text.lstrip()
    if not stripped:
        return False
    cp = ord(stripped[0])
    return 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF or 0x20000 <= cp <= 0x2FFFF


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        entries = json.load(f)
    logger.info("Loaded %d entries from %s", len(entries), json_path.name)

    now = datetime.now(timezone.utc)
    emitted = 0
    skipped_corrupt = 0
    for key in sorted(entries):
        entry = entries[key]
        text = normalize((entry.get("例句漢字") or "").strip())
        if not text:
            continue

        poj_raw = (entry.get("例句臺羅") or "").strip()
        # Upstream pdftotext extraction split ~67 sentences: the Han tail leaked
        # into the start of 例句臺羅, leaving 例句漢字 truncated and the romanization
        # itself dropping characters. Skip these unrecoverable rows rather than
        # ship truncated text and polluted parallel_poj.
        if _starts_with_han(poj_raw):
            skipped_corrupt += 1
            continue

        parallel_poj = normalize(poj_raw)
        serial = (entry.get("編號") or key).strip() or key

        emitted += 1
        yield Document(
            id=f"{source.source_id}:{serial}",
            text=text,
            metadata=DocumentMetadata.from_source(
                source,
                format="json",
                collected_at=now,
                script=Script.HAN,
                publication_date=PUBLICATION_DATE,
                title=(entry.get("詞條漢字") or "").strip(),
                tags=["subset:900leku"],
                parallel_poj=parallel_poj,
            ),
            provenance=Provenance(
                raw_path=f"{json_path.name}#編號={serial}",
                extractor=EXTRACTOR_VERSION,
                processor=PROCESSOR_VERSION,
                content_hash=content_hash(text),
            ),
        )

    logger.info("Emitted %d documents (%d corrupt rows skipped)", emitted, skipped_corrupt)
