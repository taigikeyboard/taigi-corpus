"""Scraper for 《TGB通訊》 articles kept in sih4sing5hong5/huan1-ik8_gian2-kiu3.

The TGB bulletin was crawled from its blog in 2014 and split into one Han-Lo
Taiwanese file (`NNNN.閩`) and one Mandarin file (`NNNN.國`) per article under
`語料/TGB/分開/`. The repo is large (research code + models), so the tarball is
streamed and only that folder is kept. Articles without a Taiwanese file are
Mandarin-only and dropped.
"""

import logging
from pathlib import Path

from corpus.scrapers.github_tarball import iter_tarball_files, save_scrape, tarball_url

logger = logging.getLogger(__name__)

REPO = "sih4sing5hong5/huan1-ik8_gian2-kiu3"
SPLIT_DIR = "語料/TGB/分開/"


def scrape() -> list[dict]:
    """Return {編號, 閩, 國} per article that has a Taiwanese file."""
    files: dict[str, dict[str, str]] = {}
    keep = lambda path: path.startswith(SPLIT_DIR)  # noqa: E731
    for path, data in iter_tarball_files(tarball_url(REPO), keep):
        number, _, kind = path[len(SPLIT_DIR) :].partition(".")
        files.setdefault(number, {})[kind] = data.decode("utf-8")
    articles = [
        {"編號": number, "閩": parts["閩"], "國": parts.get("國", "")}
        for number, parts in sorted(files.items())
        if parts.get("閩", "").strip()
    ]
    if not articles:
        raise ValueError(f"No {SPLIT_DIR}*.閩 in {REPO}; check upstream layout")
    logger.info("Extracted %d articles (%d files)", len(articles), len(files))
    return articles


def scrape_and_save(cache_dir: Path) -> Path:
    articles = scrape()
    return save_scrape(cache_dir, articles, len(articles), "articles")
