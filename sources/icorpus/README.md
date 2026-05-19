# icorpus — Taiwanese-Mandarin Parallel News Corpus

Parallel Taiwanese-Mandarin news corpus released by Academia Sinica
(Dr. Meng-Chang Chen, Institute of Information Science). 3,266
articles, 83,544 sentence pairs; Taiwanese ~1.03M chars, Mandarin
~1.03M chars (upstream counts). Articles dated 2009-08 through 2016-06.

## Upstream

- Website (no longer maintained): <http://icorpus.iis.sinica.edu.tw/>
- GitHub snapshot: <https://github.com/sih4sing5hong5/icorpus>
  (last push 2018-07)
- Data file: `icorpus.json` (~8.6 MB). `corpus/scrapers/icorpus.py`
  fetches it directly from the GitHub raw URL on every build.

## License

CC-BY-NC-SA 4.0 for the corpus content. Attribution to
Academia Sinica IIS, Dr. Meng-Chang Chen. Non-commercial use only;
derivative works must be shared under the same license.

## Record Shape

Each `Document`:

- `text` — Taiwanese article, **numerical POJ** (e.g. `toa7-seng3 Bi2-kok`),
  one sentence per line
- `metadata.parallel_zh` — Mandarin translation, word-segmented,
  **line-aligned** with `text`
- `metadata.title` — first Mandarin line (article headline)
- `metadata.publication_date` — `YYYY-MM-DD`
- `metadata.tags` — `["news", "parallel", "script:poj-numerical"]`
- `id` — `icorpus:<文號>` where `文號` is 1..3266

## Training Use

Extract sentence pairs:

```python
import json
for line in open("data/normalized/icorpus.jsonl"):
    doc = json.loads(line)
    tw = doc["text"].split("\n")
    zh = doc["metadata"]["parallel_zh"].split("\n")
    for t, z in zip(tw, zh):
        yield {"tw": t, "zh": z}
```

Monolingual (Taiwanese LM): use `text` directly.

## Known Limitations

- Taiwanese is numerical POJ. Conversion to Tâi-lô diacritics or Han-Lo
  is out of scope for this repo (transliteration belongs in the
  downstream training pipeline).
- Upstream is frozen, so the corpus is effectively a fixed snapshot.
  `make build-icorpus` still re-fetches each time; content should be
  identical.
