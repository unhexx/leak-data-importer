"""
Repository for Document model.

Provides CRUD operations and typed query finders for documents.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from leak_data_importer.db.models import DocType, Document
from leak_data_importer.db.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document model."""

    def __init__(self, session: Session) -> None:
        """Initialize the Document repository."""
        super().__init__(Document, session)

    def get_by_doc_type_and_number(
        self, doc_type: DocType, number: str, report_id: Any | None = None
    ) -> list[Document]:
        """
        Fetch documents by type and number.

        Args:
            doc_type: The document type
            number: The document number
            report_id: Optional report ID to filter by

        Returns:
            List of Document instances
        """
        query = select(Document).where(
            Document.doc_type == doc_type,
            Document.number == number,
        )
        if report_id:
            query = query.where(Document.report_id == report_id)
        return list(self._session.execute(query).scalars().all())

    def get_by_person_id(self, person_id: Any) -> list[Document]:
        """
        Fetch all documents for a person.

        Args:
            person_id: The person UUID

        Returns:
            List of Document instances
        """
        query = select(Document).where(Document.person_id == person_id)
        return list(self._session.execute(query).scalars().all())

    def get_by_report_id(self, report_id: Any) -> list[Document]:
        """
        Fetch all documents linked to a report.

        Args:
            report_id: The report UUID

        Returns:
            List of Document instances
        """
        query = select(Document).where(Document.report_id == report_id)
        return list(self._session.execute(query).scalars().all())

    def get_by_type(self, doc_type: DocType) -> list[Document]:
        """
        Fetch documents by type.

        Args:
            doc_type: The document type to filter by

        Returns:
            List of Document instances
        """
        query = select(Document).where(Document.doc_type == doc_type)
        return list(self._session.execute(query).scalars().all())

    def get_by_series(self, series: str) -> list[Document]:
        """
        Fetch documents by series.

        Args:
            series: The document series

        Returns:
            List of Document instances
        """
        query = select(Document).where(Document.series == series)
        return list(self._session.execute(query).scalars().all())

    def get_by_issuer(self, issuer: str) -> list[Document]:
        """
        Fetch documents by issuer.

        Args:
            issuer: The document issuer

        Returns:
            List of Document instances
        """
        query = select(Document).where(Document.issuer.ilike(f"%{issuer}%"))
        return list(self._session.execute(query).scalars().all())

    def get_active(self) -> list[Document]:
        """
        Fetch active documents (not expired).

        Returns:
            List of active Document instances
        """
        from sqlalchemy import or_

        query = select(Document).where(
            or_(
                Document.status == "active",
                Document.expiry_date.is_(None),
            )
        )
        return list(self._session.execute(query).scalars().all())
