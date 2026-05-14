"""Downloader for 教育部臺灣台語常用詞辭典 ODS dump.

Fetches https://sutian.moe.edu.tw/media/senn/ods/kautian.ods to cache_dir.
The remote filename is fixed (`kautian.ods`), so each call overwrites the
previous download — there is only ever one cache file.
"""

import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

URL = "https://sutian.moe.edu.tw/media/senn/ods/kautian.ods"
USER_AGENT = "taigi-corpus scraper (https://github.com/taigikeyboard/taigi-corpus)"


def download_and_save(cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / "kautian.ods"
    logger.info("Downloading %s", URL)
    # sutian.moe.edu.tw serves a chain whose CA cert is missing the
    # Subject Key Identifier extension — Python's OpenSSL rejects it while
    # curl/system TLS accepts it. The file is a public static download from
    # a .gov.tw host, so verify=False is acceptable here; corpus-level
    # content_hash still provides integrity.
    with httpx.Client(follow_redirects=True, timeout=120, verify=False) as client:
        resp = client.get(URL, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
    target.write_bytes(resp.content)
    logger.info("Saved %d bytes → %s", len(resp.content), target.name)
    return target
