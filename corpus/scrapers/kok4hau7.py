"""Scraper for 國校仔課本 (Taiwanese-Corpus/kok4hau7-kho3pun2).

Elementary-school Taiwanese textbooks from five publishers (翰林, 康軒, 真平,
安可, 巧兒). The upstream repo ships one JSON per volume under
`JSON格式資料/<出版者>/`; there is no combined file, so we fetch the repo
tarball and extract them in memory. Each volume has 資料 = list of 篇 (lessons),
each 篇 has 段 = list of [漢字, 台羅] line pairs.
"""

import io
import json
import logging
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

TARBALL_URL = (
    "https://codeload.github.com/Taiwanese-Corpus/kok4hau7-kho3pun2/tar.gz/refs/heads/master"
)
USER_AGENT = "taigi-corpus scraper (https://github.com/siansiansu/taigi-corpus)"
JSON_DIR_MARKER = "/JSON格式資料/"


def scrape() -> list[dict]:
    logger.info("Fetching %s", TARBALL_URL)
    with httpx.Client(follow_redirects=True) as client:
        r = client.get(TARBALL_URL, headers={"User-Agent": USER_AGENT}, timeout=180)
        r.raise_for_status()

    books: list[dict] = []
    with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tar:
        for member in tar:
            name = member.name
            if not member.isfile() or JSON_DIR_MARKER not in name or not name.endswith(".json"):
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            book = json.load(extracted)
            # Filename stem is unique across publishers (e.g. 翰林1, 康軒9, 巧兒09)
            # and gives a stable per-volume id.
            book["來源檔"] = Path(name).stem
            books.append(book)

    if not books:
        raise ValueError(f"No {JSON_DIR_MARKER.strip('/')}/*.json found in tarball")
    books.sort(key=lambda b: b["來源檔"])
    logger.info("Extracted %d volumes", len(books))
    return books


def scrape_and_save(cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    books = scrape()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    new_path = cache_dir / f"scrape-{stamp}.json"
    new_path.write_text(json.dumps(books, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in cache_dir.glob("scrape-*.json"):
        if f != new_path:
            f.unlink()
    logger.info("Saved %d volumes → %s", len(books), new_path.name)
    return new_path
