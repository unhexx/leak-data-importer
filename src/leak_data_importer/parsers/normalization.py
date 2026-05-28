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
