"""Scraper for Taiwanese-Corpus repos converted by KIPsupin_doc2yaml.

These repos (楊允言's collections) ship one JSON per work under `JSON格式資料/`,
converted from fixed-layout DOC tables. Each JSON has work-level fields
(作者, 出版年, 出版者, 文類, 書寫系統, 書名, 年級別) and 資料 = list of 篇, each with
篇名, optional per-篇 overrides of the same fields, and 段 = list of
[Han / Han-Lo line, numeric or diacritic romanization line] pairs.
"""

import json
import logging
from pathlib import Path

from corpus.scrapers.github_tarball import iter_tarball_files, save_scrape, tarball_url

logger = logging.getLogger(__name__)

JSON_DIR = "JSON格式資料/"


def scrape(repo: str) -> list[dict]:
    """Return every work as its JSON object plus `來源檔` (path under JSON格式資料/, no suffix)."""
    works: list[dict] = []
    keep = lambda path: path.startswith(JSON_DIR) and path.endswith(".json")  # noqa: E731
    for path, data in iter_tarball_files(tarball_url(repo), keep):
        work = json.loads(data)
        work["來源檔"] = path[len(JSON_DIR) : -len(".json")]
        works.append(work)
    if not works:
        raise ValueError(f"No {JSON_DIR}*.json in {repo}; check upstream layout")
    works.sort(key=lambda w: w["來源檔"])
    logger.info("Extracted %d works", len(works))
    return works


def scrape_and_save(repo: str, cache_dir: Path) -> Path:
    works = scrape(repo)
    return save_scrape(cache_dir, works, len(works), "works")
