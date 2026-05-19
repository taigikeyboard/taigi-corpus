"""台灣白話字文獻館 — paragraph-aligned Han-Lo / POJ-diacritic articles
from late 19th- and 20th-century Taiwanese Presbyterian Church publications.

Each upstream entry has: pianho (id), 作者, 刊名, 卷期, 日期, 本次, 篇名,
頁數, hanlo (list of paragraphs in Han-Lo), tailo (list of paragraphs in
POJ-diacritic; the upstream field name is misleading).
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
from corpus.scrapers.khinhoan_pojbh import scrape_and_save

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "sources.khinhoan_pojbh.ingest@v1"
PROCESSOR_VERSION = "corpus.scrapers.khinhoan_pojbh@v1"

_DATE_TOKEN_RE = re.compile(r"^(\d{4})(?:/(\d{1,2}))?(?:/(\d{1,2}))?$")


def _normalize_date(raw: str) -> str:
    """Normalize upstream date strings like '1925/1' or '1962/2/15' to ISO
    (YYYY, YYYY-MM, YYYY-MM-DD). Falls back to the raw value if unparseable."""
    if not raw:
        return ""
    token = raw.strip().split()[0] if raw.strip() else ""
    m = _DATE_TOKEN_RE.match(token)
    if not m:
        return raw.strip()
    y, mo, d = m.groups()
    if d:
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    if mo:
        return f"{y}-{int(mo):02d}"
    return y


def _era_from_year(year_str: str) -> str:
    if not year_str or not year_str[:4].isdigit():
        return ""
    year = int(year_str[:4])
    if year < 1895:
        return "清領"
    if year < 1945:
        return "日治"
    return "戰後"


def _build_tags(journal: str, era: str, aligned: bool) -> list[str]:
    tags = ["subset:pojbh", "category:religious", "parallel:poj-diacritic"]
    tags.append("parallel-status:aligned" if aligned else "parallel-status:mismatched")
    if journal:
        tags.append(f"journal:{journal}")
    if era:
        tags.append(f"era:{era}")
    return tags


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        entries = json.load(f)
    logger.info("Loaded %d entries from %s", len(entries), json_path.name)

    now = datetime.now(timezone.utc)
    skipped_empty = 0
    aligned_n = 0
    mismatched_n = 0

    for entry in entries:
        hanlo_paras = [p for p in (entry.get("hanlo") or []) if isinstance(p, str)]
        tailo_paras = [p for p in (entry.get("tailo") or []) if isinstance(p, str)]

        text = normalize("\n".join(hanlo_paras).strip())
        parallel_poj = normalize("\n".join(tailo_paras).strip())
        if not text:
            skipped_empty += 1
            continue

        aligned = bool(parallel_poj) and len(hanlo_paras) == len(tailo_paras)
        if aligned:
            aligned_n += 1
        else:
            mismatched_n += 1

        pianho = str(entry.get("pianho") or "noid").strip() or "noid"
        pub_date = _normalize_date(entry.get("日期") or "")
        era = _era_from_year(pub_date)
        journal = (entry.get("刊名") or "").strip()

        yield Document(
            id=f"{source.source_id}:{pianho}",
            text=text,
            metadata=DocumentMetadata.from_source(
                source,
                format="json",
                collected_at=now,
                script=Script.HANLO,
                publication_date=pub_date,
                author=(entry.get("作者") or "").strip(),
                title=(entry.get("篇名") or "").strip(),
                tags=_build_tags(journal, era, aligned),
                parallel_poj=parallel_poj,
            ),
            provenance=Provenance(
                raw_path=f"{json_path.name}#pianho={pianho}",
                extractor=EXTRACTOR_VERSION,
                processor=PROCESSOR_VERSION,
                content_hash=content_hash(text),
            ),
        )

    logger.info("Skipped %d entries with no Han-Lo text", skipped_empty)
    logger.info("Aligned: %d, mismatched: %d", aligned_n, mismatched_n)
