"""Excel → list of row dicts (first sheet by default)."""

from pathlib import Path

import pandas as pd


def parse_excel(path: str | Path, *, sheet: str | int = 0) -> list[dict]:
    df = pd.read_excel(path, sheet_name=sheet)
    return df.to_dict(orient="records")
