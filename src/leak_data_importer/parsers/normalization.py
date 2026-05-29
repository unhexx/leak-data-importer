"""
Normalization utilities as per the detailed specification.
"""

import re
from datetime import date, datetime
from typing import Optional
from dateutil import parser as date_parser


def normalize_phone(phone: str) -> Optional[str]:
    """
    Normalize Russian phone to +7XXXXXXXXXX format.
    """
    if not phone:
        return None

    # Remove everything except digits and leading +
    cleaned = re.sub(r"[^\d+]", "", phone.strip())

    if cleaned.startswith("+"):
        digits = cleaned[1:]
    else:
        digits = cleaned

    # Handle Russian specifics
    if len(digits) == 10 and digits.startswith("9"):
        return "+7" + digits
    if len(digits) == 11 and digits.startswith("8"):
        return "+7" + digits[1:]
    if len(digits) == 11 and digits.startswith("7"):
        return "+" + digits

    if len(digits) >= 10:
        # Best effort
        return "+" + digits[-10:] if len(digits) > 10 else "+" + digits

    return None


def normalize_date(value: str) -> Optional[date]:
    """
    Parse various date formats using dayfirst=True.
    """
    if not value or not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    try:
        # dateutil with dayfirst for Russian format
        dt = date_parser.parse(value, dayfirst=True, fuzzy=True)
        return dt.date()
    except (ValueError, TypeError, OverflowError):
        return None


def normalize_datetime(value: str) -> Optional[datetime]:
    """
    Parse datetime with fuzzy matching.
    """
    if not value or not isinstance(value, str):
        return None
    try:
        return date_parser.parse(value, dayfirst=True, fuzzy=True)
    except (ValueError, TypeError):
        return None


def normalize_fio(fio: str) -> str:
    """
    Normalize FIO to Title Case.
    """
    if not fio:
        return ""
    parts = [p.strip().capitalize() for p in re.split(r"\s+", fio.strip()) if p.strip()]
    return " ".join(parts)


def normalize_inn(inn: str) -> Optional[str]:
    """Normalize INN: accept only pure digit strings of length 10 or 12."""
    if not inn:
        return None
    cleaned = inn.strip()
    if not re.fullmatch(r"\d{10}|\d{12}", cleaned):
        return None
    return cleaned


def normalize_snils(snils: str) -> Optional[str]:
    """Normalize SNILS to XXX-XXX-XXX XX format."""
    if not snils:
        return None
    digits = re.sub(r"\D", "", snils)
    if len(digits) != 11:
        return None
    return f"{digits[:3]}-{digits[3:6]}-{digits[6:9]} {digits[9:]}"


def normalize_passport(number: str) -> Optional[str]:
    """Normalize Russian passport to 10 digits."""
    if not number:
        return None
    digits = re.sub(r"\D", "", number)
    return digits if len(digits) == 10 else None


def normalize_address(address: str) -> Optional[str]:
    """Normalize Russian address - basic cleanup and standardization."""
    if not address or not isinstance(address, str):
        return None

    # Basic cleanup
    cleaned = address.strip()

    # Remove extra whitespace
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Common replacements
    replacements = [
        (r"г\.\s*", "г. "),
        (r"г\s*\.?\s*", "г. "),  # city abbreviations
        (r"ул\.\s*", "ул. "),
        (r"д\.\s*", "д. "),
        (r"кв\.\s*", "кв. "),
        (r"корп\.\s*", "корп. "),
        (r"стр\.\s*", "стр. "),
    ]

    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    return cleaned if cleaned else None


def normalize_address_structured(address: str) -> dict[str, str]:
    """
    Normalize Russian address to structured components.

    Extracts: region, city, street, house, apartment, postal_code

    Returns:
        Dict with normalized address components
    """
    if not address:
        return {}

    result = {
        "raw": address.strip(),
        "region": "",
        "city": "",
        "street": "",
        "house": "",
        "apartment": "",
        "postal_code": "",
    }

    # Russian address patterns
    text = address.strip()

    # Extract postal code (6 digits)
    postal_match = re.search(r"\b(\d{6})\b", text)
    if postal_match:
        result["postal_code"] = postal_match.group(1)

    # Extract apartment (can be "кв. 15", "кв.15", "апарт. 5", "квартира 5")
    apt_match = re.search(r"(?:кв\.?|апарт\.?|квартира)\s*(\d+[\wа-я]?)", text, re.IGNORECASE)
    if apt_match:
        result["apartment"] = apt_match.group(1)

    # Extract house (can be "д. 15", "дом 15", "стр. 1", "строение 1")
    house_match = re.search(r"(?:д\.?|дом\s*|стр\.?|строение\s*)(\d+[\wа-я]?)", text, re.IGNORECASE)
    if house_match:
        result["house"] = house_match.group(1)

    # Try to extract city - common patterns
    city_match = re.search(r"(?:г\.|город)\s+([А-Яа-яЁё\s\-]+?)(?:,|$)", text)
    if city_match:
        result["city"] = city_match.group(1).strip()

    # Try to extract region - common patterns
    region_match = re.search(r"(?:обл\.|область)\s+([А-Яа-яЁё\s\-]+?)(?:,|$)", text)
    if region_match:
        result["region"] = region_match.group(1).strip()

    # Try to extract street
    street_match = re.search(r"(?:ул\.|улица|пер\.|переулок|пр-кт\.|проспект|пл\.|площадь)\s+([А-Яа-яЁё\s\-]+?)(?:,|$)", text, re.IGNORECASE)
    if street_match:
        result["street"] = street_match.group(1).strip()

    return result
