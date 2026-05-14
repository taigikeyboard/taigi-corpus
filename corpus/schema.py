"""Pydantic models for corpus documents and source metadata.

Source-level metadata lives in `sources/<id>/source.yaml` and is merged into
every Document record so the output JSONL is self-contained.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Script(str, Enum):
    HAN = "han"
    LO = "lo"
    HANLO = "hanlo"
    UNKNOWN = "unknown"


class SourceMetadata(BaseModel):
    """Source-level metadata. Loaded from `sources/<id>/source.yaml`."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_name: str
    source_url: str
    license: str = "unknown"
    license_notes: str = ""
    copyright_holder: str = "unknown"
    contact: str = ""
    language: str = "nan-Hant-TW"
    default_script: Script = Script.UNKNOWN
    description: str = ""


class DocumentMetadata(BaseModel):
    """Per-document metadata. Built from SourceMetadata + per-doc overrides."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_name: str
    source_url: str
    original_url: str = ""
    license: str
    license_notes: str = ""
    copyright_holder: str
    language: str
    script: Script
    format: str
    collected_at: datetime
    publication_date: str = ""
    author: str = ""
    title: str = ""
    tags: list[str] = Field(default_factory=list)

    @classmethod
    def from_source(
        cls,
        source: SourceMetadata,
        *,
        format: str,
        collected_at: datetime,
        script: Script | None = None,
        original_url: str = "",
        publication_date: str = "",
        author: str = "",
        title: str = "",
        tags: list[str] | None = None,
    ) -> "DocumentMetadata":
        return cls(
            source_id=source.source_id,
            source_name=source.source_name,
            source_url=source.source_url,
            original_url=original_url,
            license=source.license,
            license_notes=source.license_notes,
            copyright_holder=source.copyright_holder,
            language=source.language,
            script=script or source.default_script,
            format=format,
            collected_at=collected_at,
            publication_date=publication_date,
            author=author,
            title=title,
            tags=tags or [],
        )


class Provenance(BaseModel):
    """Where this document came from and how it was produced."""

    model_config = ConfigDict(extra="forbid")

    raw_path: str = ""
    extractor: str = ""
    processor: str = ""
    content_hash: str = ""


class Document(BaseModel):
    """A normalized corpus document. One per line in JSONL output."""

    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    metadata: DocumentMetadata
    provenance: Provenance
