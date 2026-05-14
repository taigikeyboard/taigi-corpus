"""Text normalization for corpus output."""

import re
import unicodedata

_HORIZONTAL_WS = re.compile(r"[ \t 　]+")
_MULTI_NL = re.compile(r"\n{3,}")


def normalize(text: str) -> str:
    """Unicode NFC, collapse repeated horizontal whitespace, collapse 3+
    newlines to 2, strip per-line whitespace, strip overall."""
    text = unicodedata.normalize("NFC", text)
    lines = [_HORIZONTAL_WS.sub(" ", line.strip()) for line in text.splitlines()]
    text = "\n".join(lines)
    text = _MULTI_NL.sub("\n\n", text)
    return text.strip()
