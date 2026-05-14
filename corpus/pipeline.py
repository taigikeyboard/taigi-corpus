"""Load sources, run their ingester, write JSONL."""

import hashlib
import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Iterator

import yaml

from corpus.schema import Document, SourceMetadata

logger = logging.getLogger(__name__)


def load_source(source_dir: Path) -> SourceMetadata:
    yaml_path = source_dir / "source.yaml"
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return SourceMetadata(**data)


def _load_ingest_module(source_dir: Path):
    """Dynamically load `sources/<id>/ingest.py` without requiring sources/ to
    be a package."""
    module_name = f"taigi_corpus_sources.{source_dir.name}.ingest"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, source_dir / "ingest.py")
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load ingest module for {source_dir.name}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def ingest_source(source_dir: Path) -> Iterator[Document]:
    source = load_source(source_dir)
    mod = _load_ingest_module(source_dir)
    if not hasattr(mod, "ingest"):
        raise AttributeError(f"{source_dir.name}/ingest.py must define `ingest(source, source_dir)`")
    yield from mod.ingest(source, source_dir)


def write_jsonl(docs: Iterator[Document], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc.model_dump(mode="json"), ensure_ascii=False) + "\n")
            count += 1
    return count


def content_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
