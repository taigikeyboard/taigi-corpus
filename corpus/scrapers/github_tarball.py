"""Shared fetch + cache helpers for sources published as files inside a GitHub repo.

Several frozen Taiwanese-Corpus repos ship many small files and no combined
download, so the scraper streams the repo tarball and keeps only the members
it needs. The result is cached as one `scrape-<timestamp>.json` per source.
"""

import json
import logging
import tarfile
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

USER_AGENT = "taigi-corpus scraper (https://github.com/taigikeyboard/taigi-corpus)"


def tarball_url(repo: str, branch: str = "master") -> str:
    """codeload URL for `owner/name` at `branch`."""
    return f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{branch}"


def iter_tarball_files(url: str, keep: Callable[[str], bool]) -> Iterator[tuple[str, bytes]]:
    """Stream a .tar.gz and yield (path inside repo, bytes) for members where keep(path)."""
    logger.info("Fetching %s", url)
    with httpx.stream(
        "GET", url, headers={"User-Agent": USER_AGENT}, timeout=600, follow_redirects=True
    ) as r:
        r.raise_for_status()
        with tarfile.open(fileobj=_ResponseReader(r.iter_bytes()), mode="r|gz") as tar:
            for member in tar:
                if not member.isfile():
                    continue
                # Drop the "<repo>-<branch>/" prefix GitHub adds to every member.
                path = member.name.split("/", 1)[1] if "/" in member.name else member.name
                if not keep(path):
                    continue
                extracted = tar.extractfile(member)
                if extracted is not None:
                    yield path, extracted.read()


def save_scrape(cache_dir: Path, payload: list | dict, count: int, unit: str) -> Path:
    """Write payload as `scrape-<timestamp>.json`, delete older scrapes, return the path."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    new_path = cache_dir / f"scrape-{stamp}.json"
    new_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in cache_dir.glob("scrape-*.json"):
        if f != new_path:
            f.unlink()
    logger.info("Saved %d %s → %s", count, unit, new_path.name)
    return new_path


class _ResponseReader:
    """Minimal file-like adapter so tarfile can read a streamed HTTP body."""

    def __init__(self, chunks: Iterator[bytes]):
        self._chunks = chunks
        self._buffer = b""

    def read(self, size: int = -1) -> bytes:
        while size < 0 or len(self._buffer) < size:
            try:
                self._buffer += next(self._chunks)
            except StopIteration:
                break
        if size < 0:
            data, self._buffer = self._buffer, b""
        else:
            data, self._buffer = self._buffer[:size], self._buffer[size:]
        return data
