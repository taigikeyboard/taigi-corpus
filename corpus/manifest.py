"""Machine-readable manifest of the normalized corpus for downstream selection.

One row per `data/normalized/<id>.jsonl`: genre + license classification,
doc/char counts, per-script counts, parallel-field coverage, file size + sha256.
Lets consumers pick sources (by genre, license_category, license_restrictions,
or script) without scanning the full corpus. Built from the JSONL itself, so an
orphan file with no `sources/<id>/` folder still appears (genre=unknown).
"""

import hashlib
import json
import logging
from pathlib import Path

from corpus.pipeline import load_source
from corpus.schema import Genre

logger = logging.getLogger(__name__)

MANIFEST_SCHEMA_VERSION = 1


def license_category(license_id: str) -> str:
    """Single headline training-usability bucket. Precedence: NC > ND > SA > permissive.

    A single label hides secondary obligations (CC-BY-NC-SA -> non_commercial only);
    use license_restrictions() for the full set.
    """
    lic = license_id.strip().upper()
    if not lic or lic == "UNKNOWN":
        return "unknown"
    if "NC" in lic:
        return "non_commercial"
    if "ND" in lic:
        return "no_derivatives"
    if "SA" in lic:
        return "share_alike"
    return "permissive"


def license_restrictions(license_id: str) -> list[str]:
    """Every obligation the headline category would hide (e.g. NC-SA = both)."""
    lic = license_id.strip().upper()
    if not lic or lic == "UNKNOWN":
        return ["unknown"]
    out = []
    if "NC" in lic:
        out.append("non_commercial")
    if "ND" in lic:
        out.append("no_derivatives")
    if "SA" in lic:
        out.append("share_alike")
    if "BY" in lic or lic == "MIT":
        out.append("attribution")
    return out


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _genre_for(source_id: str, sources_dir: Path) -> str:
    """genre from sources/<id>/source.yaml; 'unknown' if no source folder (orphan)."""
    source_dir = sources_dir / source_id
    if not (source_dir / "source.yaml").exists():
        return Genre.UNKNOWN.value
    return load_source(source_dir).genre.value


def summarize(jsonl_path: Path, sources_dir: Path) -> dict:
    source_id = jsonl_path.stem
    doc_count = 0
    char_count = 0
    poj = 0
    zh = 0
    scripts: dict[str, int] = {}
    first_meta: dict = {}
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            md = doc["metadata"]
            if not first_meta:
                first_meta = md
            doc_count += 1
            char_count += len(doc.get("text", ""))
            scripts[md["script"]] = scripts.get(md["script"], 0) + 1
            if md.get("parallel_poj", "").strip():
                poj += 1
            if md.get("parallel_zh", "").strip():
                zh += 1

    license_id = first_meta.get("license", "unknown")

    def pct(n: int) -> float:
        return round(100 * n / doc_count, 1) if doc_count else 0.0

    return {
        "source_id": source_id,
        "source_name": first_meta.get("source_name", ""),
        "source_url": first_meta.get("source_url", ""),
        "genre": _genre_for(source_id, sources_dir),
        "license": license_id,
        "license_category": license_category(license_id),
        "license_restrictions": license_restrictions(license_id),
        "license_notes": first_meta.get("license_notes", ""),
        "file_name": jsonl_path.name,
        "scripts": scripts,
        "doc_count": doc_count,
        "char_count": char_count,
        "parallel_poj_count": poj,
        "parallel_poj_pct": pct(poj),
        "parallel_zh_count": zh,
        "parallel_zh_pct": pct(zh),
        "size_bytes": jsonl_path.stat().st_size,
        "file_sha256": _file_sha256(jsonl_path),
    }


def build_manifest(normalized_dir: Path, sources_dir: Path) -> dict:
    rows = [summarize(p, sources_dir) for p in sorted(normalized_dir.glob("*.jsonl"))]

    docs_by_genre: dict[str, int] = {}
    docs_by_license_category: dict[str, int] = {}
    for r in rows:
        docs_by_genre[r["genre"]] = docs_by_genre.get(r["genre"], 0) + r["doc_count"]
        cat = r["license_category"]
        docs_by_license_category[cat] = docs_by_license_category.get(cat, 0) + r["doc_count"]

    totals = {
        "source_count": len(rows),
        "doc_count": sum(r["doc_count"] for r in rows),
        "char_count": sum(r["char_count"] for r in rows),
        "size_bytes": sum(r["size_bytes"] for r in rows),
        "docs_by_genre": docs_by_genre,
        "docs_by_license_category": docs_by_license_category,
    }
    return {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "totals": totals,
        "sources": rows,
    }
