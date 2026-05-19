"""Scraper for 台灣白話字文獻館 (Taiwanese-Corpus/Khin-hoan_2010_pojbh).

Frozen archive of NTNU Graduate Institute of Taiwan Culture, Languages
and Literature's POJ literature database. The upstream repo ships a
pre-built `pojbh.json` (~22 MB); each entry has parallel `hanlo` and
`tailo` paragraph lists (the `tailo` field is actually POJ-diacritic,
not Tâi-lô) plus bibliographic metadata.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

RAW_URL = "https://raw.githubusercontent.com/Taiwanese-Corpus/Khin-hoan_2010_pojbh/master/pojbh.json"
USER_AGENT = "taigi-corpus scraper (https://github.com/siansiansu/taigi-corpus)"


def scrape() -> list[dict]:
    logger.info("Fetching %s", RAW_URL)
    with httpx.Client(follow_redirects=True) as client:
        r = client.get(RAW_URL, headers={"User-Agent": USER_AGENT}, timeout=180)
        r.raise_for_status()
        entries = r.json()
    if not isinstance(entries, list):
        raise ValueError(f"Expected JSON list, got {type(entries).__name__}")
    logger.info("Fetched %d entries", len(entries))
    return entries


def scrape_and_save(cache_dir: Path) -> Path:
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
