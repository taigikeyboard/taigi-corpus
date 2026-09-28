# taigi_bible_nt — 新約臺語聖經三譯本

The Taiwanese New Testament in three translations, from 楊允言's collection:
1916 巴克禮 (Barclay), 1975 高陳 (Kho-Tân), 2008 現代台語譯本.

- **780 chapters** (260 per translation; one `Document` per chapter per translation), 23,822 verse pairs
- `text` = Han-Lo verses, one per line; `metadata.parallel_poj` = diacritic POJ, line-aligned
- `tags`: `translation:<巴克禮譯本 | 高陳譯本 | 現代譯本>`, `book:<book slug>`, `script:poj`
- `publication_date` = the translation year
- `id`: `taigi_bible_nt:<version folder>/<book folder>/<chapter>`

Religious register; the 1916 and 1975 texts use period vocabulary. Consumers
building a modern-usage model may want to down-weight or drop them by tag.

## Upstream

- GitHub: <https://github.com/Taiwanese-Corpus/Pakhelke-1916_KoTan-1975_hiantaiekpun-2008_taiwanese-bible> (last push 2016-07)
- Same `JSON格式資料/` layout as `kipsupin_2009`; fetched by `corpus/scrapers/doc2json.py`.
- Reading / audio: <https://bible.fhl.net/>

## License

**Unknown.** The 1916 translation is out of copyright; the 1975 and 2008
translations remain under their publishers' copyright.
