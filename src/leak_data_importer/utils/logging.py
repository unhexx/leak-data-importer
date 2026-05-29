"""
Утилиты для логирования с защитой PII данных.

Модуль предоставляет безопасные функции для логирования операций импорта и обработки
данных без утечки персональной информации (PII).
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Any, Optional

from leak_data_importer.utils.redaction import is_pii_safe


class PiiSafeLogger:
    """
    logger с защитой от утечки PII данных.
    
    Автоматически проверяет и маскирует потенциальные PII значения
    перед выводом в лог.
    """
    
    def __init__(self, name: str = "leak-data-importer", verbose: bool = False) -> None:
        self.name = name
        self.verbose = verbose
        self._enabled = True
    
    def disable(self) -> None:
        """Отключить логирование."""
        self._enabled = False
    
    def enable(self) -> None:
        """Включить логирование."""
        self._enabled = True
    
    def _format_message(self, message: str, *args: Any, **kwargs: Any) -> str:
        """Форматировать сообщение с проверкой PII."""
        if not args and not kwargs:
            return message
        
        # Проверяем аргументы на наличие PII
        safe_args = []
        for arg in args:
            if isinstance(arg, str) and not is_pii_safe(arg):
                safe_args.append("[REDACTED]")
            else:
                safe_args.append(arg)
        
        safe_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str) and not is_pii_safe(value):
                safe_kwargs[key] = "[REDACTED]"
            else:
                safe_kwargs[key] = value
        
        try:
            return message.format(*safe_args, **safe_kwargs)
        except (ValueError, KeyError):
            return message
    
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Логировать информационное сообщение."""
        if not self._enabled:
            return
        
        formatted = self._format_message(message, *args, **kwargs)
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: {formatted}", file=sys.stdout)
    
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Логировать предупреждение."""
        if not self._enabled:
            return
        
        formatted = self._format_message(message, *args, **kwargs)
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] WARNING: {formatted}", file=sys.stderr)
    
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Логировать ошибку."""
        if not self._enabled:
            return
        
        formatted = self._format_message(message, *args, **kwargs)
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ERROR: {formatted}", file=sys.stderr)
    
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Логировать отладочное сообщение (только в verbose режиме)."""
        if not self._enabled or not self.verbose:
            return
        
        formatted = self._format_message(message, *args, **kwargs)
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] DEBUG: {formatted}", file=sys.stdout)
    
    def success(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Логировать успешное завершение операции."""
        if not self._enabled:
            return
        
        formatted = self._format_message(message, *args, **kwargs)
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] SUCCESS: {formatted}", file=sys.stdout)


# Глобальный экземпляр логгера
_default_logger: Optional[PiiSafeLogger] = None


def get_logger(name: str = "leak-data-importer", verbose: bool = False) -> PiiSafeLogger:
    """
    Получить глобальный экземпляр PiiSafeLogger.
    
    Args:
        name: Имя логгера
        verbose: Включить отладочный вывод
    
    Returns:
        Экземпляр PiiSafeLogger
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = PiiSafeLogger(name, verbose)
    return _default_logger


def log_record_summary(
    record: Any,
    include_name: bool = False,
    include_count: bool = True,
) -> str:
    """
    Безопасная сводка о записи для логирования.
    
    Args:
        record: Объект записи (PersonRecord или похожий)
        include_name: Включить ФИО (обычно False для безопасности)
        include_count: Включить только количественные показатели
    
    Returns:
        Безопасная строка сводки
    """
    parts = []
    
    if include_name and hasattr(record, "full_name") and record.full_name:
        parts.append(str(record.full_name))
    else:
        parts.append("Record")
    
    if hasattr(record, "phones") and include_count:
        parts.append(f"phones={len(record.phones)}")
    
    if hasattr(record, "emails") and include_count:
        parts.append(f"emails={len(record.emails)}")
    
    if hasattr(record, "passports") and include_count:
        parts.append(f"passports={len(record.passports)}")
    
    if hasattr(record, "parsing_strategy") and record.parsing_strategy:
        parts.append(f"strategy={record.parsing_strategy}")
    
    if hasattr(record, "confidence") and record.confidence is not None:
        parts.append(f"conf={record.confidence:.2f}")
    
    return " | ".join(parts)


def audit_log_for_pii(message: str) -> bool:
    """
    Проверить сообщение на наличие потенциального PII перед логированием.
    
    Args:
        message: Сообщение для проверки
    
    Returns:
        True если сообщение безопасно, False если содержит PII
    """
    # Простая проверка - если сообщение содержит незамаскированные данные
    # это потенциально небезопасно
    
    # Проверяем наличие маркеров PII в открытом виде
    pii_patterns = [
        r"\d{4}\s*\d{4}",  # Паспорт (4+4 цифры)
        r"\d{3}-\d{3}-\d{3}\s*\d{2}",  # СНИЛС
        r"\+\d{11,}",  # Телефон с +
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Email
        r"\d{10,12}",  # ИНН
    ]
    
    import re
    
    for pattern in pii_patterns:
        if re.search(pattern, message):
            # Нашли потенциальный PII
            if is_pii_safe(message):
                return True  # Уже замаскирован
            return False  # Найден PII в открытом виде
    
    return True  # Не найден PII
