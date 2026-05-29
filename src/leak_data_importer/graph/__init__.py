"""
Graph-oriented data model for leak data.

Use this when you want to build connections between objects
(phones, emails, people, documents, accounts, etc.) instead of flat records.
"""

from leak_data_importer.graph.entity import Entity, Relationship, ImportGraph
from leak_data_importer.graph.factories import (
    make_document,
    make_email,
    make_esia_account,
    make_event,
    make_location,
    make_passport,
    make_person,
    make_phone,
    make_sim_card,
    make_snils,
    make_vehicle,
    make_address,
)
from leak_data_importer.graph.relationships import (
    associated_with,
    event_at,
    has_document,
    has_email,
    has_phone,
    issued_to,
    located_at,
    owns_account,
    registered_at,
    related_to,
)
from leak_data_importer.graph.result import ImportGraphResult

__all__ = [
    "Entity",
    "Relationship",
    "ImportGraph",
    "make_person",
    "make_phone",
    "make_email",
    "make_passport",
    "make_snils",
    "make_esia_account",
    "make_address",
    "make_vehicle",
    "make_sim_card",
    "make_event",
    "make_location",
    "make_document",
    "has_phone",
    "has_email",
    "has_document",
    "registered_at",
    "owns_account",
    "associated_with",
    "event_at",
    "located_at",
    "issued_to",
    "related_to",
    "ImportGraphResult",
]
