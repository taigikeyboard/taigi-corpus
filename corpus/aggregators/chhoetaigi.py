"""Shared ingester for ChhoeTaigi-format dictionary CSVs.

ChhoeTaigi (https://github.com/ChhoeTaigi/ChhoeTaigiDatabase) bundles ~9
Taiwanese dictionaries into per-dict CSVs with shared column conventions
(PojUnicode, HanLoTaibunPoj, HoaBun, KaisoehHanLoPoj, LekuHanLoPoj, ...).
Each dictionary has its own license and original author, so they live as
separate `sources/chhoetaigi_*/` folders that share this helper.

Path resolution: looks at $CHHOETAIGI_DB_PATH first, then falls back to a
sibling clone at `<repo-root>/../ChhoeTaigiDatabase/ChhoeTaigiDatabase/`.

Each source's ingest.py is just a config call:

    from corpus.aggregators.chhoetaigi import make_ingester
    from corpus.schema import Script

    ingest = make_ingester(
        csv_filename="ChhoeTaigi_TaihoaSoanntengTuichiautian.csv",
        headword_fields=["HanLoTaibunPoj", "PojUnicode"],
        body_fields=[("華文", "HoaBun")],
        script=Script.HANLO,
    )
"""

import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata

PROCESSOR_VERSION = "corpus.aggregators.chhoetaigi@v1"


def _find_csv(filename: str) -> Path:
    env = os.environ.get("CHHOETAIGI_DB_PATH")
    if env:
        base = Path(env)
    else:
        repo_root = Path(__file__).resolve().parents[2]
        base = repo_root.parent / "ChhoeTaigiDatabase" / "ChhoeTaigiDatabase"
    csv_path = base / filename
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Cannot find {filename}. Clone ChhoeTaigiDatabase as a sibling "
            f"repo, or set $CHHOETAIGI_DB_PATH to the directory that contains "
            f"the CSV files. Tried: {csv_path}"
        )
    return csv_path


def _compose_entry(
    row: dict,
    headword_fields: list[str],
    body_fields: list[tuple[str, str]],
) -> str:
    """Pick first non-empty value among `headword_fields` as headword, then
    append `{label}: {value}` lines for each non-empty `body_fields` entry."""
    headword = ""
    for field in headword_fields:
        value = (row.get(field) or "").strip()
        if value:
            headword = value
            break
    if not headword:
        return ""
    lines = [headword]
    for label, field in body_fields:
        value = (row.get(field) or "").strip()
        if value:
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


def make_ingester(
    *,
    csv_filename: str,
    headword_fields: list[str],
    body_fields: list[tuple[str, str]],
    script: Script = Script.HANLO,
    publication_date: str = "",
    extra_tags: list[str] | None = None,
) -> Callable[[SourceMetadata, Path], Iterator[Document]]:
    """Build an `ingest(source, source_dir)` generator for one ChhoeTaigi CSV."""
    extra_tags = extra_tags or []

    def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
        csv_path = _find_csv(csv_filename)
        now = datetime.now(timezone.utc)
        extractor = f"sources.{source.source_id}.ingest@v1"

        with open(csv_path, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                text = normalize(_compose_entry(row, headword_fields, body_fields))
                if not text:
                    continue

                word_id = (row.get("DictWordID") or "").strip() or "noid"

                yield Document(
                    id=f"{source.source_id}:{word_id}",
                    text=text,
                    metadata=DocumentMetadata.from_source(
                        source,
                        format="csv",
                        collected_at=now,
                        script=script,
                        publication_date=publication_date,
                        tags=["dictionary", *extra_tags],
                    ),
                    provenance=Provenance(
                        raw_path=f"{csv_filename}#row={word_id}",
                        extractor=extractor,
                        processor=PROCESSOR_VERSION,
                        content_hash=content_hash(text),
                    ),
                )

    return ingest
