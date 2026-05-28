"""Importer for the common Russian 'report_*.txt' breach report format.

These files usually contain blocks like:

    ФИО: Иванов Иван Иванович 08.08.1999
    Телефон: 79161234567 (27/46)
    Паспорт: 45 06 123456 (12/46)
    ...

The format is semi-structured, often in cp1251 or utf-8, with "confidence" scores.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Iterator, Optional

from charset_normalizer import from_bytes

from leak_data_importer.importers.base import BaseImporter
from leak_data_importer.models.person import PersonRecord


class TxtReportImporter(BaseImporter):
    """Parser for forum-style Russian leak 'report_YYYYMMDD_*.txt' files."""

    name = "txt_report"
    supported_extensions = (".txt",)

    # Common field labels we see in these dumps (case insensitive, Russian + translit)
    FIELD_PATTERNS = {
        "full_name": re.compile(r"(?:ФИО|ФИО:|name|фио)\s*[:：]?\s*(.+?)(?:\s*\(|$)", re.IGNORECASE),
        "phone": re.compile(r"(?:телефон|мобильный|phone|тел)\s*[:：]?\s*([+\d\s\-()]+)", re.IGNORECASE),
        "passport": re.compile(r"(?:паспорт|пасп|passport)\s*[:：]?\s*([\d\s]+)", re.IGNORECASE),
        "snils": re.compile(r"(?:снилс|snils)\s*[:：]?\s*([\d\s\-]+)", re.IGNORECASE),
        "email": re.compile(r"(?:email|e-mail|почта|эл\.?\s*почта)\s*[:：]?\s*([\w\.-]+@[\w\.-]+)", re.IGNORECASE),
        "birth_date": re.compile(r"(\d{2}\.\d{2}\.\d{4})"),
    }

    CONFIDENCE_RE = re.compile(r"\((\d+)/(\d+)\)")

    def __init__(self, source: Path | str, **options):
        super().__init__(source, **options)
        self.encoding: Optional[str] = options.get("encoding")
        self.strict = options.get("strict", False)

    def _detect_encoding(self, raw: bytes) -> str:
        """Use charset-normalizer for best-effort detection."""
        result = from_bytes(raw).best()
        if result and result.encoding:
            return result.encoding
        return "utf-8"

    def _normalize_phone(self, raw: str) -> Optional[str]:
        digits = re.sub(r"\D", "", raw)
        if len(digits) == 10 and digits.startswith("9"):
            return "+7" + digits
        if len(digits) == 11 and digits.startswith("8"):
            return "+7" + digits[1:]
        if len(digits) == 11 and digits.startswith("7"):
            return "+" + digits
        if 10 <= len(digits) <= 12:
            return "+" + digits
        return None

    def _normalize_snils(self, raw: str) -> Optional[str]:
        digits = re.sub(r"\D", "", raw)
        if len(digits) == 11:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:9]} {digits[9:]}"
        return None

    def _parse_block(self, block: str, source_file: str, block_id: str) -> Optional[PersonRecord]:
        rec = PersonRecord(source_file=source_file, source_block_id=block_id)

        # Full name + birth date often glued together
        name_match = self.FIELD_PATTERNS["full_name"].search(block)
        if name_match:
            name_part = name_match.group(1).strip()
            rec.full_name = re.sub(r"\s+", " ", name_part)
            # Try to extract birth date from the same line
            date_match = self.FIELD_PATTERNS["birth_date"].search(name_part)
            if date_match:
                d, m, y = map(int, date_match.group(1).split("."))
                rec.birth_date = date(y, m, d)

        # Phones
        for m in self.FIELD_PATTERNS["phone"].finditer(block):
            phone = self._normalize_phone(m.group(1))
            if phone:
                rec.phones.append(phone)

        # SNILS
        for m in self.FIELD_PATTERNS["snils"].finditer(block):
            sn = self._normalize_snils(m.group(1))
            if sn:
                rec.snils.append(sn)

        # Passport (very rough)
        for m in self.FIELD_PATTERNS["passport"].finditer(block):
            pas = re.sub(r"\s+", "", m.group(1))
            if 8 <= len(pas) <= 12:
                rec.passports.append(pas)

        # Email
        for m in self.FIELD_PATTERNS["email"].finditer(block):
            rec.emails.append(m.group(1).lower())

        # Crude confidence aggregation from (XX/YY) markers
        scores = self.CONFIDENCE_RE.findall(block)
        if scores:
            total = sum(int(x[1]) for x in scores)
            got = sum(int(x[0]) for x in scores)
            if total > 0:
                rec.confidence = got / total

        if rec.full_name or rec.phones or rec.emails:
            return rec
        return None

    def iter_records(self) -> Iterator[PersonRecord]:
        if not self.source.exists():
            raise FileNotFoundError(self.source)

        files = [self.source] if self.source.is_file() else list(self.source.glob("report_*.txt"))

        for file_path in files:
            raw = file_path.read_bytes()
            encoding = self.encoding or self._detect_encoding(raw)
            try:
                text = raw.decode(encoding, errors="replace")
            except Exception:
                text = raw.decode("utf-8", errors="replace")

            # Split into logical blocks (usually separated by long lines of = or ─)
            blocks = re.split(r"\n[═\-─]{10,}\n", text)

            for idx, block in enumerate(blocks):
                if len(block.strip()) < 30:
                    continue
                record = self._parse_block(block, str(file_path), f"{file_path.name}:{idx}")
                if record:
                    yield record
