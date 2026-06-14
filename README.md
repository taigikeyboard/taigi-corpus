# Taigi Corpus

Taiwanese (台語) corpus pipeline for language-model training. Ingests
heterogeneous sources (HTML / ODS / CSV / JSON / TAR) into normalized
JSONL with full per-document metadata (source, license, copyright,
URL, language, script, provenance).

**352,398 documents** across 18 sources (plus one orphan file,
`chhoetaigi_moe.jsonl`, 24,608 docs with no `sources/` folder — see Sources).
Snapshot of `data/normalized/` is versioned in this repo.
[`data/normalized/manifest.json`](data/normalized/manifest.json) is the
machine-readable catalog (genre, license class, counts, sha per source) —
regenerate with `uv run corpus manifest`.

Several sources carry **parallel data**: icorpus (TW↔ZH sentence pairs),
nmtl_dadwt / khinhoan_pojbh / kok4hau7 / sinpak_900leku (Han↔POJ/台羅 in
`metadata.parallel_poj`), and ungian_guliau_supin (separate HL and POJ subsets).

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

| ID                   | Name                          | Format | Docs        | License             |
|----------------------|-------------------------------|--------|------------:|---------------------|
| chhoetaigi_taihoa    | 2002+ 台華線頂對照典           | CSV    | 91,332      | CC-BY-SA-4.0        |
| chhoetaigi_taijit    | 1932 台日大辭典 (台譯版)       | CSV    | 69,515      | CC-BY-NC-SA-3.0-TW  |
| chhoetaigi_maryknoll | 1976 Maryknoll 台英辭典        | CSV    | 55,903      | CC-BY-NC-SA-3.0-TW  |
| chhoetaigi_embree    | 1973 Embree 台英辭典           | CSV    | 36,734      | CC-BY-NC-SA-3.0-TW  |
| moe_kautian          | 教育部臺灣台語常用詞辭典         | ODS    | 29,606      | CC-BY-ND-3.0-TW     |
| chhoetaigi_kam       | 1913 甘字典                    | CSV    | 24,367      | CC-BY-NC-SA-3.0-TW  |
| chhoetaigi_itaigi    | 2016+ iTaigi 華台對照典         | CSV    | 19,775      | CC0-1.0             |
| chhoetaigi_pehoe     | 1956 台灣白話基礎語句           | CSV    | 5,429       | CC-BY-SA-4.0        |
| ungian_guliau_supin  | 2005 楊允言 NSC 台語文語料庫    | TAR    | 5,207       | unknown             |
| icorpus              | 台華平行新聞語料庫 (中研院)      | JSON   | 3,266       | CC-BY-NC-SA-4.0     |
| khinhoan_pojbh       | 台灣白話字文獻館 (NTNU)          | JSON   | 2,733       | unknown             |
| nmtl_dadwt           | 台語文數位典藏資料庫 (NMTL)      | JSON   | 2,167       | unknown             |
| pts_taigitv          | 公視台語台 新詞辭典             | JSON   | 2,157       | CC-BY-4.0           |
| chhoetaigi_sitbut    | 1928 台灣植物名彙               | CSV    | 1,722       | CC-BY-SA-4.0        |
| kanggesu             | 台語工藝詞庫                    | JSON   | 1,209       | CC-BY-NC            |
| sinpak_900leku       | 新北市 900例句                  | JSON   | 821         | MIT                 |
| kok4hau7             | 國校仔課本 (國小台語課本)        | TAR    | 367         | unknown             |
| tsbp                 | 台文通訊BONG報                  | HTML   | 88          | unknown             |
| **TOTAL**            |                               |        | **352,398** |                     |

Genre and license class per source live in
[`data/normalized/manifest.json`](data/normalized/manifest.json), not this table.

**Orphan**: `data/normalized/chhoetaigi_moe.jsonl` (24,608 docs, CC-BY-ND-3.0-TW)
has no `sources/chhoetaigi_moe/` folder — it cannot be rebuilt and overlaps
`moe_kautian`. It still appears in the manifest (`genre: unknown`); resolve
(re-add ingester or drop) before relying on it.

## Manifest & licensing

`uv run corpus manifest` writes [`data/normalized/manifest.json`](data/normalized/manifest.json) —
one row per normalized file so downstream consumers can select sources by
genre, license, or script without scanning the corpus. Per row: `genre`,
`license`, `license_category`, `license_restrictions`, `license_notes`,
`scripts` (per-script doc counts), doc/char counts, parallel-field coverage,
`size_bytes`, `file_sha256`.

