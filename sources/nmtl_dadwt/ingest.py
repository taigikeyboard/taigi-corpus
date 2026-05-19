"""NMTL 台語文數位典藏資料庫 — 2,167 paragraph-aligned Han-Lo / POJ articles.

Each upstream entry has: 流水號, 年, 時代 (C/J/K), 類 (SB/KP/KS/SS), 類二,
檔案名, 漢羅名, 漢羅標, 全羅名, 全羅標, 資料 (list of [Han-Lo, POJ] paragraph
pairs).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata
from corpus.scrapers.nmtl_dadwt import (
    ERA_CODE_TO_HAN,
    GENRE_CODE_TO_HAN,
    scrape_and_save,
)

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "sources.nmtl_dadwt.ingest@v1"
PROCESSOR_VERSION = "corpus.scrapers.nmtl_dadwt@v1"


def _build_tags(genre_han: str, era_han: str) -> list[str]:
    tags = ["subset:dadwt"]
    if genre_han:
        tags.append(f"category:{genre_han}")
    if era_han:
        tags.append(f"era:{era_han}")
    return tags


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    json_path = scrape_and_save(source_dir / "raw")
    with open(json_path, encoding="utf-8") as f:
        entries = json.load(f)
    logger.info("Loaded %d entries from %s", len(entries), json_path.name)

    now = datetime.now(timezone.utc)

    for entry in entries:
        pairs = entry.get("資料") or []
        if not pairs:
            continue

        hanlo_paras = [(p[0] if len(p) > 0 else "") for p in pairs]
        poj_paras = [(p[1] if len(p) > 1 else "") for p in pairs]

        text = normalize("\n".join(hanlo_paras).strip())
        parallel_poj = normalize("\n".join(poj_paras).strip())
        if not text:
            continue

        serial = str(entry.get("流水號") or "noid").strip() or "noid"
        genre_han = GENRE_CODE_TO_HAN.get((entry.get("類") or "").strip(), "")
        era_han = ERA_CODE_TO_HAN.get((entry.get("時代") or "").strip(), "")

        yield Document(
            id=f"{source.source_id}:{serial}",
            text=text,
            metadata=DocumentMetadata.from_source(
                source,
                format="json",
                collected_at=now,
                script=Script.HANLO,
                publication_date=(entry.get("年") or "").strip(),
                author=(entry.get("漢羅名") or "").strip(),
                title=(entry.get("漢羅標") or "").strip(),
                tags=_build_tags(genre_han, era_han),
                parallel_poj=parallel_poj,
            ),
            provenance=Provenance(
                raw_path=f"{json_path.name}#流水號={serial}",
                extractor=EXTRACTOR_VERSION,
                processor=PROCESSOR_VERSION,
                content_hash=content_hash(text),
            ),
        )
