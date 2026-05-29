"""
Repository for Report model.

Provides CRUD operations and typed query finders for reports.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from leak_data_importer.db.models import Report
from leak_data_importer.db.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Repository for Report model."""

    def __init__(self, session: Session) -> None:
        """Initialize the Report repository."""
        super().__init__(Report, session)

    def get_by_filename(self, filename: str) -> Report | None:
        """
        Fetch a report by filename.

        Args:
            filename: The report filename

        Returns:
            The Report instance or None if not found
        """
        query = select(Report).where(Report.filename == filename)
        return self._session.execute(query).scalars().first()

    def get_by_status(self, status: str) -> list[Report]:
        """
        Fetch reports by status.

        Args:
            status: The status to filter by

        Returns:
            List of Report instances
        """
        query = select(Report).where(Report.status == status)
        return list(self._session.execute(query).scalars().all())

    def get_by_main_fio(self, fio: str) -> list[Report]:
        """
        Fetch reports by main person FIO.

        Args:
            fio: The main person FIO

        Returns:
            List of Report instances
        """
        query = select(Report).where(Report.main_fio == fio)
        return list(self._session.execute(query).scalars().all())

    def get_recent(self, limit: int = 10) -> list[Report]:
        """
        Fetch recently imported reports.

        Args:
            limit: Maximum number of reports to return

        Returns:
            List of Report instances ordered by import date
        """
        query = select(Report).order_by(Report.imported_at.desc()).limit(limit)
        return list(self._session.execute(query).scalars().all())
