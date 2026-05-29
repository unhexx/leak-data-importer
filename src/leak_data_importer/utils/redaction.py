"""
Утилиты для маскирования (редкации) персональных данных (PII).

Модуль предоставляет функции для безопасного отображения чувствительных данных:
- Паспорт РФ (45 06 123456 -> ** ** *456)
- СНИЛС (123-456-789 01 -> ***-***-** 01)
- ИНН (1234567890 -> **********)
- Телефон (+79161234567 -> +79***4567)
- Email (user@mail.ru -> u***@mail.ru)

Использование:
    from leak_data_importer.utils.redaction import redact_passport, redact_snils
    
    passport = redact_passport("45 06 123456")  # "** ** *456"
    snils = redact_snils("123-456-789 01")   # "***-***-** 01"
"""

import hashlib
import re
import secrets
from typing import Optional


def redact_passport(passport: str) -> str:
    """
    Маскировать российский паспорт.
    
    Формат: XX XX NNNNNN -> ** ** *NNNN
    Первые 4 цифры скрыты, последние 4 видны.
    
    Args:
        passport: Номер паспорта (например, "45 06 123456")
    
    Returns:
        Маскированный паспорт (например, "** ** *456")
    """
    if not passport or not isinstance(passport, str):
        return ""
    
    # Удаляем пробелы
    digits = re.sub(r"\D", "", passport)
    
    if len(digits) < 6:
        return "*" * len(passport)
    
    # Первые 2 серии + последние 4 номера
    number = digits[-4:]
    
    return f"** ** {number}"


def redact_snils(snils: str) -> str:
    """
    Маскировать СНИЛС.
    
    Формат: XXX-XXX-XXX NN -> ***-***-** NN
    Первые 6 цифр скрыты, последние 2 видны.
    
    Args:
        snils: Номер СНИЛС (например, "123-456-789 01")
    
    Returns:
        Маскированный СНИЛС (например, "***-***-** 01")
    """
    if not snils or not isinstance(snils, str):
        return ""
    
    # Удаляем всё кроме цифр
    digits = re.sub(r"\D", "", snils)
    
    if len(digits) < 2:
        return "*" * len(snils)
    
    # Первые 6 скрыты, последние 2 видны
    suffix = digits[-2:]
    
    # Формат с дефисами: ***-***-** NN
    return f"***-***-** {suffix}"


def redact_inn(inn: str) -> str:
    """
    Маскировать ИНН.
    
    Формат: XXXXXXXXXX (10 цифр) -> **********
    Все цифры скрыты.
    
    Args:
        inn: ИНН (например, "1234567890")
    
    Returns:
        Маскированный ИНН (например, "**********")
    """
    if not inn or not isinstance(inn, str):
        return ""
    
    digits = re.sub(r"\D", "", inn)
    
    if len(digits) < 4:
        return "*" * len(inn)
    
    # Все скрыты
    return "*" * len(digits)


def redact_phone(phone: str) -> str:
    """
    Маскировать номер телефона.
    
    Формат: +7 XXX XXX XX XX -> +79***XX XX
    Код скрыт, последние 6 цифр видны.
    
    Args:
        phone: Номер телефона (например, "+79161234567")
    
    Returns:
        Маскированный телефон (например, "+79***4567")
    """
    if not phone or not isinstance(phone, str):
        return ""
    
    # Удаляем всё кроме цифр
    digits = re.sub(r"\D", "", phone)
    
    if len(digits) < 4:
        return "*" * len(phone)
    
    # Determine country code
    if phone.lstrip().startswith("+"):
        # Phone starts with +, use actual country code
        country = digits[:2] if len(digits) >= 2 else "79"
    elif digits.startswith("8") and len(digits) >= 10:
        # Russian phone starting with 8, normalize to +7
        country = "79"
    elif digits.startswith("9") and len(digits) >= 10:
        # Russian mobile without +, normalize to +7
        country = "79"
    else:
        # Fallback - use whatever we have
        country = digits[:2] if len(digits) >= 2 else "7"
    
    last_4 = digits[-4:]  # 4567
    return f"+{country}***{last_4}"


def redact_email(email: str) -> str:
    """
    Маскировать email адрес.
    
    Формат: user@mail.ru -> u***@mail.ru
    Первая буква имени видна, остальное скрыто.
    
    Args:
        email: Email адрес (например, "user@mail.ru")
    
    Returns:
        Маскированный email (например, "u***@mail.ru")
    """
    if not email or not isinstance(email, str):
        return ""
    
    if "@" not in email:
        return redact_document(email)
    
    local, domain = email.rsplit("@", 1)
    
    if len(local) <= 1:
        masked_local = "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 1)
    
    return f"{masked_local}@{domain}"


def redact_document(document: str) -> str:
    """
    Универсальное маскирование документа.
    
    Показывает только первые 2 и последние 2 символа.
    
    Args:
        document: Номер документа
    
    Returns:
        Маскированный документ
    """
    if not document or not isinstance(document, str):
        return ""
    
    doc = document.strip()
    
    if len(doc) <= 4:
        return doc  # Short docs shown fully
    
    # Первые 2 + последние 2 (only 2 asterisks for middle)
    prefix = doc[:2]
    suffix = doc[-2:]
    
    return f"{prefix}**{suffix}"


def pii_hash(value: str, salt: Optional[str] = None) -> str:
    """
    Deterministically hash PII value using SHA-256.

    Args:
        value: Raw value to hash
        salt: Optional salt. If not provided, environment-level default
              should be used by caller in production.

    Returns:
        Hex digest SHA-256 hash
    """
    if value is None:
        value = ""
    payload = f"{salt or ''}:{value}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class PiiTokenizer:
    """
    In-memory reversible tokenizer for internal workflow usage.

    This is intentionally simple and process-local. For production-grade usage,
    replace with secure vault/KMS-backed tokenization service.
    """

    def __init__(self) -> None:
        self._forward: dict[str, str] = {}
        self._reverse: dict[str, str] = {}

    def tokenize(self, value: str) -> str:
        """Return stable token for value within current tokenizer instance."""
        if value in self._forward:
            return self._forward[value]

        token = f"tok_{secrets.token_hex(16)}"
        self._forward[value] = token
        self._reverse[token] = value
        return token

    def detokenize(self, token: str) -> Optional[str]:
        """Return original value if token exists, else None."""
        return self._reverse.get(token)


def is_pii_safe(value: str, field_type: Optional[str] = None) -> bool:
    """
    Проверить, содержит ли значение маскированные PII данные.
    
    Args:
        value: Значение для проверки
        field_type: Тип поля (passport, snils, inn, phone, email)
    
    Returns:
        True если данные уже маскированы
    """
    if not value or not isinstance(value, str):
        return True
    
    # Проверяем на маркеры маскирования
    if "*" in value or "**" in value:
        return True
    
    # Дополнительная проверка по типу
    if field_type == "passport":
        digits = re.sub(r"\D", "", value)
        if len(digits) < 6:
            return True
    elif field_type == "snils":
        digits = re.sub(r"\D", "", value)
        if len(digits) < 11:
            return True
    elif field_type == "inn":
        digits = re.sub(r"\D", "", value)
        if len(digits) < 10:
            return True
    
    return False
