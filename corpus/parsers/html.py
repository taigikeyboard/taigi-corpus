"""HTML → plain text. Generic; source-specific selectors live in ingest.py."""

from bs4 import BeautifulSoup

_BLOCK_TAGS = ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "tr")


def parse_html(html: str | bytes, *, container_selector: str | None = None) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    container = soup.select_one(container_selector) if container_selector else None
    if container is None:
        container = soup

    for br in container.find_all("br"):
        br.replace_with("\n")
    for tag in container.find_all(_BLOCK_TAGS):
        tag.insert_before("\n")
        tag.insert_after("\n")

    return container.get_text()
