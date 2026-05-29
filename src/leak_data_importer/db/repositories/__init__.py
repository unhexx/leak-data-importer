"""
Database repositories.

Provides typed repository classes for all database models
with CRUD operations and custom query finders.
"""

from leak_data_importer.db.repositories.base import BaseRepository
from leak_data_importer.db.repositories.document import DocumentRepository
from leak_data_importer.db.repositories.person import PersonRepository
from leak_data_importer.db.repositories.person_link import PersonLinkRepository
from leak_data_importer.db.repositories.report import ReportRepository

__all__ = [
    "BaseRepository",
    "ReportRepository",
    "PersonRepository",
    "PersonLinkRepository",
    "DocumentRepository",
]
