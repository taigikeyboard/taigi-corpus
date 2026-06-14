# kok4hau7 — 國校仔課本 (國小台語課本)

Elementary-school Taiwanese (台語) textbook lessons, compiled by 楊允言 from
five publishers' Grade 1-6 readers (翰林, 康軒, 真平, 安可, 巧兒).

- 60 volumes, **367 lessons** (one `Document` per 篇/lesson)
- `text` = 漢字 lines; `metadata.parallel_poj` = aligned 台羅 (numeric-tone Tâi-lô)
- `script` = `han` (all volumes are 書寫系統=漢字)
- `tags`: `subset:kok4hau7`, `publisher:<出版社>`, `grade:<年級別>`, `book:<書名>`
- `id`: `kok4hau7:<來源檔>-<lesson index>` (e.g. `kok4hau7:翰林1-3`)

## Upstream

- GitHub: <https://github.com/Taiwanese-Corpus/kok4hau7-kho3pun2>
- Per-volume JSON lives under `JSON格式資料/<出版者>/`; there is no combined
  file, so the scraper fetches the repo tarball and extracts every
  `JSON格式資料/**/*.json` in memory.
- `make build-kok4hau7` re-fetches in full; the latest scrape is cached at
  `raw/scrape-<timestamp>.json`.

## License

**Unknown.** The upstream repo has no LICENSE file. Textbook content is
copyright of the respective publishers; the files were compiled by 楊允言.
Verify per-publisher authorization before commercial or training use.
