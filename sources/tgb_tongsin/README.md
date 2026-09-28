# tgb_tongsin — TGB通訊

Articles of the TGB通訊 bulletin (essays, commentary, translations, issue
editorials; around 2012-2014), crawled from its blog in 2014 by 薛丞宏 for
Taiwanese–Mandarin translation research.

- **1,015 articles** (one `Document` per article)
- `text` = Taiwanese in Han-Lo: Han characters with POJ words inline
  (`Lán chit ê所在欠缺實實在在ê理解kap尊重`)
- `metadata.parallel_zh` = the Mandarin version published beside it; first line
  is the title, optionally `title@author`. **Not line-aligned** with `text`.
- `title` / `author` are parsed from that first Mandarin line
- `tags`: `script:hanlo-poj`, `parallel:zh-unaligned`
- `id`: `tgb_tongsin:<NNNN>` (upstream file number)

## Upstream

- GitHub: <https://github.com/sih4sing5hong5/huan1-ik8_gian2-kiu3>, folder
  `語料/TGB/分開/` (`NNNN.閩` Taiwanese, `NNNN.國` Mandarin). 164 Mandarin-only
  articles are dropped.
- The repo is large (research code and models), so the scraper streams the
  tarball and keeps only that folder.
- The same repo holds a sentence-aligned, word-segmented version
  (`語料/TGB/對齊平行閩南語資料`) whose readings were assigned by software and
  contain visible errors; it is not ingested.

## License

**Unknown.** No LICENSE upstream; copyright stays with the bulletin and authors.
