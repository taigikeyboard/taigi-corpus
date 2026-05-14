# CLAUDE.md

Guidelines for **Claude Code (claude.ai/code)** when working with this codebase.

## Project Overview

**Taigi Corpus** — Taiwanese (台語) language corpus pipeline for model training.
Ingest heterogeneous sources (HTML, PDF, CSV, Excel, plain text) into a single
normalized JSONL corpus with complete per-document metadata (source, license,
copyright, original URL, language/script, provenance).

## Project Structure

```
taigi-corpus/
├── corpus/                # Generic pipeline (format-agnostic)
│   ├── schema.py          # Pydantic models: Document, SourceMetadata, ...
│   ├── normalize.py       # Unicode NFC, whitespace, newline collapsing
│   ├── pipeline.py        # Source loader + JSONL writer
│   ├── cli.py             # `corpus list | build | stats`
│   └── parsers/           # html, pdf, csv, excel, text
├── sources/               # One folder per data source
│   └── tsbp/              # First source: 台文通訊BONG報
│       ├── source.yaml    # Source-level metadata (license, URL, ...)
│       ├── ingest.py      # Yields normalized Document records
│       ├── raw/           # Cached raw downloads (gitignored)
│       └── README.md
└── data/                  # Build outputs
    └── normalized/        # data/normalized/{source_id}.jsonl
```

## Core Principles

1. **Source isolation** — Each source is a self-contained folder. Adding a new
   source means copying the template and writing one `ingest.py` that yields
   `Document` records. No central registry to edit.
2. **Metadata is mandatory** — Every document must carry source, license,
   copyright holder, original URL, language, script, and provenance. License
   may be `unknown` but must be explicit; never silent.
3. **Raw → Normalized → Corpus, JSONL all the way** — Plain JSONL is the
   storage format at every stage. No databases, no parquet (yet), no
   bespoke binary formats.
4. **YAGNI** — No tokenization, dedup, or quality filtering in this repo.
   Those belong in the consuming training pipeline. Build hooks only when
   a second use case appears.
5. **Boring tooling** — `uv` for env, `pydantic` for schemas, `argparse`
   for CLI, `httpx` + `beautifulsoup4` for fetching/parsing. No frameworks.

## Development Principles

**Clean code**

- One purpose per function. Resist premature abstraction — wait for the
  second use case before factoring a helper out (we did this for the
  ChhoeTaigi aggregator: 9 sources before extracting `make_ingester`).
- Trust internal code. Validate only at external boundaries (HTTP, file
  I/O, user input). Pydantic catches the rest.
- Delete obsolete code rather than leaving it behind a feature flag or
  `# legacy` comment.
- Plain `dict` / `list` for transient data; pydantic models at boundaries
  (`Document`, `SourceMetadata`).
- Failures fail loud and early with an actionable message. Don't silently
  fall back to stale data without saying so.

**Consistent logging**

- Every module starts with `logger = logging.getLogger(__name__)`.
  Never `print()` in library code (CLI is allowed to write to stdout).
- Use `%`-style format, not f-strings:
  `logger.info("Loaded %d entries from %s", n, path)`.
- Levels: `INFO` for progress, `WARNING` for recoverable / fallback,
  `ERROR` for user-visible failure.
- Message style: completed action (`"Saved %d entries → %s"`) or current
  step (`"Fetching start_index=%d"`). Past tense for "done", present
  participle for "in flight".
- 2-space indent for sub-step lines: `"  page %d/%d"`. One line per
  log statement. The arrow `→` (U+2192) means "wrote to / produced".

**No verbose noise**

- Names do the explaining. Don't write comments that paraphrase the
  code — only the *why* when non-obvious (a workaround, a constraint,
  a surprise).
- One-line docstrings on public functions. Multi-paragraph descriptions
  belong in `CLAUDE.md` / `README.md`, not docstrings.
- No PR numbers, task IDs, or caller names in source comments — they
  rot. The PR description and `git log` are the right home.
- No emojis in code, docs, log messages, or commit messages.
- Error messages tell the user what to do, not what went wrong inside:
  `"Set $CHHOETAIGI_DB_PATH or clone the repo as a sibling"` ✓, not
  `"FileNotFoundError: path missing"` ✗.

## Document Schema

Every record in `data/normalized/{source}.jsonl` and `data/corpus/corpus.jsonl`
follows this shape (see `corpus/schema.py` for the authoritative definition):

```json
{
  "id": "tsbp:2024-03_some-slug",
  "text": "正文 Han-Lo 文字...",
  "metadata": {
    "source_id": "tsbp",
    "source_name": "台文通訊BONG報",
    "source_url": "https://tsbp.tgb.org.tw",
    "original_url": "https://tsbp.tgb.org.tw/2024/03/xxx.html",
    "license": "unknown",
    "license_notes": "需聯絡編輯部確認再次利用授權",
    "copyright_holder": "台文通訊BONG報編輯部 / 各文章原作者",
    "language": "nan-Hant-TW",
    "script": "hanlo",
    "format": "html",
    "collected_at": "2026-05-14T12:00:00Z",
    "publication_date": "2024-03-15",
    "author": "...",
    "title": "...",
    "tags": ["issue:123"]
  },
  "provenance": {
    "raw_path": "sources/tsbp/raw/feed_page_0001.json",
    "extractor": "sources.tsbp.ingest@v1",
    "processor": "corpus.parsers.html@v1",
    "content_hash": "sha256:..."
  }
}
```

## Commands

```bash
uv sync                    # install dependencies
make help                  # list configured source IDs
make build-<id>            # fetch latest + process one source (always live)
```

**One action per source, one source per command.** There is no
bulk "build everything" target — invoke `build-<id>` for each source
you want to rebuild. `build-<id>` always reaches upstream:

- `tsbp` runs an incremental Blogger-feed fetch (fast; stops at first all-cached page).
- `chhoetaigi_*` re-reads the sibling clone of ChhoeTaigiDatabase.
- `pts_taigitv` / `kanggesu` re-scrape the upstream site (full re-fetch).
- The scrape file in `sources/<id>/raw/` is replaced; only the latest is kept.

Underlying CLI (`uv run corpus list | build <id> | stats <id>|--all`)
is still available if needed.

## Adding a New Source

1. `mkdir sources/<source_id>` (e.g. `sources/moe-dict`)
2. Create `source.yaml` with the fields in `SourceMetadata` (see
   `sources/tsbp/source.yaml` as template). License must be explicit
   (`unknown` is allowed).
3. Write `ingest.py` exposing `def ingest(source, source_dir) -> Iterator[Document]`.
   Use parsers from `corpus.parsers` (html/pdf/csv/excel/text) and
   `corpus.normalize.normalize()` for the text body. Use
   `DocumentMetadata.from_source(...)` to avoid copying source fields by hand.
4. `uv run corpus build <source_id>` — confirm output JSONL looks right.
5. Add a one-paragraph `README.md` in the source folder describing what
   it contains and how it was obtained.

## Conventions

- **Python 3.13+**, `uv` for package management, `ruff` for lint/format,
  exact-pin all dependencies in `pyproject.toml`
- **English** for code and code docs; **Taiwanese Mandarin** for
  user-facing text and source descriptions
- **Communication**: reply in 台灣華語, concise bullet points, batch
  clarifications in the first turn
- **License field must be explicit** — never silently default to a
  permissive license. `unknown` is the honest default until verified.
