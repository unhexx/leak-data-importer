"""
Common relationship types used when modeling leak data connections.
"""

from __future__ import annotations

from typing import Optional

from leak_data_importer.graph.entity import Relationship


def has_phone(person_id: str, phone_id: str, source: Optional[str] = None, confidence: Optional[float] = None, **props) -> Relationship:
    return Relationship(
        from_id=person_id,
        to_id=phone_id,
        type="has_phone",
        properties=props,
        source_ref=source,
        confidence=confidence,
    )


def has_email(person_id: str, email_id: str, source: Optional[str] = None, confidence: Optional[float] = None, **props) -> Relationship:
    return Relationship(
        from_id=person_id,
        to_id=email_id,
        type="has_email",
        properties=props,
        source_ref=source,
        confidence=confidence,
    )


def has_document(person_id: str, document_id: str, doc_type: str, source: Optional[str] = None, **props) -> Relationship:
    return Relationship(
        from_id=person_id,
        to_id=document_id,
        type="has_document",
        properties={"document_type": doc_type, **props},
        source_ref=source,
    )


def registered_at(person_id: str, address_id: str, date: Optional[str] = None, source: Optional[str] = None, **props) -> Relationship:
    return Relationship(
        from_id=person_id,
        to_id=address_id,
        type="registered_at",
        properties={"date": date, **props},
        source_ref=source,
    )


def owns_account(person_id: str, account_id: str, account_type: str, source: Optional[str] = None, **props) -> Relationship:
    return Relationship(
        from_id=person_id,
        to_id=account_id,
        type="owns_account",
        properties={"account_type": account_type, **props},
        source_ref=source,
    )


def associated_with(from_id: str, to_id: str, rel_type: str, source: Optional[str] = None, confidence: Optional[float] = None, **props) -> Relationship:
    """Generic association when we don't have a more specific type yet."""
    return Relationship(
        from_id=from_id,
        to_id=to_id,
        type=rel_type,
        properties=props,
        source_ref=source,
        confidence=confidence,
    )
