"""1932 台日大辭典 台譯版 (ChhoeTaigi)."""

from corpus.aggregators.chhoetaigi import make_ingester
from corpus.schema import Script

ingest = make_ingester(
    csv_filename="ChhoeTaigi_TaijitToaSutian.csv",
    headword_fields=["HanLoTaibunPoj", "PojUnicode"],
    body_fields=[("解說", "KaisoehHanLoPoj"), ("例句", "LekuHanLoPoj")],
    script=Script.HANLO,
    publication_date="1932",
)
