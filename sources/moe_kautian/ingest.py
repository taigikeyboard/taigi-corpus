"""教育部臺灣台語常用詞辭典 (sutian.moe.edu.tw kautian.ods).

ODS dump with 19 sheets. We join 3 for each Document:

- 詞目 (headwords): 漢字 + 羅馬字 + 分類, keyed by 詞目id
- 義項 (senses): 詞性 + 解說, many per 詞目id
- 例句 (examples): 漢字 + 羅馬字 + 華語, many per 義項id

Each output Document is one 詞目 plus its enumerated senses, with the
example sentences indented under their owning sense.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import pandas as pd

from corpus.normalize import normalize
from corpus.pipeline import content_hash
from corpus.schema import Document, DocumentMetadata, Provenance, Script, SourceMetadata
from corpus.scrapers.moe_kautian import download_and_save

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "sources.moe_kautian.ingest@v1"
PROCESSOR_VERSION = "corpus.scrapers.moe_kautian@v1"


def _cell(row: dict, key: str) -> str:
    """Read a cell as a stripped str. Treats pandas NaN / None as empty."""
    v = row.get(key)
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compose_text(
    hw: dict,
    senses: list[dict],
    examples_by_sense: dict[int, list[dict]],
) -> str:
    hanji = _cell(hw, "漢字")
    if not hanji:
        return ""
    poj = _cell(hw, "羅馬字")
    category = _cell(hw, "分類")

    lines = [hanji]
    if poj:
        lines.append(f"羅馬字: {poj}")
    if category:
        lines.append(f"分類: {category}")

    for i, sense in enumerate(senses, 1):
        meaning = _cell(sense, "解說")
        pos = _cell(sense, "詞性")
        if not meaning and not pos:
            continue
        prefix = f"【{pos}】" if pos else ""
        lines.append(f"{i}. {prefix}{meaning}")
        for ex in examples_by_sense.get(sense["義項id"], []):
            ex_han = _cell(ex, "漢字")
            if not ex_han:
                continue
            ex_rom = _cell(ex, "羅馬字")
            ex_hua = _cell(ex, "華語")
            if ex_rom and ex_hua:
                lines.append(f"   例:{ex_han}（{ex_rom}）— {ex_hua}")
            elif ex_rom:
                lines.append(f"   例:{ex_han}（{ex_rom}）")
            elif ex_hua:
                lines.append(f"   例:{ex_han} — {ex_hua}")
            else:
                lines.append(f"   例:{ex_han}")

    return "\n".join(lines)


def ingest(source: SourceMetadata, source_dir: Path) -> Iterator[Document]:
    ods_path = download_and_save(source_dir / "raw")
    logger.info("Reading 3 sheets from %s", ods_path.name)

    df_words = pd.read_excel(ods_path, sheet_name="詞目", engine="odf")
    df_senses = pd.read_excel(ods_path, sheet_name="義項", engine="odf")
    df_examples = pd.read_excel(ods_path, sheet_name="例句", engine="odf")
    logger.info(
        "Loaded %d 詞目, %d 義項, %d 例句",
        len(df_words), len(df_senses), len(df_examples),
    )

    senses_by_word: dict[int, list[dict]] = {}
    for wid, group in df_senses.sort_values("義項id").groupby("詞目id"):
        senses_by_word[int(wid)] = group.to_dict("records")

    examples_by_sense: dict[int, list[dict]] = {}
    for sid, group in df_examples.sort_values("例句順序").groupby("義項id"):
        examples_by_sense[int(sid)] = group.to_dict("records")

    now = datetime.now(timezone.utc)

    for hw in df_words.to_dict("records"):
        wid = int(hw["詞目id"])
        senses = senses_by_word.get(wid, [])
        text = normalize(_compose_text(hw, senses, examples_by_sense))
        if not text:
            continue

        yield Document(
            id=f"{source.source_id}:{wid}",
            text=text,
            metadata=DocumentMetadata.from_source(
                source,
                format="ods",
                collected_at=now,
                script=Script.HANLO,
                tags=["dictionary"],
            ),
            provenance=Provenance(
                raw_path=f"{ods_path.name}#詞目id={wid}",
                extractor=EXTRACTOR_VERSION,
                processor=PROCESSOR_VERSION,
                content_hash=content_hash(text),
            ),
        )
