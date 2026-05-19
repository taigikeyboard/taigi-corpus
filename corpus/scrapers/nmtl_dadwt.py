"""Scraper for 台語文數位典藏資料庫 (Taiwanese-Corpus/nmtl_2006_dadwt).

Frozen archive from NMTL (National Museum of Taiwan Literature). The
upstream repo ships a pre-built `nmtl.json` (~24 MB) produced from the
project's SQL database; each entry has a `資料` field holding paragraph
pairs `[Han-Lo, POJ]` for the same article.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

RAW_URL = "https://raw.githubusercontent.com/Taiwanese-Corpus/nmtl_2006_dadwt/master/nmtl.json"
USER_AGENT = "taigi-corpus scraper (https://github.com/siansiansu/taigi-corpus)"

# `類` codes → Han genre labels (consistent with ungian_guliau_supin's HL labels)
GENRE_CODE_TO_HAN: dict[str, str] = {
    "SB": "散文",
    "KP": "劇本",
    "KS": "歌詩",
    "SS": "小說",
}

# `時代` codes → Han era labels
ERA_CODE_TO_HAN: dict[str, str] = {
    "C": "清領",
    "J": "日治",
    "K": "戰後",
}


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
