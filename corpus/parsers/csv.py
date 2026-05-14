"""CSV → list of row dicts. Source decides how rows become documents."""

import csv as _csv
from io import StringIO
from pathlib import Path


def parse_csv(data: str | bytes | Path) -> list[dict]:
    if isinstance(data, Path):
        with open(data, encoding="utf-8") as f:
            return list(_csv.DictReader(f))
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    return list(_csv.DictReader(StringIO(data)))
