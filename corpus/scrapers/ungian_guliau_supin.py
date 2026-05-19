"""Scraper for 楊允言 2005 NSC 計畫 (Taiwanese-Corpus/Ungian_2005_guliau-supin).

Frozen academic dataset (last push 2018-09). Downloads the master.tar.gz
from GitHub, extracts the two CSV metadata files + all UTF-8 text files
under `轉換後資料/{HL,POJ}/`, joins them by filename stem, returns one
entry per CSV row that has a matching text file.
"""

import csv
import io
import json
import logging
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

TARBALL_URL = "https://github.com/Taiwanese-Corpus/Ungian_2005_guliau-supin/archive/refs/heads/master.tar.gz"
USER_AGENT = "taigi-corpus scraper (https://github.com/siansiansu/taigi-corpus)"

# POJ.csv uses romanized genre labels; HL.csv uses Han labels. Map the
# romanized side to Han so downstream code can filter `category:散文`
# across both subsets.
POJ_GENRE_TO_HAN: dict[str, str] = {
    "sanbun": "散文",
    "siosoat": "小說",
    "sinsi": "新詩",
    "toanki": "傳記",
    "poto": "報導",
    "phenglun": "評論",
    "chhiooe": "笑話",
    "phoe": "批",
    "kitha": "其它",
    "haksut": "學術",
    "kekpun": "劇本",
    "gina": "囡仔",
    "gugian": "寓言",
    "iankang": "演講",
    "binkanbunhak": "民間文學",
    "tuioe": "對話",
}


def _parse_tarball(tar_bytes: bytes) -> list[dict]:
    csv_rows: dict[str, list[dict]] = {"HL": [], "POJ": []}
    text_files: dict[tuple[str, str], tuple[str, str]] = {}

    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            parts = member.name.split("/", 1)
            if len(parts) < 2:
                continue
            rel = parts[1]

            if rel in ("轉換後資料/HL.csv", "轉換後資料/POJ.csv"):
                subset = "HL" if "HL" in rel else "POJ"
                f = tar.extractfile(member)
                if f is None:
                    continue
                text = f.read().decode("utf-8")
                csv_rows[subset] = list(csv.DictReader(io.StringIO(text)))
                logger.info("Loaded %s.csv: %d rows", subset, len(csv_rows[subset]))
                continue

            if not rel.endswith(".txt"):
                continue
            if rel.startswith("轉換後資料/HL/"):
                subset = "HL"
            elif rel.startswith("轉換後資料/POJ/"):
                subset = "POJ"
            else:
                continue

            f = tar.extractfile(member)
            if f is None:
                continue
            raw = f.read()
            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError:
                logger.warning("Skipping non-UTF8 file: %s", rel)
                continue
            text_files[(subset, Path(rel).stem)] = (rel, content)

    logger.info("Found %d HL .txt + %d POJ .txt files",
                sum(1 for k in text_files if k[0] == "HL"),
                sum(1 for k in text_files if k[0] == "POJ"))

    entries: list[dict] = []
    for subset in ("HL", "POJ"):
        matched = 0
        unmatched = 0
        for row in csv_rows[subset]:
            stem = (row.get("tongmia") or "").strip()
            if not stem:
                continue
            file_info = text_files.get((subset, stem))
            if file_info is None:
                unmatched += 1
                continue
            rel_path, text = file_info
            entries.append({
                "subset": subset,
                "csv_id": row.get("id", ""),
                "luipiat": row.get("luipiat", ""),
                "chokchia": row.get("chokchia", ""),
                "piautoe": row.get("piautoe", ""),
                "tongmia": stem,
                "nitai": row.get("nitai", ""),
                "rel_path": rel_path,
                "text": text,
            })
            matched += 1
        logger.info("%s: %d matched, %d CSV rows without file", subset, matched, unmatched)
    return entries


def scrape() -> list[dict]:
    """Fetch tarball, parse CSVs + text files, return joined entries."""
    logger.info("Fetching %s", TARBALL_URL)
    with httpx.Client(follow_redirects=True) as client:
        r = client.get(TARBALL_URL, headers={"User-Agent": USER_AGENT}, timeout=180)
        r.raise_for_status()
        tar_bytes = r.content
    logger.info("Downloaded %d bytes", len(tar_bytes))
    entries = _parse_tarball(tar_bytes)
    logger.info("Total entries: %d", len(entries))
    return entries


def scrape_and_save(cache_dir: Path) -> Path:
    """Always hit upstream live; save the parsed entries as
    `scrape-<timestamp>.json` in cache_dir; remove older scrape files."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    entries = scrape()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    new_path = cache_dir / f"scrape-{stamp}.json"
    new_path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    for f in cache_dir.glob("scrape-*.json"):
        if f != new_path:
            f.unlink()
    logger.info("Saved %d entries → %s", len(entries), new_path.name)
    return new_path
