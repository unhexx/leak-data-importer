"""Abstract base class for all data importers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Optional

from leak_data_importer.models.person import PersonRecord


class BaseImporter(ABC):
    """Base class for leak data importers.

    Each importer knows how to handle one specific messy format
    (txt reports, sql dumps, csv from specific forums, etc.).
    """

    name: str = "base"
    supported_extensions: tuple[str, ...] = ()

    def __init__(self, source: Path | str, **options):
        self.source = Path(source)
        self.options = options

    @abstractmethod
    def iter_records(self) -> Iterator[PersonRecord]:
        """Yield normalized PersonRecord objects one by one (memory efficient)."""
        raise NotImplementedError

    def run(self) -> list[PersonRecord]:
        """Convenience method that materializes all records (use with caution on huge files)."""
        return list(self.iter_records())

    @classmethod
    def can_handle(cls, path: Path | str) -> bool:
        """Quick check whether this importer can probably handle the given file."""
        p = Path(path)
        if cls.supported_extensions:
            return p.suffix.lower() in cls.supported_extensions
        return False
