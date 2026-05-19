# ungian_guliau_supin — Un Iong-gian 2005 NSC Project

"Collection of Taiwanese Written Corpus and Corpus-Based Syllable/Word
Frequency Statistics" (NSC 93-2213-E-122-001), by Un Iong-gian
(楊允言).

## Upstream

- GitHub: <https://github.com/Taiwanese-Corpus/Ungian_2005_guliau-supin>
- Paper: <http://ip194097.ntcu.edu.tw/giankiu/keoe/KKH/guliau-supin/guliau-supin.asp>
- Last push: 2018-09 (frozen snapshot)
- Fetching: HTTP GET `master.tar.gz` (~54 MB) per build; the scraper
  extracts both CSVs and every `.txt` under `轉換後資料/{HL,POJ}/` and
  joins them by filename stem.

## Scale

5,208 articles total:

- **HL** (Han-Lo, mixed Han + romanization): 3,810 articles,
  1965-2007, 17 genres (散文 1469 / 新詩 973 / 小說 302 / 報導 223 /
  評論 188 / ...).
- **POJ** (numerical romanization): 1,398 articles, 1885-2007,
  16 genres (sanbun 560 / siosoat 218 / sinsi 196 / toanki 110 / ...).

## License

**Unknown.** The upstream repo has no `LICENSE` file.

The collection aggregates works by 1,293 authors over 122 years:
- Modern works by living authors (台文通訊, 台文罔報, TGB 通訊,
  湠根, 蓮蕉花, etc.)
- Academic monographs and theses
- Early missionary translations (e.g. Barclay's 1885 Bible
  translation, which is in the public domain)

Verify per-author authorization before any commercial or training use.

## Record Shape

Each `Document`:

- `text` — full UTF-8 article (upstream converted from Big5)
- `metadata.script` — `hanlo` (HL) or `lo` (POJ)
- `metadata.title` — CSV `piautoe` field
- `metadata.author` — CSV `chokchia` field (Han for HL, romanized for POJ)
- `metadata.publication_date` — CSV `nitai` field, year string (e.g.
  `"1998"`, sometimes `"200x"`)
- `metadata.original_url` — GitHub blob URL
- `metadata.tags` — `["subset:HL|POJ", "category:<Han genre>"]`,
  plus `"script:poj-numerical"` for POJ docs
- `id` — `ungian_guliau_supin:<HL|POJ>:<csv_id>`

POJ.csv uses romanized genre labels (`sanbun`, `siosoat`, ...). The
scraper maps these to the Han labels used in HL.csv (`散文`, `小說`,
...), so downstream code can filter `category:散文` across both
subsets.

## Known Limitations

- Upstream README mentions manual character fix-ups (e.g.
  `chh"a => chhōa`, `sia5? => siaⁿ5`); residual encoding/typo
  issues may remain.
- The POJ subset uses Un Iong-gian's variant of numerical POJ:
  `Pan7--loh8-khi3`, `siuN7-tioh8` (`N` marks nasalization; `--`
  marks neutral-tone particles). Tagged `script:poj-numerical`
  alongside icorpus, though minor conventions differ.
- A small number of CSV rows have no matching `.txt`; the scraper
  logs and skips them. At time of writing: 1 POJ row, 15 HL `.txt`
  files orphaned from CSV.
