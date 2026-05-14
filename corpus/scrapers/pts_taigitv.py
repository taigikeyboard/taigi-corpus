"""Scraper for 公視台語台 新詞辭典 (taigitv.org.tw/taigi-words).

Ported from taigikeyboard/kemdict-data-pts-taigitv/scraper.ts. HTML
scraping with BeautifulSoup. Page count from `.pagination`, words from
`.doc-con .s4-btng > * .btngaa`, IDs from URL trailing digits.
"""

import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.taigitv.org.tw/taigi-words"
FETCH_DELAY = 0.5
USER_AGENT = "taigi-corpus scraper (https://github.com/siansiansu/taigi-corpus)"

_TRAILING_ID_RE = re.compile(r"/(\d+)/?$")


def _fetch_page(client: httpx.Client, page: int) -> str:
    r = client.get(
        BASE_URL,
        params={"page": page},
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    r.raise_for_status()
    return r.text


def _id_from_href(href: str) -> int:
    if not href:
        return 0
    m = _TRAILING_ID_RE.search(href.strip())
    return int(m.group(1)) if m else 0


def _page_count(html: str) -> int:
    soup = BeautifulSoup(html, "lxml")
    max_page = 1
    for a in soup.select(".pagination a.page-link"):
        href = a.get("href") or ""
        qs = parse_qs(urlparse(href).query)
        val = qs.get("page", [None])[0]
        if val and val.isdigit():
            n = int(val)
            if n > max_page:
                max_page = n
    return max_page


def _scrape_one_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    container = soup.select_one(".doc-con .s4-btng")
    if container is None:
        return []
    words: list[dict] = []
    for word_el in container.find_all(recursive=False):
        inner = word_el.select_one(".btngaa")
        if inner is None:
            continue
        title_a = inner.select_one("div.h3 a")
        if title_a is None:
            continue

        word_id = _id_from_href(title_a.get("href", ""))
        title = title_a.get_text(strip=True)

        pn = [el.get_text(strip=True) for el in inner.select("div p.eng span")]
        pn = [p for p in pn if p]

        zh_el = inner.select_one("div.row > div > span")
        zh = zh_el.get_text(strip=True) if zh_el else ""

        tags: list[dict] = []
        for tag_a in inner.select("div.pop-tag a"):
            tag_id = _id_from_href(tag_a.get("href", ""))
            tag_title = tag_a.get_text(strip=True).lstrip("#")
            if tag_title:
                tags.append({"id": tag_id, "title": tag_title})

        words.append(
            {"id": word_id, "title": title, "pn": pn, "zh": zh, "tags": tags}
        )
    return words


def scrape() -> list[dict]:
    """Walk all pages of taigitv.org.tw/taigi-words. Returns word list
    deduped by id and sorted by id."""
    by_id: dict[int, dict] = {}
    with httpx.Client(follow_redirects=True) as client:
        first_html = _fetch_page(client, 1)
        total = _page_count(first_html)
        logger.info("pts_taigitv: total pages = %d", total)
        for w in _scrape_one_page(first_html):
            by_id[w["id"]] = w
        logger.info("  page 1/%d (%d words so far)", total, len(by_id))

        for p in range(2, total + 1):
            time.sleep(FETCH_DELAY)
            html = _fetch_page(client, p)
            for w in _scrape_one_page(html):
                by_id[w["id"]] = w
            logger.info("  page %d/%d (%d words so far)", p, total, len(by_id))

    for w in by_id.values():
        w["tags"].sort(key=lambda t: t["id"])
    return sorted(by_id.values(), key=lambda w: w["id"])


def scrape_and_save(cache_dir: Path) -> Path:
    """Always hit taigitv.org.tw live; save as `scrape-<timestamp>.json` in
    cache_dir; remove any older scrape files so only the latest remains."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    words = scrape()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    new_path = cache_dir / f"scrape-{stamp}.json"
    new_path.write_text(
        json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    for f in cache_dir.glob("scrape-*.json"):
        if f != new_path:
            f.unlink()
    logger.info("Saved %d words → %s", len(words), new_path.name)
    return new_path
