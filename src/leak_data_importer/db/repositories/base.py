"""
Base repository class with common CRUD operations.

Provides standard create, read, update, delete operations
for all database models.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from leak_data_importer.db.models import Base

# Type variable for generic repository
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations.

    Each entity repository should inherit from this and add
    entity-specific query methods.
    """

    def __init__(self, model: type[ModelType], session: Session) -> None:
        """
        Initialize repository with model class and database session.

        Args:
            model: The SQLAlchemy model class
            session: The database session
        """
        self._model = model
        self._session = session

    @property
    def session(self) -> Session:
        """Get the database session."""
        return self._session

    def create(self, **kwargs: Any) -> ModelType:
        """
        Create a new record.

        Args:
            **kwargs: Model field values

        Returns:
            The created model instance
        """
        instance = self._model(**kwargs)
        self._session.add(instance)
        self._session.flush()
        return instance

    def get_by_id(self, id: Any) -> ModelType | None:
        """
        Fetch a record by ID.

        Args:
            id: The record UUID

        Returns:
            The model instance or None if not found
        """
        return self._session.get(self._model, id)

    def get_all(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ModelType]:
        """
        Fetch all records with optional pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of model instances
        """
        query = select(self._model).offset(offset)
        if limit:
            query = query.limit(limit)
        return list(self._session.execute(query).scalars().all())

    def update(self, id: Any, **kwargs: Any) -> ModelType | None:
        """
        Update a record by ID.

        Args:
            id: The record UUID
            **kwargs: Fields to update

        Returns:
            The updated model instance or None if not found
        """
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            self._session.flush()
        return instance

    def delete(self, id: Any, hard: bool = False) -> bool:
        """
        Delete a record by ID.

        Args:
            id: The record UUID
            hard: If False, soft-delete; if True, hard delete

        Returns:
            True if deleted, False if not found
        """
        instance = self.get_by_id(id)
        if instance:
            if hard:
                self._session.delete(instance)
            else:
                # Soft delete - set status field if exists
                if hasattr(instance, "status"):
                    setattr(instance, "status", "deleted")
            self._session.flush()
            return True
        return False

    def count(self) -> int:
        """
        Count total records.

        Returns:
            Number of records
        """
        return len(self.get_all())

    def commit(self) -> None:
        """Commit the current transaction."""
        self._session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self._session.rollback()
