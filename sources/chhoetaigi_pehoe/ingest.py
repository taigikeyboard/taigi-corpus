"""1956 台灣白話基礎語句 (ChhoeTaigi)."""

from corpus.aggregators.chhoetaigi import make_ingester
from corpus.schema import Script

ingest = make_ingester(
    csv_filename="ChhoeTaigi_TaioanPehoeKichhooGiku.csv",
    headword_fields=["PojUnicode"],
    body_fields=[
        ("華文", "HoaBun"),
        ("英文", "EngBun"),
        ("例句", "LekuPoj"),
    ],
    script=Script.LO,
    publication_date="1956",
)
