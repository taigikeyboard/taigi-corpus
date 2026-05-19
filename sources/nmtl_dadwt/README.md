# nmtl_dadwt — NMTL Digital Archive Database for Written Taiwanese

Taiwanese literary works archived by the National Museum of Taiwan
Literature (NMTL) under the DADWT project. Each article carries
**paragraph-aligned Han-Lo (漢羅) and POJ (全羅) versions** of the same
text — a different kind of parallel data from icorpus (which is
Taiwanese ↔ Mandarin).

## Upstream

- Public lookup site: <http://xdcm.nmtl.gov.tw/dadwt/pbk.asp>
- Mirror by Un Iong-gian: <http://ip194097.ntcu.edu.tw/nmtl/dadwt/pbk.asp>
- GitHub snapshot: <https://github.com/Taiwanese-Corpus/nmtl_2006_dadwt>
  (last push 2018-07; pre-built `nmtl.json` ~24 MB)
- Fetching: HTTP GET `nmtl.json` from the raw GitHub URL on every build

## Scale

2,167 articles spanning 1885 to the modern era.

Genres (`類` field): `SB` 散文, `KP` 劇本, `KS` 歌詩, `SS` 小說.
Eras (`時代` field): `C` 清領, `J` 日治, `K` 戰後.

## License

**Unknown.** The upstream repo has no `LICENSE` file. Authors span
from 1885 (Qing era missionary writings, public domain) through
20th-century literary works (copyright with the authors or their
estates) to modern submissions. Verify per-author authorization
before any commercial or training use.

## Record Shape

Each `Document`:

- `text` — Han-Lo (漢羅) version of the article; paragraphs joined by `\n`
- `metadata.parallel_poj` — POJ (全羅, numerical romanization) version
  of the **same** article; paragraphs joined by `\n`, **line-aligned**
  with `text`
- `metadata.script` — `hanlo` (the primary `text`)
- `metadata.title` — Han-Lo title (`漢羅標`)
- `metadata.author` — Han-Lo author name (`漢羅名`)
- `metadata.publication_date` — year string (`年`, e.g. `"1885"`)
- `metadata.tags` — `["subset:dadwt", "category:<散文|劇本|歌詩|小說>",
  "era:<清領|日治|戰後>"]`
- `id` — `nmtl_dadwt:<流水號>` (serial 1..2167)

## Training Use

Han-Lo ↔ POJ paragraph pairs (transliteration training):

```python
import json
for line in open("data/normalized/nmtl_dadwt.jsonl"):
    doc = json.loads(line)
    hl = doc["text"].split("\n")
    poj = doc["metadata"]["parallel_poj"].split("\n")
    for h, p in zip(hl, poj):
        yield {"hanlo": h, "poj": p}
```

Monolingual Taiwanese LM (Han-Lo): use `text` directly. For a
POJ-only corpus, read `metadata.parallel_poj` from each record.

## Known Limitations

- Upstream README documents a few known data issues (missing
  characters, mis-filed entries); see the upstream `README.md`
  "勘誤" section.
- Paragraph alignment is not perfect: some `[Han-Lo, POJ]` pairs in
  the upstream `資料` field have one side empty. These are preserved
  as-is so paragraph indices stay aligned; downstream code should
  filter pairs with an empty side before training.
- POJ here is numerical romanization (e.g. `Peh8-oe7-ji7 e5 Li7-ek`).
  This source does NOT carry a `script:poj-numerical` tag on the
  primary text because `text` is Han-Lo; the romanization lives in
  `parallel_poj`.
