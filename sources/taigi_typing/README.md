# taigi_typing — 台語文拍字練習 文章

The articles of the 台語文拍字練習 typing-practice page
(<https://github.com/luke871016/taigi_typing>): modern Taiwanese prose, poems
and word-play by 陳建中, 張寶明, 盧廣誠, 李勤岸, 温若喬, 陳豐惠 and others.

- **35 articles** (one `Document` per article)
- 10 `mapped` articles: `text` = Han, `metadata.parallel_poj` = diacritic
  Tâi-lô, line-aligned; tags `type:mapped`, `script:tl`
- 25 `single` articles: `text` = the one version given; `script` inferred from
  its characters (`han`, `hanlo` or `lo`); tag `type:single`
- `author` = upstream `source` (author, sometimes with the book it is excerpted
  from); `original_url` = upstream `url`; upstream tags become `topic:<tag>`
- `id`: `taigi_typing:<upstream id>`

## Upstream

- `articles.js` fetched raw from the `main` branch on every build. It is a
  JavaScript object literal, parsed by a small tokenizer in
  `corpus/scrapers/taigi_typing.py` that accepts only the syntax the file uses
  and fails loudly on anything new (e.g. `${...}` interpolation).
- The page's `exampleSentences.js` (7,787 教典 example sentences) is not
  ingested: it is the same data as the `moe_kautian` examples.
- The upstream repo is also a submodule of TaigiKeyboard (`corpus/taigi-typing`),
  where it supplies dogfood sentences.

## License

**Unknown.** Upstream README: article texts belong to their authors and may be
used only inside that page; the page code is CC0.
