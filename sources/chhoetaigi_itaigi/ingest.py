"""2016+ iTaigi 華台對照典 (ChhoeTaigi)."""

from corpus.aggregators.chhoetaigi import make_ingester
from corpus.schema import Script

ingest = make_ingester(
    csv_filename="ChhoeTaigi_iTaigiHoataiTuichiautian.csv",
    headword_fields=["HanLoTaibunPoj", "PojUnicode"],
    body_fields=[("華文", "HoaBun")],
    script=Script.HANLO,
    publication_date="2016",
)
