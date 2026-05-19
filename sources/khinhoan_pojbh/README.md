# khinhoan_pojbh — 台灣白話字文獻館 (POJ Bûn-hiàn-koán)

Romanized Taiwanese literature archive maintained by the Graduate
Institute of Taiwan Culture, Languages and Literature at National
Taiwan Normal University (NTNU). Covers late 19th- and 20th-century
Presbyterian Church publications — the first periodicals printed in
Taiwanese — spanning 1885 (台灣府城教會報 first issue) through 2008.

## Upstream

- Website: <http://pojbh.lib.ntnu.edu.tw/>
- GitHub snapshot: <https://github.com/Taiwanese-Corpus/Khin-hoan_2010_pojbh>
  (pre-built `pojbh.json` ~22 MB)
- Fetching: HTTP GET `pojbh.json` from the raw GitHub URL on every build

## Scale

~2,733 articles (excluding 70 metadata-only stubs and 2 entries
without any Han-Lo content):

- Aligned (paragraph counts match between Han-Lo and POJ): ~2,380
  articles, ~37,984 paragraph pairs
- Mismatched (counts differ; preserved but tagged): ~355 articles

Top journals: 台灣教會公報 (1232), 台灣教會報 (433), 台南府城教會報 (388),
芥菜子 (296).

## License

**Unknown.** The upstream README states "本資料庫之內容...採用CC授權條款"
(content released under a Creative Commons license) but does not name
the specific CC variant. The license_notes field carries the relevant
copyright holders (NTNU 台灣文化及語言文學研究所 and the Taiwan
e-Learning and Digital Archives Program). Verify the specific CC
variant with upstream before commercial or training use.

## Record Shape

Each `Document`:

- `text` — Han-Lo (漢羅) article body; paragraphs joined by `\n`
- `metadata.parallel_poj` — **POJ-diacritic** version of the same
  article, paragraphs joined by `\n`. (Upstream calls this field
  `tailo`, but the actual content uses POJ orthography — e.g. `oē`,
  `Kàu-hoē`, `Le̍k-sú` — not Tâi-lô.)
- `metadata.script` — `hanlo` (the primary `text`)
- `metadata.title` — `篇名` (often "漢羅標題 [ POJ Title ]")
- `metadata.author` — `作者`
- `metadata.publication_date` — ISO-normalized from `日期`; could be
  `YYYY`, `YYYY-MM`, or `YYYY-MM-DD`
- `metadata.tags`:
  - `subset:pojbh`
  - `category:religious`
  - `parallel:poj-diacritic` (distinguishes from `parallel:poj-numerical`
    in icorpus / nmtl_dadwt)
  - `parallel-status:aligned` or `parallel-status:mismatched`
  - `journal:<刊名>` (e.g. `journal:台灣教會公報`)
  - `era:清領|日治|戰後` (derived from year)
- `id` — `khinhoan_pojbh:<pianho>`

## Training Use

Han-Lo ↔ POJ-diacritic paragraph pairs (filter for clean alignment):

```python
import json
for line in open("data/normalized/khinhoan_pojbh.jsonl"):
    doc = json.loads(line)
    if "parallel-status:aligned" not in doc["metadata"]["tags"]:
        continue
    hl = doc["text"].split("\n")
    poj = doc["metadata"]["parallel_poj"].split("\n")
    for h, p in zip(hl, poj):
        yield {"hanlo": h, "poj": p}
```

Monolingual Han-Lo: read `text` from every record.
Monolingual POJ-diacritic: read `metadata.parallel_poj` from every record.

## Known Limitations

- About 16% of articles have a paragraph-count mismatch between the
  Han-Lo and POJ sides. These are still ingested (both sides preserved
  for monolingual use) but tagged `parallel-status:mismatched`; filter
  them out before paired training.
- The upstream `tailo` field is misnamed: content is POJ-diacritic
  (e.g. `oē`, `chh`), not Tâi-lô (`uē`, `tsh`). Tagged accordingly.
- Date strings are sometimes paired with page numbers in the upstream
  `日期` field (e.g. `"1962/2/15    16-18"`). The ingester strips
  trailing tokens and keeps the date portion only.
