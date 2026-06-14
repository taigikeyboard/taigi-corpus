"""Export a filtered, training-ready JSONL view from the per-source corpus.

Selects sources by genre / license_category / script (via the manifest) and
concatenates their documents into one file. The full corpus stays per-source
(never merged in git); an export is an on-demand local view written under the
gitignored data/export/, so a future trainer runs one command to get exactly
the subset it is licensed to use.
"""

import json
import logging
from pathlib import Path

from corpus.manifest import build_manifest

logger = logging.getLogger(__name__)


def export(
    normalized_dir: Path,
    sources_dir: Path,
    output_path: Path,
    *,
    genres: set[str] | None = None,
    license_categories: set[str] | None = None,
    scripts: set[str] | None = None,
    text_only: bool = False,
) -> dict:
    """Concatenate documents from sources matching all given filters into one JSONL.

    A None filter matches everything. `scripts` also filters individual documents
    (a source like ungian_guliau_supin mixes scripts). `text_only` projects each
    record to {id, source_id, text}.
    """
    resolved_out = output_path.resolve()
    if resolved_out == normalized_dir.resolve() or normalized_dir.resolve() in resolved_out.parents:
        raise ValueError(
            f"Refusing to write export inside {normalized_dir} (would clobber source files). "
            f"Pick an -o path outside data/normalized/."
        )

    manifest = build_manifest(normalized_dir, sources_dir)
    selected = [
        row
        for row in manifest["sources"]
        if (genres is None or row["genre"] in genres)
        and (license_categories is None or row["license_category"] in license_categories)
        and (scripts is None or set(row["scripts"]) & scripts)
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc_count = 0
    with open(output_path, "w", encoding="utf-8") as out:
        for row in selected:
            with open(normalized_dir / row["file_name"], encoding="utf-8") as f:
                for line in f:
                    if scripts or text_only:
                        doc = json.loads(line)
                        if scripts and doc["metadata"]["script"] not in scripts:
                            continue
                        if text_only:
                            line = (
                                json.dumps(
                                    {
                                        "id": doc["id"],
                                        "source_id": doc["metadata"]["source_id"],
                                        "text": doc["text"],
                                    },
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )
                    out.write(line)
                    doc_count += 1

    return {
        "output": str(output_path),
        "doc_count": doc_count,
        "sources": [row["source_id"] for row in selected],
        "license_categories": sorted({row["license_category"] for row in selected}),
    }
