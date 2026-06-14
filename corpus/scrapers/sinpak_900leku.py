"""Scraper for 900例句 (Taiwanese-Corpus/Sin1pak8tshi7_2015_900-le7ku3).

新北市 104 學年度閩南語字音字形 900 例句工作坊. The upstream repo ships a
maintained `minnan900.json`: a dict keyed by 編號, each value carrying
例句漢字, 例句臺羅 (Tâi-lô diacritic), 詞條漢字, 詞條臺羅.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

RAW_URL = (
    "https://raw.githubusercontent.com/Taiwanese-Corpus/"
    "Sin1pak8tshi7_2015_900-le7ku3/master/minnan900.json"
)
USER_AGENT = "taigi-corpus scraper (https://github.com/siansiansu/taigi-corpus)"


def scrape() -> dict:
    logger.info("Fetching %s", RAW_URL)
    with httpx.Client(follow_redirects=True) as client:
        r = client.get(RAW_URL, headers={"User-Agent": USER_AGENT}, timeout=120)
        r.raise_for_status()
        entries = r.json()
    if not isinstance(entries, dict):
        raise ValueError(f"Expected JSON object, got {type(entries).__name__}")
    logger.info("Fetched %d entries", len(entries))
    return entries


def scrape_and_save(cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    entries = scrape()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    new_path = cache_dir / f"scrape-{stamp}.json"
    new_path.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in cache_dir.glob("scrape-*.json"):
        if f != new_path:
            f.unlink()
    logger.info("Saved %d entries → %s", len(entries), new_path.name)
    return new_path