**Genre** (the register axis for training selection) — one per source:
`prose` (LM pretraining), `dictionary`, `terminology`, `news`,
`example_sentence`, `unknown`. Genre is source-level; join on `source_id`.

**License class** is derived from each doc's `license`. `license_category` is
the single headline bucket; `license_restrictions` lists every obligation a
single label hides (e.g. CC-BY-NC-SA = `non_commercial` + `share_alike` +
`attribution`). Document totals:

| license_category | docs    | notes |
|------------------|--------:|-------|
| non_commercial   | 190,994 | NC — no commercial training |
| share_alike      |  98,483 | CC-BY-SA — output must share-alike |
| no_derivatives   |  54,214 | CC-BY-ND — training as a derivative is legally unsettled |
| permissive       |  22,753 | CC0 / CC-BY / MIT |
| unknown          |  10,562 | rights unverified |

Only ~32% (permissive + share_alike) is comfortably training-usable; filter on
`license_category` / `license_restrictions` before use. `permissive` does not
override per-source `license_notes` (e.g. sinpak_900leku is MIT but flags
content provenance).

## Upstream

- `chhoetaigi_*` — sibling clone of [ChhoeTaigiDatabase](https://github.com/ChhoeTaigi/ChhoeTaigiDatabase) (`$CHHOETAIGI_DB_PATH` or `../ChhoeTaigiDatabase`)
- `moe_kautian` — official ODS dump `sutian.moe.edu.tw/media/senn/ods/kautian.ods`
- `pts_taigitv` — HTML scrape of `taigitv.org.tw/taigi-words`
- `kanggesu` — POST API of `kanggesu.ntcri.gov.tw`
- `tsbp` — Blogger JSON feed `tsbp.tgb.org.tw`, incremental per-entry cache
- `icorpus` — pre-built `icorpus.json` from [sih4sing5hong5/icorpus](https://github.com/sih4sing5hong5/icorpus) (Academia Sinica IIS)
- `ungian_guliau_supin` — full `master.tar.gz` from [Taiwanese-Corpus/Ungian_2005_guliau-supin](https://github.com/Taiwanese-Corpus/Ungian_2005_guliau-supin)
- `nmtl_dadwt` — pre-built `nmtl.json` from [Taiwanese-Corpus/nmtl_2006_dadwt](https://github.com/Taiwanese-Corpus/nmtl_2006_dadwt) (NMTL)
- `khinhoan_pojbh` — pre-built `pojbh.json` from [Taiwanese-Corpus/Khin-hoan_2010_pojbh](https://github.com/Taiwanese-Corpus/Khin-hoan_2010_pojbh) (NTNU 白話字文獻館)
- `kok4hau7` — repo `master.tar.gz` from [Taiwanese-Corpus/kok4hau7-kho3pun2](https://github.com/Taiwanese-Corpus/kok4hau7-kho3pun2); `JSON格式資料/**/*.json` extracted in memory
- `sinpak_900leku` — pre-built `minnan900.json` from [Taiwanese-Corpus/Sin1pak8tshi7_2015_900-le7ku3](https://github.com/Taiwanese-Corpus/Sin1pak8tshi7_2015_900-le7ku3)

## Parallel data

Four sources carry alignment data usable for sequence-to-sequence
training. Each parallel record is stored in a single `Document`; the
primary side lives in `text` and the alignment lives in a typed
metadata field.

| Source              | Pair                                | Granularity | Pairs   | Metadata field          |
|---------------------|-------------------------------------|-------------|--------:|-------------------------|
| icorpus             | Taiwanese (POJ-numerical) ↔ Mandarin | sentence    |  83,544 | `metadata.parallel_zh`  |
| nmtl_dadwt          | Han-Lo ↔ POJ-numerical              | paragraph   |  64,281 | `metadata.parallel_poj` |
| khinhoan_pojbh      | Han-Lo ↔ POJ-diacritic              | paragraph   |  37,984 | `metadata.parallel_poj` |
| ungian_guliau_supin | Han-Lo + POJ-numerical (not aligned) | —           |     —   | (separate `subset:HL` / `subset:POJ` docs) |

Within a parallel record, line N of `text` corresponds to line N of
the parallel field. khinhoan_pojbh additionally tags each document
`parallel-status:aligned` or `parallel-status:mismatched`; the pair
count above counts only `aligned` records. See each source's
`README.md` for extraction code.

Schema, conventions, and how to add a new source: see [`CLAUDE.md`](CLAUDE.md).
