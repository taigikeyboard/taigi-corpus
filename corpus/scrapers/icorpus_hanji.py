"""Scraper for the iCorpus Han-character / Tâi-lô edition (Taiwanese-Corpus/icorpus_ka1_han3-ji7).

Frozen upstream (last push 2015-11). Three line-aligned files under `語料/` are
kept: 原始華語 (Mandarin), 自動標人工改漢字 (hand-corrected Taiwanese Han
characters, space-separated words) and 自動標人工改音標 (hand-corrected
numeric-tone Tâi-lô, the same words). The files carry no article breaks, so
each article of the original iCorpus (`corpus.scrapers.icorpus`) is located by
its first two Mandarin lines; lines up to the next located article belong to it.
"""

import logging
import re
from difflib import SequenceMatcher
from pathlib import Path

from corpus.scrapers import icorpus
from corpus.scrapers.github_tarball import iter_tarball_files, save_scrape, tarball_url

logger = logging.getLogger(__name__)

REPO = "Taiwanese-Corpus/icorpus_ka1_han3-ji7"
FILES = {
    "語料/原始華語.txt": "華語",
    "語料/自動標人工改漢字.txt": "漢字",
    "語料/自動標人工改音標.txt": "音標",
}
# The two editions were edited separately, so the second line only has to be similar.
SECOND_LINE_MIN_RATIO = 0.6
_NON_TEXT = re.compile(r"[\s，。、「」『』：；！？,.!?:;()（）《》〈〉…—\-\"']")


def _key(line: str) -> str:
    return _NON_TEXT.sub("", line)


def _similar(keys: list[str], index: int, expected: str) -> bool:
    if index >= len(keys):
        return False
    return SequenceMatcher(None, keys[index], expected).ratio() >= SECOND_LINE_MIN_RATIO


def _locate_articles(zh_lines: list[str], articles: list[dict]) -> list[tuple[dict, int]]:
    """Return (article, start line) for every iCorpus article found in zh_lines, in order."""
    keys = [_key(line) for line in zh_lines]
    located: list[tuple[dict, int]] = []
    cursor = 0
    for article in sorted(articles, key=lambda a: int(a["文號"])):
        heads = [k for k in (_key(x) for x in (article.get("華語") or "").split("\n")) if k][:2]
        if not heads:
            continue
        for start in range(cursor, len(keys)):
            if keys[start] != heads[0]:
                continue
            if len(heads) > 1 and not _similar(keys, start + 1, heads[1]):
                continue
            located.append((article, start))
            cursor = start + 1
            break
    return located


def scrape() -> list[dict]:
    """Fetch the three aligned files and split them into iCorpus articles."""
    texts: dict[str, list[str]] = {}
    for path, data in iter_tarball_files(tarball_url(REPO), lambda p: p in FILES):
        texts[FILES[path]] = data.decode("utf-8").rstrip("\n").split("\n")
    missing = {"華語", "漢字", "音標"} - texts.keys()
    if missing:
        raise ValueError(f"{REPO} tarball lacks {sorted(missing)}; check upstream layout")
    n = len(texts["華語"])
    if not (len(texts["漢字"]) == len(texts["音標"]) == n):
        raise ValueError(f"{REPO} files are not line-aligned; check upstream")

    located = _locate_articles(texts["華語"], icorpus.scrape())
    if not located:
        raise ValueError("No iCorpus article matched; check that icorpus.json is reachable")
    if located[0][1] != 0:
        logger.warning("  first %d lines precede any located article", located[0][1])
        located.insert(0, ({"文號": "unmatched-0", "日期": ""}, 0))

    entries: list[dict] = []
    for index, (article, start) in enumerate(located):
        stop = located[index + 1][1] if index + 1 < len(located) else n
        entries.append(
            {
                "文號": article["文號"],
                "日期": article.get("日期") or "",
                "漢字": texts["漢字"][start:stop],
                "音標": texts["音標"][start:stop],
                "華語": texts["華語"][start:stop],
            }
        )
    logger.info("Split %d lines into %d articles", n, len(entries))
    return entries


def scrape_and_save(cache_dir: Path) -> Path:
    entries = scrape()
    return save_scrape(cache_dir, entries, len(entries), "articles")
