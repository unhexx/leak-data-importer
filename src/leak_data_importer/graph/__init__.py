"""
Graph-oriented data model for leak data.

Use this when you want to build connections between objects
(phones, emails, people, documents, accounts, etc.) instead of flat records.
"""

from leak_data_importer.graph.entity import Entity, Relationship, ImportGraph
from leak_data_importer.graph.factories import (
    make_person, make_phone, make_email, make_passport, make_snils,
    make_esia_account, make_address, make_vehicle, make_sim_card,
)
from leak_data_importer.graph.relationships import (
    has_phone, has_email, has_document, registered_at, owns_account, associated_with,
)
from leak_data_importer.graph.result import ImportGraphResult

__all__ = [
    "Entity", "Relationship", "ImportGraph",
    "make_person", "make_phone", "make_email", "make_passport", "make_snils",
    "make_esia_account", "make_address", "make_vehicle", "make_sim_card",
    "has_phone", "has_email", "has_document", "registered_at", "owns_account", "associated_with",
    "ImportGraphResult",
]
