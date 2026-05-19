"""Scraper for 台華平行新聞語料庫 (sih4sing5hong5/icorpus).

Upstream is a frozen Academia Sinica dataset (last push 2018-07) released
as a single `icorpus.json` (~8.6MB) in the GitHub repo. One HTTP GET per
build; no pagination. Each entry is a parallel article pair with keys
`台語` (numerical POJ), `華語` (Mandarin), `文號`, `日期`.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

RAW_URL = "https://raw.githubusercontent.com/sih4sing5hong5/icorpus/master/icorpus.json"
USER_AGENT = "taigi-corpus scraper (https://github.com/siansiansu/taigi-corpus)"


def scrape() -> list[dict]:
    """Fetch icorpus.json from the upstream GitHub repo."""
    logger.info("Fetching %s", RAW_URL)
    with httpx.Client(follow_redirects=True) as client:
        r = client.get(RAW_URL, headers={"User-Agent": USER_AGENT}, timeout=120)
        r.raise_for_status()
        entries = r.json()
    if not isinstance(entries, list):
        raise ValueError(f"Expected JSON list, got {type(entries).__name__}")
    logger.info("Fetched %d entries", len(entries))
    return entries


def scrape_and_save(cache_dir: Path) -> Path:
    """Always hit upstream live; save as `scrape-<timestamp>.json` in
    cache_dir; remove any older scrape files so only the latest remains."""
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
