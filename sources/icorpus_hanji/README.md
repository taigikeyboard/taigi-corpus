# icorpus_hanji — iCorpus 臺華平行新聞語料庫漢字臺羅版

The Han-character / Tâi-lô edition of the iCorpus news corpus, made by 薛丞宏
in 2014. The original iCorpus (source `icorpus`) has Taiwanese only as numeric
POJ; this edition adds hand-corrected Taiwanese Han characters and numeric-tone
Tâi-lô for the articles of 2008-11-06 to 2014-03-14.

- **2,559 articles, 64,110 sentences** (one `Document` per article)
- `text` = Taiwanese Han characters, **word-segmented with spaces**, one sentence per line
- `metadata.parallel_poj` = numeric-tone **Tâi-lô** (despite the field name), the
  same words in the same order: token N of a `text` line is the reading of token N
  of the `parallel_poj` line (99.97 % of lines have equal token counts)
- `metadata.parallel_zh` = the original Mandarin sentence, line-aligned
- `tags`: `news`, `parallel`, `script:tl-numerical`, `segmented:word`, `aligned:word`
- `id`: `icorpus_hanji:<文號>` — the same 文號 as the `icorpus` source

## Upstream

- GitHub: <https://github.com/Taiwanese-Corpus/icorpus_ka1_han3-ji7> (last push 2015-11)
- Files used: `語料/原始華語.txt`, `語料/自動標人工改漢字.txt`,
  `語料/自動標人工改音標.txt` (line-aligned, no article breaks).
- Article breaks are recovered from the original `icorpus.json`: an article
  starts where its first Mandarin line matches exactly and its second line is
  similar (the two editions were edited separately). 2,547 of 2,559 articles
  have exactly the original line count; when an article is not found, its lines
  stay with the article before it.

## License

CC BY 4.0 (this edition, 薛丞宏). The underlying translation belongs to the
Academia Sinica iCorpus project, released as CC BY-NC-SA 4.0 (see `icorpus`).
