"""
Repository for Person model.

Provides CRUD operations and typed query finders for persons.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from leak_data_importer.db.models import Person
from leak_data_importer.db.repositories.base import BaseRepository


class PersonRepository(BaseRepository[Person]):
    """Repository for Person model."""

    def __init__(self, session: Session) -> None:
        """Initialize the Person repository."""
        super().__init__(Person, session)

    def get_by_fio(self, fio: str) -> list[Person]:
        """
        Fetch persons by FIO (full name search).

        Uses GIN trigram index for fuzzy matching.

        Args:
            fio: The person's full name

        Returns:
            List of Person instances
        """
        query = select(Person).where(Person.fio == fio)
        return list(self._session.execute(query).scalars().all())

    def get_by_fio_like(self, fio_pattern: str, limit: int = 50) -> list[Person]:
        """
        Fetch persons by FIO pattern (partial match).

        Args:
            fio_pattern: The FIO pattern to search for
            limit: Maximum number of results

        Returns:
            List of Person instances
        """
        query = select(Person).where(Person.fio.ilike(f"%{fio_pattern}%")).limit(limit)
        return list(self._session.execute(query).scalars().all())

    def get_by_birth_date(self, birth_date: date) -> list[Person]:
        """
        Fetch persons by birth date.

        Args:
            birth_date: The birth date to filter by

        Returns:
            List of Person instances
        """
        query = select(Person).where(Person.birth_date == birth_date)
        return list(self._session.execute(query).scalars().all())

    def get_by_passport(self, passport: str) -> list[Person]:
        """
        Fetch persons by main passport number.

        Args:
            passport: The passport number

        Returns:
            List of Person instances
        """
        query = select(Person).where(Person.main_passport == passport)
        return list(self._session.execute(query).scalars().all())

    def get_by_snils(self, snils: str) -> list[Person]:
        """
        Fetch persons by SNILS number.

        Args:
            snils: The SNILS number

        Returns:
            List of Person instances
        """
        query = select(Person).where(Person.main_snils == snils)
        return list(self._session.execute(query).scalars().all())

    def get_by_inn(self, inn: str) -> list[Person]:
        """
        Fetch persons by INN.

        Args:
            inn: The INN number

        Returns:
            List of Person instances
        """
        query = select(Person).where(Person.main_inn == inn)
        return list(self._session.execute(query).scalars().all())

    def get_by_report_id(self, report_id: Any) -> list[Person]:
        """
        Fetch all persons linked to a report.

        Args:
            report_id: The report UUID

        Returns:
            List of Person instances
        """
        query = select(Person).where(Person.report_id == report_id)
        return list(self._session.execute(query).scalars().all())
