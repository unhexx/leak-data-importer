"""
Convenience factories for creating common entity types found in Russian leak reports.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from leak_data_importer.graph.entity import Entity


def make_person(
    full_name: Optional[str] = None,
    birth_date: Optional[date] = None,
    source_ref: Optional[str] = None,
    **extra_properties
) -> Entity:
    props = {}
    if full_name:
        props["full_name"] = full_name
    if birth_date:
        props["birth_date"] = birth_date.isoformat()

    props.update(extra_properties)

    return Entity(
        type="person",
        properties=props,
        source_refs=[source_ref] if source_ref else [],
        canonical_key=full_name.lower().replace(" ", "_") if full_name else None,
    )


def make_phone(phone: str, source_ref: Optional[str] = None, **props) -> Entity:
    return Entity(
        type="phone_number",
        properties={"number": phone, **props},
        source_refs=[source_ref] if source_ref else [],
        canonical_key=phone,
    )


def make_email(email: str, source_ref: Optional[str] = None, **props) -> Entity:
    return Entity(
        type="email_address",
        properties={"address": email.lower(), **props},
        source_refs=[source_ref] if source_ref else [],
        canonical_key=email.lower(),
    )


def make_passport(number: str, source_ref: Optional[str] = None, **props) -> Entity:
    return Entity(
        type="passport",
        properties={"number": number, **props},
        source_refs=[source_ref] if source_ref else [],
        canonical_key=number,
    )


def make_snils(number: str, source_ref: Optional[str] = None, **props) -> Entity:
    return Entity(
        type="snils",
        properties={"number": number, **props},
        source_refs=[source_ref] if source_ref else [],
        canonical_key=number,
    )


def make_esia_account(esia_id: str, source_ref: Optional[str] = None, **props) -> Entity:
    return Entity(
        type="esia_account",
        properties={"esia_id": esia_id, **props},
        source_refs=[source_ref] if source_ref else [],
        canonical_key=esia_id,
    )


def make_address(address: str, source_ref: Optional[str] = None, **props) -> Entity:
    return Entity(
        type="physical_address",
        properties={"address": address, **props},
        source_refs=[source_ref] if source_ref else [],
        canonical_key=address.lower()[:64],
    )


def make_vehicle(vin: str, source_ref: Optional[str] = None, **props) -> Entity:
    return Entity(
        type="vehicle",
        properties={"vin": vin, **props},
        source_refs=[source_ref] if source_ref else [],
        canonical_key=vin.upper(),
    )


def make_sim_card(iccid: str | None = None, imsi: str | None = None, source_ref: Optional[str] = None, **props) -> Entity:
    props = {"iccid": iccid, "imsi": imsi, **props}
    key = iccid or imsi or str(id(props))
    return Entity(
        type="sim_card",
        properties=props,
        source_refs=[source_ref] if source_ref else [],
        canonical_key=key,
    )
