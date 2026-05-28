"""Advanced importer for hybrid Russian 'report_*.txt' breach reports.

These files are often aggregations from multiple sources and contain several
different block formats mixed together:
  - Compact single-line style with (score/total)
  - Bulleted multi-value summary style with (xNN)
  - Rich detailed blocks with ESIA ID, addresses, registration dates, etc.

The goal of this parser is to be as robust as possible against real files
found in data/raw while never losing information.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterator, Optional

from charset_normalizer import from_bytes

from leak_data_importer.importers.base import BaseImporter
from leak_data_importer.models.person import PersonRecord
from leak_data_importer.graph import (
    Entity, ImportGraph, ImportGraphResult,
    make_person, make_phone, make_email, make_passport, make_snils,
    make_esia_account, make_address,
    has_phone, has_email, has_document, owns_account,
)


@dataclass
class ParsingStats:
    """Rich statistics for a parsing run. Essential for quality assessment of messy dumps."""
    total_blocks: int = 0
    records_extracted: int = 0
    by_strategy: dict[str, int] = field(default_factory=dict)
    low_confidence_records: int = 0
    files_processed: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "total_blocks": self.total_blocks,
            "records_extracted": self.records_extracted,
            "by_strategy": dict(self.by_strategy),
            "low_confidence_records": self.low_confidence_records,
            "files_processed": self.files_processed,
        }


class TxtReportImporter(BaseImporter):
    """Robust parser for the hybrid report_*.txt format found in real leaks."""

    name = "txt_report"
    supported_extensions = (".txt",)

    # Broad synonym map for fields commonly seen in these Russian dumps
    FIELD_SYNONYMS = {
        "full_name": {"фио", "фамилия имя отчество", "name", "ф.и.о", "ф и о"},
        "phone": {"телефон", "мобильный", "тел", "phone", "моб.", "мобильник"},
        "passport": {"паспорт", "пасп", "passport", "серия и номер", "паспорт рф"},
        "snils": {"снилс", "snils", "страховое свидетельство"},
        "email": {"email", "e-mail", "эл. почта", "почта", "e mail"},
        "esia": {"esia id", "esia", "есия", "госуслуги"},
        "birth": {"дата рождения", "д.р.", "родился", "дата рожд"},
    }

    CONF_SCORE = re.compile(r"\((\d+)\s*/\s*(\d+)\)")
    CONF_X = re.compile(r"\(x\s*(\d+)\)", re.IGNORECASE)
    DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")

    def __init__(self, source: Path | str, **options):
        super().__init__(source, **options)
        self.encoding: Optional[str] = options.get("encoding")
        self.min_block_len = options.get("min_block_len", 22)

    # ---------- Low level ----------

    def _read_text(self, path: Path) -> str:
        raw = path.read_bytes()
        if self.encoding:
            return raw.decode(self.encoding, errors="replace")
        result = from_bytes(raw).best()
        enc = result.encoding if result else "utf-8"
        return raw.decode(enc, errors="replace")

    def _normalize_phone(self, raw: str) -> Optional[str]:
        digits = re.sub(r"[^\d]", "", raw)
        if len(digits) < 10:
            return None
        if len(digits) == 10 and digits[0] == "9":
            return "+7" + digits
        if len(digits) == 11 and digits[0] in "78":
            return "+7" + digits[1:]
        if 10 <= len(digits) <= 12:
            return "+" + digits
        return None

    def _normalize_snils(self, raw: str) -> Optional[str]:
        d = re.sub(r"\D", "", raw)
        if len(d) == 11:
            return f"{d[:3]}-{d[3:6]}-{d[6:9]} {d[9:]}"
        return None

    def _parse_date(self, text: str) -> Optional[date]:
        m = self.DATE_RE.search(text)
        if m:
            try:
                return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except ValueError:
                pass
        return None

    def _extract_confidence(self, text: str) -> Optional[float]:
        scores = self.CONF_SCORE.findall(text)
        if scores:
            got = sum(int(a) for a, b in scores)
            total = sum(int(b) for a, b in scores)
            return round(got / total, 3) if total > 0 else None
        xscores = [int(x) for x in self.CONF_X.findall(text)]
        if xscores:
            return min(0.92, sum(xscores) / (len(xscores) * 25 + 5))
        return None

    # ---------- Block strategies ----------

    def _extract_name_birth(self, block: str) -> tuple[Optional[str], Optional[date]]:
        patterns = [
            r"ФИО[:：]?\s*([А-ЯЁа-яё][А-ЯЁа-яё\-]+(?:\s+[А-ЯЁа-яё\-]+){1,3})\s+(\d{2}\.\d{2}\.\d{4})",
            r"ФИО[:：]?\s*([А-ЯЁа-яё][А-ЯЁа-яё\-]+(?:\s+[А-ЯЁа-яё\-]+){1,3})",
            r"\[.*?x\d+.*?\]\s*-\s*([А-ЯЁа-яё][А-ЯЁа-яё\-]+(?:\s+[А-ЯЁа-яё\-]+){1,3})\s+(\d{2}\.\d{2}\.\d{4})",
        ]
        for p in patterns:
            m = re.search(p, block, re.IGNORECASE)
            if m:
                name = re.sub(r"\s+", " ", m.group(1)).strip().title()
                birth = self._parse_date(m.group(0))
                return name, birth
        return None, None

    def _get_values_for_label(self, block: str, label: str) -> list[str]:
        """Handles both 'Label: value' and bulleted styles."""
        vals = []
        # direct
        for m in re.finditer(rf"{re.escape(label)}[:：]?\s*([^\n(]+?)(?:\s*\(|\n|$)", block, re.IGNORECASE):
            v = m.group(1).strip(" -•\t")
            if v and len(v) > 1:
                vals.append(v)
        # bulleted under label
        for m in re.finditer(rf"{re.escape(label)}[:：]?\s*\n(?:\s*[-•]\s*([^\n(]+))", block, re.IGNORECASE):
            v = m.group(1).strip()
            if v:
                vals.append(v)
        return vals

    def _parse_compact_bulleted(self, block: str, rec: PersonRecord) -> bool:
        name, birth = self._extract_name_birth(block)
        if name: rec.full_name = name
        if birth: rec.birth_date = birth

        for v in self._get_values_for_label(block, "телефон") + self._get_values_for_label(block, "мобильный"):
            p = self._normalize_phone(v)
            if p: rec.phones.append(p)

        for v in self._get_values_for_label(block, "email") + self._get_values_for_label(block, "почта"):
            if "@" in v: rec.emails.append(v.lower())

        for v in self._get_values_for_label(block, "паспорт"):
            clean = re.sub(r"\s+", "", v)
            if 8 <= len(clean) <= 12: rec.passports.append(clean)

        for v in self._get_values_for_label(block, "снилс"):
            sn = self._normalize_snils(v)
            if sn: rec.snils.append(sn)

        for v in self._get_values_for_label(block, "esia"):
            rec.esia_id = v.strip() or rec.esia_id

        rec.confidence = self._extract_confidence(block)
        rec.parsing_strategy = "compact_bulleted"
        return bool(rec.full_name or rec.phones or rec.emails)

    def _parse_rich(self, block: str, rec: PersonRecord) -> bool:
        name, birth = self._extract_name_birth(block)
        if name: rec.full_name = name
        if birth: rec.birth_date = birth

        # Greedy extraction for rich blocks
        for canon, variants in self.FIELD_SYNONYMS.items():
            for var in variants:
                for v in self._get_values_for_label(block, var):
                    if canon == "phone":
                        p = self._normalize_phone(v)
                        if p: rec.phones.append(p)
                    elif canon == "email" and "@" in v:
                        rec.emails.append(v.lower())
                    elif canon == "snils":
                        sn = self._normalize_snils(v)
                        if sn: rec.snils.append(sn)
                    elif canon == "passport":
                        c = re.sub(r"\s+", "", v)
                        if 8 <= len(c) <= 12: rec.passports.append(c)
                    elif canon == "esia":
                        rec.esia_id = v.strip()

        # Catch everything else interesting
        extra_keys = ["адрес", "дата регистрации", "дата авторизации", "ip", "iccid", "imsi", "vin", "дата"]
        for key in extra_keys:
            vals = self._get_values_for_label(block, key)
            if vals:
                rec.other_ids.setdefault(key, []).extend(vals)

        rec.confidence = self._extract_confidence(block) or 0.55
        rec.parsing_strategy = "rich_detailed"
        return bool(rec.full_name or rec.phones)

    def _parse_block(self, block: str, source_file: str, block_id: str) -> Optional[PersonRecord]:
        if len(block.strip()) < self.min_block_len:
            return None

        rec = PersonRecord(source_file=source_file, source_block_id=block_id)

        # Try strategies (order matters for these particular files)
        ok = self._parse_compact_bulleted(block, rec) or self._parse_rich(block, rec)

        # Dedup + cleanup
        rec.phones = sorted(set(rec.phones))
        rec.emails = sorted(set(rec.emails))
        rec.passports = sorted(set(rec.passports))
        rec.snils = sorted(set(rec.snils))

        if ok and (rec.full_name or rec.phones or rec.emails):
            return rec
        return None

    # ---------- Public interface ----------

    def iter_records(self) -> Iterator[PersonRecord]:
        if not self.source.exists():
            raise FileNotFoundError(self.source)

        files = [self.source] if self.source.is_file() else list(self.source.glob("report_*.txt"))

        for fp in files:
            text = self._read_text(fp)
            blocks = re.split(r"\n[═─=+\-]{5,}\n", text)
            for idx, block in enumerate(blocks):
                rec = self._parse_block(block, str(fp), f"{fp.name}:{idx}")
                if rec:
                    yield rec

    def parse_with_stats(self) -> tuple[list[PersonRecord], ParsingStats]:
        """Best method for real work — returns records + detailed quality stats."""
        stats = ParsingStats()
        records: list[PersonRecord] = []

        files = [self.source] if self.source.is_file() else list(self.source.glob("report_*.txt"))
        stats.files_processed = [str(f) for f in files]

        for fp in files:
            text = self._read_text(fp)
            blocks = [b for b in re.split(r"\n[═─=+\-]{5,}\n", text) if len(b.strip()) > 20]
            stats.total_blocks += len(blocks)

            for idx, block in enumerate(blocks):
                rec = self._parse_block(block, str(fp), f"{fp.name}:{idx}")
                if rec:
                    stats.records_extracted += 1
                    key = rec.parsing_strategy or "unknown"
                    stats.by_strategy[key] = stats.by_strategy.get(key, 0) + 1
                    if (rec.confidence or 1.0) < 0.35:
                        stats.low_confidence_records += 1
                    records.append(rec)

        return records, stats

    # ==================== GRAPH / ENTITY MODE (for connection analysis) ====================

    def parse_to_graph(self) -> "ImportGraphResult":
        """
        Returns data in graph form (entities + relationships).

        This is the recommended output when your goal is to search for
        connections between people, phones, documents, accounts, etc.
        """
        from leak_data_importer.graph import ImportGraph
        from leak_data_importer.graph.result import ImportGraphResult
        from leak_data_importer.graph import (
            make_person, make_phone, make_email, make_passport,
            make_snils, make_esia_account,
            has_phone, has_email, has_document, owns_account,
        )

        flat_records, stats = self.parse_with_stats()

        graph = ImportGraph()
        graph.metadata = {
            "source": str(self.source),
            "parser": "txt_report.v2.graph",
        }

        entity_by_key: dict[str, Entity] = {}

        def get_or_create_person(rec: PersonRecord) -> Entity | None:
            if not rec.full_name:
                return None
            # Each record with a distinct name gets its own Person entity (for now).
            # Later we can add fuzzy deduplication.
            key = f"person:{rec.source_block_id}:{rec.full_name.lower().replace(' ', '_')[:50]}"
            if key in entity_by_key:
                return entity_by_key[key]

            p = make_person(
                full_name=rec.full_name,
                birth_date=rec.birth_date,
                source_ref=rec.source_block_id,
            )
            entity_by_key[key] = p
            graph.entities.append(p)
            return p

        for rec in flat_records:
            person = get_or_create_person(rec)
            if not person:
                continue

            # Phones
            for num in rec.phones:
                key = "phone:" + num
                if key not in entity_by_key:
                    ph = make_phone(num, source_ref=rec.source_block_id)
                    entity_by_key[key] = ph
                    graph.entities.append(ph)
                graph.relationships.append(has_phone(person.id, entity_by_key[key].id, source=rec.source_block_id))

            # Emails
            for addr in rec.emails:
                key = "email:" + addr.lower()
                if key not in entity_by_key:
                    em = make_email(addr, source_ref=rec.source_block_id)
                    entity_by_key[key] = em
                    graph.entities.append(em)
                graph.relationships.append(has_email(person.id, entity_by_key[key].id, source=rec.source_block_id))

            # Documents
            for pas in rec.passports:
                key = "passport:" + pas
                if key not in entity_by_key:
                    doc = make_passport(pas, source_ref=rec.source_block_id)
                    entity_by_key[key] = doc
                    graph.entities.append(doc)
                graph.relationships.append(has_document(person.id, entity_by_key[key].id, "passport", source=rec.source_block_id))

            for sn in rec.snils:
                key = "snils:" + sn
                if key not in entity_by_key:
                    doc = make_snils(sn, source_ref=rec.source_block_id)
                    entity_by_key[key] = doc
                    graph.entities.append(doc)
                graph.relationships.append(has_document(person.id, entity_by_key[key].id, "snils", source=rec.source_block_id))

            if rec.esia_id:
                key = "esia:" + rec.esia_id
                if key not in entity_by_key:
                    acc = make_esia_account(rec.esia_id, source_ref=rec.source_block_id)
                    entity_by_key[key] = acc
                    graph.entities.append(acc)
                graph.relationships.append(owns_account(person.id, entity_by_key[key].id, "esia", source=rec.source_block_id))

        result = ImportGraphResult(
            graph=graph,
            flat_records=[r.to_dict() for r in flat_records],
            stats={
                "parser_stats": stats.as_dict(),
                "entities": len(graph.entities),
                "relationships": len(graph.relationships),
            },
        )
        return result
