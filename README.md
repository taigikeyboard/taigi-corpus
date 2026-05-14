# Taigi Corpus

Taiwanese (台語) corpus pipeline for language-model training. Ingests
heterogeneous sources (HTML / ODS / CSV / JSON) into normalized JSONL
with full per-document metadata (source, license, copyright, URL,
language, script, provenance).

**337,837 documents** across 12 licensed sources. Snapshot of `data/normalized/`
is versioned in this repo.

## Quick start

```bash
uv sync
make help              # list configured source IDs
make build-<id>        # fetch upstream + normalize one source
```

One source per command, no bulk targets. `make build-<id>` always reaches
upstream and replaces the raw cache; only the latest snapshot is kept.

## Layout

- `corpus/` — generic pipeline (schema, parsers, scrapers, CLI)
- `sources/<id>/` — `source.yaml` (metadata) + `ingest.py` per source
- `sources/<id>/raw/` — raw upstream cache (versioned)
- `data/normalized/<id>.jsonl` — normalized output (versioned)

## Sources

| ID                   | Name                       | Format | Docs        | License             |
|----------------------|----------------------------|--------|------------:|---------------------|
| chhoetaigi_taihoa    | 2002+ 台華線頂對照典         | CSV    | 91,332      | CC-BY-SA-4.0        |
| chhoetaigi_taijit    | 1932 台日大辭典 (台譯版)     | CSV    | 69,515      | CC-BY-NC-SA-3.0-TW  |
| chhoetaigi_maryknoll | 1976 Maryknoll 台英辭典     | CSV    | 55,903      | CC-BY-NC-SA-3.0-TW  |
| chhoetaigi_embree    | 1973 Embree 台英辭典        | CSV    | 36,734      | CC-BY-NC-SA-3.0-TW  |
| moe_kautian          | 教育部臺灣台語常用詞辭典       | ODS    | 29,606      | CC-BY-ND-3.0-TW   |
| chhoetaigi_kam       | 1913 甘字典                 | CSV    | 24,367      | CC-BY-NC-SA-3.0-TW  |
| chhoetaigi_itaigi    | 2016+ iTaigi 華台對照典      | CSV    | 19,775      | CC0-1.0             |
| chhoetaigi_pehoe     | 1956 台灣白話基礎語句         | CSV    | 5,429       | CC-BY-SA-4.0        |
| pts_taigitv          | 公視台語台 新詞辭典           | JSON   | 2,157       | CC-BY-4.0           |
| chhoetaigi_sitbut    | 1928 台灣植物名彙             | CSV    | 1,722       | CC-BY-SA-4.0        |
| kanggesu             | 台語工藝詞庫                  | JSON   | 1,209       | CC-BY-NC            |
| tsbp                 | 台文通訊BONG報              | HTML   | 88          | unknown             |
| **TOTAL**            |                            |        | **337,837** |                     |

## Upstream

- `chhoetaigi_*` — sibling clone of [ChhoeTaigiDatabase](https://github.com/ChhoeTaigi/ChhoeTaigiDatabase) (`$CHHOETAIGI_DB_PATH` or `../ChhoeTaigiDatabase`)
- `moe_kautian` — official ODS dump `sutian.moe.edu.tw/media/senn/ods/kautian.ods`
- `pts_taigitv` — HTML scrape of `taigitv.org.tw/taigi-words`
- `kanggesu` — POST API of `kanggesu.ntcri.gov.tw`
- `tsbp` — Blogger JSON feed `tsbp.tgb.org.tw`, incremental per-entry cache

Schema, conventions, and how to add a new source: see [`CLAUDE.md`](CLAUDE.md).
