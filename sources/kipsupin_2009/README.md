# kipsupin_2009 — 教育部臺灣閩南語字詞頻調查工作語料 (2009)

Texts 楊允言 collected for the Ministry of Education Taiwanese character and
word frequency survey (2009): folk tales, textbooks, prose, fiction, 歌仔冊,
褒歌, reportage, speeches, drama, theses.

- 1,093 works, **4,469 pieces** (one `Document` per 篇), 59,558 paragraph pairs
- `text` = Han / Han-Lo paragraphs; `metadata.parallel_poj` = numeric-tone
  romanization, line-aligned (mostly POJ, some Tâi-lô such as `Tshiunn3`)
- `tags`: `collection:<upstream folder>`, `category:<文類>`,
  `original-script:<書寫系統>` (the work's original writing system — 漢字,
  漢羅 or 羅馬字; the Han-Lo side exists for every piece), `grade:<年級別>`
- `id`: `kipsupin_2009:<folder>/<file>-<piece index>`

## Upstream

- GitHub: <https://github.com/Taiwanese-Corpus/Ungian_2009_KIPsupin> (last push 2018-07)
- One JSON per work under `JSON格式資料/`, converted from DOC tables by
  [KIPsupin_doc2yaml](https://github.com/sih4sing5hong5/KIPsupin_doc2yaml);
  `corpus/scrapers/doc2json.py` streams the repo tarball and keeps those files.
- Survey results: <https://kipsupin.iis.sinica.edu.tw/>

## License

**Unknown.** No LICENSE upstream; copyright stays with the original authors
and publishers.
