"""1976 Maryknoll 台英辭典 (ChhoeTaigi)."""

from corpus.aggregators.chhoetaigi import make_ingester
from corpus.schema import Script

ingest = make_ingester(
    csv_filename="ChhoeTaigi_MaryknollTaiengSutian.csv",
    headword_fields=["PojUnicode"],
    body_fields=[("華文", "HoaBun"), ("英文", "EngBun")],
    script=Script.LO,
    publication_date="1976",
)
