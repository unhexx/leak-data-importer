"""
Repository for PersonLink model.

Provides CRUD operations for entity resolution linking decisions.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from leak_data_importer.db.models import PersonLink
from leak_data_importer.db.repositories.base import BaseRepository


class PersonLinkRepository(BaseRepository[PersonLink]):
    """Repository for PersonLink model."""

    def __init__(self, session: Session) -> None:
        """Initialize the PersonLink repository."""
        super().__init__(PersonLink, session)

    def get_by_persons(
        self,
        person_a_id: UUID,
        person_b_id: UUID,
    ) -> Optional[PersonLink]:
        """
        Fetch link between two persons (in either direction).

        Args:
            person_a_id: First person UUID
            person_b_id: Second person UUID

        Returns:
            PersonLink if exists, None otherwise
        """
        query = select(PersonLink).where(
            or_(
                and_(
                    PersonLink.person_a_id == person_a_id,
                    PersonLink.person_b_id == person_b_id,
                ),
                and_(
                    PersonLink.person_a_id == person_b_id,
                    PersonLink.person_b_id == person_a_id,
                ),
            )
        )
        return self._session.execute(query).scalars().first()

    def get_by_person_a(self, person_a_id: UUID) -> list[PersonLink]:
        """
        Fetch all links where person_a is the first person.

        Args:
            person_a_id: Person UUID

        Returns:
            List of PersonLink instances
        """
        query = select(PersonLink).where(PersonLink.person_a_id == person_a_id)
        return list(self._session.execute(query).scalars().all())

    def get_by_person_b(self, person_b_id: UUID) -> list[PersonLink]:
        """
        Fetch all links where person_b is the second person.

        Args:
            person_b_id: Person UUID

        Returns:
            List of PersonLink instances
        """
        query = select(PersonLink).where(PersonLink.person_b_id == person_b_id)
        return list(self._session.execute(query).scalars().all())

    def get_by_confidence_range(
        self,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0,
    ) -> list[PersonLink]:
        """
        Fetch links by confidence score range.

        Args:
            min_confidence: Minimum confidence (default 0.0)
            max_confidence: Maximum confidence (default 1.0)

        Returns:
            List of PersonLink instances
        """
        query = select(PersonLink).where(
            PersonLink.confidence.between(min_confidence, max_confidence)
        )
        return list(self._session.execute(query).scalars().all())

    def get_unreviewed(self, limit: int = 100) -> list[PersonLink]:
        """
        Fetch unreviewed links for manual review.

        Args:
            limit: Maximum number of results

        Returns:
            List of unreviewed PersonLink instances
        """
        query = select(PersonLink).where(
            PersonLink.is_reviewed == False
        ).limit(limit)
        return list(self._session.execute(query).scalars().all())

    def get_confirmed(self) -> list[PersonLink]:
        """
        Fetch all confirmed links.

        Returns:
            List of confirmed PersonLink instances
        """
        query = select(PersonLink).where(
            and_(
                PersonLink.is_reviewed == True,
                PersonLink.is_confirmed == True,
            )
        )
        return list(self._session.execute(query).scalars().all())

    def search_by_strategy(self, strategy: str) -> list[PersonLink]:
        """
        Fetch links by match strategy.

        Args:
            strategy: Match strategy name (e.g., "exact_passport", "fuzzy_fio")

        Returns:
            List of PersonLink instances
        """
        query = select(PersonLink).where(PersonLink.match_strategy == strategy)
        return list(self._session.execute(query).scalars().all())

    def create_link(
        self,
        person_a_id: UUID,
        person_b_id: UUID,
        confidence: float,
        match_strategy: str,
    ) -> PersonLink:
        """
        Create a new person link.

        Args:
            person_a_id: First person UUID
            person_b_id: Second person UUID
            confidence: Confidence score (0.0-1.0)
            match_strategy: Strategy used for matching

        Returns:
            Created PersonLink instance
        """
        link = PersonLink(
            person_a_id=person_a_id,
            person_b_id=person_b_id,
            confidence=confidence,
            match_strategy=match_strategy,
        )
        self._session.add(link)
        self._session.commit()
        self._session.refresh(link)
        return link

    def mark_reviewed(
        self,
        link_id: UUID,
        is_confirmed: bool,
        reviewed_by: str,
        notes: Optional[str] = None,
    ) -> Optional[PersonLink]:
        """
        Mark a link as reviewed.

        Args:
            link_id: Link UUID
            is_confirmed: Whether the match is confirmed
            reviewed_by: Who reviewed the link
            notes: Optional review notes

        Returns:
            Updated PersonLink or None if not found
        """
        link = self.get_by_id(link_id)
        if link:
            link.is_reviewed = True
            link.is_confirmed = is_confirmed
            link.reviewed_by = reviewed_by
            if notes:
                link.review_notes = notes
            self._session.commit()
            self._session.refresh(link)
        return link
