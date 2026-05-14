"""Source-specific scrapers that hit upstream sites directly.

Each scraper exposes `scrape() -> list[dict]` (does the network work) and
`scrape_or_use_cache(cache_dir) -> Path` (returns latest cached scrape if
present, else scrapes and saves a timestamped JSON to cache_dir).

The cache files use the same `scrape-<timestamp>.json` naming and entry
list shape as the upstream taigikeyboard mirror repos, so previously
mirror-downloaded files remain usable.
"""
