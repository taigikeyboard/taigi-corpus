"""Plain text passthrough (handles bytes → str decoding)."""

from pathlib import Path


def parse_text(data: str | bytes | Path) -> str:
    if isinstance(data, Path):
        return data.read_text(encoding="utf-8", errors="replace")
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return data
