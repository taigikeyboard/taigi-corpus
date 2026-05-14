"""1913 甘字典 廈門音新字典 (ChhoeTaigi)."""

from corpus.aggregators.chhoetaigi import make_ingester
from corpus.schema import Script

ingest = make_ingester(
    csv_filename="ChhoeTaigi_KamJitian.csv",
    headword_fields=["HanLoTaibunPoj", "PojUnicode"],
    body_fields=[("解說", "KaisoehHanLoPoj")],
    script=Script.HANLO,
    publication_date="1913",
)
