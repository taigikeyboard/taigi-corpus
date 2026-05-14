"""Scraper for 台語工藝詞庫 (kanggesu.ntcri.gov.tw).

Ported from taigikeyboard/kanggesu-data/scraper.ts. Uses the site's
POST JSON API; paginate via page.current; dedupe + sort by entriesBaseId.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

API_URL = "https://kanggesu.ntcri.gov.tw/NTCRI_TaigiWebSite/api/EntriesBase/List"
USER_AGENT = "taigi-corpus scraper (https://github.com/siansiansu/taigi-corpus)"

REQUEST_BODY: dict = {
    "mainType": ["A", "B", "C", "F", "G", "L", "M", "O", "P", "S", "W"],
    "childType": [1, 2, 3, 4, 5, 6, 7],
    "keyword": "",
    "page": {"current": 1, "per": 100, "orderBy": "CreateTime", "orderByAsc": True},
    "relatedpage": {"current": 1, "per": 3, "orderBy": "", "orderByAsc": True},
}


def _fetch_page(client: httpx.Client, page: int) -> dict:
    body = dict(REQUEST_BODY)
    body["page"] = {**REQUEST_BODY["page"], "current": page}
    r = client.post(
        API_URL,
        json=body,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def scrape() -> list[dict]:
    """Fetch every page, dedupe by entriesBaseId, return sorted list."""
    entries: dict[str, dict] = {}
    with httpx.Client(follow_redirects=True) as client:
        first = _fetch_page(client, 1)
        total = int(first.get("page", {}).get("count", 1))
        logger.info("kanggesu: total pages = %d", total)
        for e in first.get("list", []) or []:
            entries[e["entriesBaseId"]] = e
        logger.info("  page 1/%d (%d entries so far)", total, len(entries))

        for p in range(2, total + 1):
            data = _fetch_page(client, p)
            for e in data.get("list", []) or []:
                entries[e["entriesBaseId"]] = e
            logger.info("  page %d/%d (%d entries so far)", p, total, len(entries))

    return sorted(entries.values(), key=lambda e: e["entriesBaseId"])


def scrape_and_save(cache_dir: Path) -> Path:
    """Always hit upstream live; save as `scrape-<date>.json` in cache_dir;
    remove any older scrape files so only the latest remains."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    entries = scrape()
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    new_path = cache_dir / f"scrape-{today}.json"
    new_path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    for f in cache_dir.glob("scrape-*.json"):
        if f != new_path:
            f.unlink()
    logger.info("Saved %d entries → %s", len(entries), new_path.name)
    return new_path
