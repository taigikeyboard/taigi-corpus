"""1928 台灣植物名彙 (ChhoeTaigi)."""

from corpus.aggregators.chhoetaigi import make_ingester
from corpus.schema import Script

ingest = make_ingester(
    csv_filename="ChhoeTaigi_TaioanSitbutMialui.csv",
    headword_fields=["HanLoTaibunPoj", "PojUnicode"],
    body_fields=[],
    script=Script.HANLO,
    publication_date="1928",
)
