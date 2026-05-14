"""TSBP (台文通訊BONG報) ingester — incremental.

Each Blogger feed entry is cached as `raw/entries/<slug>.json` (one file per
post). The filesystem is the state: presence of the file means we've already
seen that entry. On each run we walk the feed from `start-index=1` and stop
as soon as a full page contains zero new entries — which means a normal
incremental run only hits 1 page if nothing has changed.

First run after the original implementation: legacy `raw/feed_page_*.json`
files are split into per-entry files (one-time migration). Legacy page files
are left in place; they can be deleted manually.

Suitable for cron / launchd — idempotent and cheap when up to date.
"""

import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import httpx
from bs4 import BeautifulSoup

from corpus.normalize import normalize
from corpus.parsers.html import parse_html
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata

logger = logging.getLogger(__name__)

FEED_URL = "https://tsbp.tgb.org.tw/feeds/posts/default"
MAX_PER_PAGE = 150
FETCH_DELAY = 1.5
ISSUE_LABEL_RE = re.compile(r"台文通訊BONG報(\d+)期")
EXTRACTOR_VERSION = "sources.tsbp.ingest@v2"
PROCESSOR_VERSION = "corpus.parsers.html@v1"


def _extract_url(entry: dict) -> str:
    for link in entry.get("link", []):
        if link.get("rel") == "alternate":
            return link.get("href", "")
    return ""


def _slug(entry: dict) -> str:
    url = _extract_url(entry)
    if url:
        parts = url.rstrip("/").split("/")
        slug = parts[-1].replace(".html", "") if parts else ""
        year_month = "-".join(parts[-3:-1]) if len(parts) >= 3 else ""
        return f"{year_month}_{slug}" if year_month else slug
    entry_id = entry.get("id", {}).get("$t", "unknown")
    return entry_id.split(".")[-1].replace("/", "_")


def _issue_number(entry: dict) -> int | None:
    for cat in entry.get("category", []):
        m = ISSUE_LABEL_RE.search(cat.get("term", ""))
        if m:
            return int(m.group(1))
    return None


def _author(entry: dict) -> str:
    authors = entry.get("author") or []
    if not authors:
        return ""
    return authors[0].get("name", {}).get("$t", "")


def _strip_source_noise(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for sel in ["div.donation-section", "div.tg-images"]:
        for tag in soup.select(sel):
            tag.decompose()
    return str(soup)


def _save_entry(entry: dict, entries_dir: Path) -> bool:
    """Write entry to raw/entries/<slug>.json. Returns True if newly written."""
    slug = _slug(entry)
    path = entries_dir / f"{slug}.json"
    if path.exists():
        return False
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def _migrate_legacy_pages(raw_dir: Path, entries_dir: Path) -> int:
    """If legacy raw/feed_page_*.json files exist but raw/entries/ is empty,
    split each page into per-entry files. Returns count migrated."""
    if entries_dir.exists() and any(entries_dir.iterdir()):
        return 0
    legacy_pages = sorted(raw_dir.glob("feed_page_*.json"))
    if not legacy_pages:
        return 0
    entries_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for page_path in legacy_pages:
        with open(page_path, encoding="utf-8") as f:
            data = json.load(f)
        for entry in data.get("feed", {}).get("entry", []) or []:
            if _save_entry(entry, entries_dir):
                count += 1
    logger.info("Migrated %d entries from legacy page files", count)
    return count


def _fetch_incremental(entries_dir: Path) -> tuple[int, int]:
    """Walk feed pages until a full page contains zero new entries.
    Returns (new_count, total_pages_fetched)."""
    entries_dir.mkdir(parents=True, exist_ok=True)
    start_index = 1
    pages_fetched = 0
    total_new = 0

    with httpx.Client(timeout=60, follow_redirects=True) as client:
        while True:
            pages_fetched += 1
            params = {
                "alt": "json",
                "max-results": MAX_PER_PAGE,
                "start-index": start_index,
            }
            logger.info("Fetching start_index=%d", start_index)
            resp = client.get(FEED_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            page_entries = data.get("feed", {}).get("entry", []) or []
            if not page_entries:
                logger.info("  empty page, stopping")
                break

            new_on_page = sum(1 for e in page_entries if _save_entry(e, entries_dir))
            total_new += new_on_page
            logger.info("  %d/%d new on page", new_on_page, len(page_entries))

            if new_on_page == 0:
                logger.info("Page fully cached; incremental cut-off reached")
                break

            if len(page_entries) < MAX_PER_PAGE:
                break
            start_index += len(page_entries)
            time.sleep(FETCH_DELAY)

    return total_new, pages_fetched


def _iter_cached_entries(entries_dir: Path) -> Iterator[dict]:
    for path in sorted(entries_dir.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            yield json.load(f)


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    raw_dir = source_dir / "raw"
    entries_dir = raw_dir / "entries"

    migrated = _migrate_legacy_pages(raw_dir, entries_dir)
    new_count, _ = _fetch_incremental(entries_dir)
    total_cached = sum(1 for _ in entries_dir.glob("*.json"))
    logger.info(
        "TSBP cache: %d total entries (+%d new this run, %d migrated)",
        total_cached, new_count, migrated,
    )

    now = datetime.now(timezone.utc)
    repo_root = source_dir.parent.parent

    for entry in _iter_cached_entries(entries_dir):
        content_html = entry.get("content", {}).get("$t", "")
        if not content_html:
            continue

        cleaned_html = _strip_source_noise(content_html)
        text_raw = parse_html(cleaned_html, container_selector="div.tg-content")
        if not text_raw.strip():
            text_raw = parse_html(cleaned_html)
        text = normalize(text_raw)
        if not text:
            continue

        slug = _slug(entry)
        title = entry.get("title", {}).get("$t", "")
        published = entry.get("published", {}).get("$t", "")
        url = _extract_url(entry)
        issue = _issue_number(entry)

        tags = [c.get("term", "") for c in entry.get("category", []) if c.get("term")]
        if issue is not None and f"issue:{issue}" not in tags:
            tags.append(f"issue:{issue}")

        meta = DocumentMetadata.from_source(
            source,
            format="html",
            collected_at=now,
            script=Script.HANLO,
            original_url=url,
            publication_date=published[:10] if published else "",
            author=_author(entry),
            title=title,
            tags=tags,
        )

        prov = Provenance(
            raw_path=str((entries_dir / f"{slug}.json").relative_to(repo_root)),
            extractor=EXTRACTOR_VERSION,
            processor=PROCESSOR_VERSION,
            content_hash=content_hash(text),
        )

        yield Document(
            id=f"{source.source_id}:{slug}",
            text=text,
            metadata=meta,
            provenance=prov,
        )
