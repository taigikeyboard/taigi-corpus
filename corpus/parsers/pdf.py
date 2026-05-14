"""PDF → plain text via pypdf. Page texts are joined with double newlines."""

from pathlib import Path

from pypdf import PdfReader


def parse_pdf(path: str | Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n\n".join(pages)
