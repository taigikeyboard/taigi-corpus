"""Scraper for the articles of luke871016/taigi_typing (台語文拍字練習).

`articles.js` declares `const articles = [...]` as a JavaScript object literal:
unquoted keys, "double-quoted" and `backtick` strings, trailing commas and
`//` comments. It is converted to JSON with a small tokenizer that handles
exactly that subset and fails loudly on anything else (e.g. `${...}`).
"""

import json
import logging
import re
from pathlib import Path

import httpx

from corpus.scrapers.github_tarball import USER_AGENT, save_scrape

logger = logging.getLogger(__name__)

RAW_URL = "https://raw.githubusercontent.com/luke871016/taigi_typing/main/articles.js"
_TOKEN = re.compile(
    r"""(?P<ws>\s+)
      | (?P<comment>//[^\n]*)
      | (?P<backtick>`[^`]*`)
      | (?P<string>"(?:[^"\\]|\\.)*")
      | (?P<word>[A-Za-z_][A-Za-z0-9_]*|-?\d+(?:\.\d+)?)
      | (?P<punct>[\[\]{}:,])""",
    re.VERBOSE,
)
_LITERALS = {"true", "false", "null"}


def js_array_to_json(source: str) -> list:
    """Parse the first `[...]` literal after `=` in a JS file."""
    body = source[source.index("=") + 1 :].strip().rstrip(";").strip()
    out: list[str] = []
    pos = 0
    while pos < len(body):
        m = _TOKEN.match(body, pos)
        if not m:
            raise ValueError(f"Unsupported JavaScript at offset {pos}: {body[pos : pos + 40]!r}")
        pos = m.end()
        kind, text = m.lastgroup, m.group()
        if kind in ("ws", "comment"):
            continue
        if kind == "backtick":
            if "${" in text:
                raise ValueError("Template interpolation is not supported; update the scraper")
            out.append(json.dumps(text[1:-1], ensure_ascii=False))
        elif kind == "word" and not text[0].isdigit() and text[0] != "-" and text not in _LITERALS:
            out.append(json.dumps(text))
        elif kind == "punct" and text in "]}" and out and out[-1] == ",":
            out[-1] = text
        else:
            out.append(text)
    return json.loads("".join(out))


def scrape() -> list[dict]:
    logger.info("Fetching %s", RAW_URL)
    r = httpx.get(RAW_URL, headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True)
    r.raise_for_status()
    articles = js_array_to_json(r.text)
    logger.info("Parsed %d articles", len(articles))
    return articles


def scrape_and_save(cache_dir: Path) -> Path:
    articles = scrape()
    return save_scrape(cache_dir, articles, len(articles), "articles")
