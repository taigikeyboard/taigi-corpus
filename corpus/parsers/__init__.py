"""Format-specific text extractors.

Each parser returns plain text (or row dicts) given raw input. Import the
specific parser you need (e.g. `from corpus.parsers.html import parse_html`)
rather than from this package — that way a missing optional dependency for
one format does not break the others.

Source-specific cleanup (e.g. stripping donation footers from one
publisher's HTML) belongs in the source's `ingest.py`, not here.
"""
