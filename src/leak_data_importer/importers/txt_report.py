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
from collections import defaultdict
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

    # Broad + aggressive synonym map for rich blocks in real dumps
    FIELD_SYNONYMS = {
        "full_name": {"фио", "фамилия имя отчество", "name", "ф.и.о", "ф и о"},
        "phone": {"телефон", "мобильный", "тел", "phone", "моб.", "мобильник"},
        "passport": {"паспорт", "пасп", "passport", "серия и номер", "паспорт рф", "загран"},
        "snils": {"снилс", "snils", "страховое свидетельство"},
        "email": {"email", "e-mail", "эл. почта", "почта", "e mail"},
        "esia": {"esia id", "esia", "есия", "госуслуги"},
        "birth": {"дата рождения", "д.р.", "родился", "дата рожд"},
        "inn": {"инн", "inn"},
        "translit_name": {"??? ?? ??????????", "фио латиница", "name eng", "translit"},
        "vin": {"vin ?????", "vin"},
        "car_model": {"модель авто", "марка", "авто", "тс"},
        "airport_code": {"??? ????????? ??????", "??? ????????? ????????"},
    }

    CONF_SCORE = re.compile(r"\((\d+)\s*/\s*(\d+)\)")
    CONF_X = re.compile(r"\(x\s*(\d+)\)", re.IGNORECASE)
    DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")
    SOURCE_TAG_RE = re.compile(r"\[([^\]]+?)\s*[xх]\s*\d+\]", re.IGNORECASE)  # supports both Latin and Cyrillic 'x'

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

    # ==================== AGGRESSIVE RICH BLOCK PARSERS ====================

    def _extract_translit_name(self, block: str) -> Optional[str]:
        for variant in self.FIELD_SYNONYMS.get("translit_name", set()):
            for val in self._get_values_for_label(block, variant):
                if re.search(r"[A-Z]{3,}", val):  # looks like translit
                    return val.strip()
        return None

    def _extract_addresses_aggressive(self, block: str) -> list[dict]:
        """Capture different kinds of addresses with context."""
        addresses = []
        addr_variants = ["адрес", "????? ? ??????", "????? ??????"]

        for variant in addr_variants:
            for val in self._get_values_for_label(block, variant):
                addr_type = "unknown"
                if "регистрац" in variant.lower() or "пропис" in variant.lower():
                    addr_type = "registration"
                elif "прожив" in variant.lower():
                    addr_type = "residence"
                addresses.append({
                    "type": addr_type,
                    "value": val.strip(),
                    "raw_label": variant
                })
        return addresses

    def _extract_registration_events(self, block: str) -> list[dict]:
        """Extract registration / authorization events with dates, IPs, systems."""
        events = []
        date_variants = [
            "дата регистрации", "дата авторизации", "???? ?????? ????????",
            "???? ???????????", "дата выдачи", "дата регистрации в"
        ]

        for variant in date_variants:
            for val in self._get_values_for_label(block, variant):
                event = {
                    "raw_label": variant,
                    "date": val.strip()
                }
                # Try to extract IP if present in same line or nearby
                ip_match = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", val)
                if ip_match:
                    event["ip"] = ip_match.group(1)
                events.append(event)
        return events

    def _extract_other_ids_aggressive(self, block: str) -> dict[str, list[str]]:
        """Capture INN, foreign IDs, system IDs, etc."""
        ids: dict[str, list[str]] = defaultdict(list)

        for canon, variants in self.FIELD_SYNONYMS.items():
            if canon in ("inn", "foreign_id"):
                for var in variants:
                    for val in self._get_values_for_label(block, var):
                        ids[canon].append(val.strip())

        # Generic "ID ..." fields
        for line in block.splitlines():
            if re.match(r"ID\s", line, re.IGNORECASE):
                val = line.split(":", 1)[-1].strip()
                if val:
                    ids["other_system_id"].append(val)

        return dict(ids)

    def _extract_vehicle_info(self, block: str) -> dict:
        info = {}
        for val in self._get_values_for_label(block, "vin"):
            if len(val) > 10:
                info["vin"] = val.strip()
        for val in self._get_values_for_label(block, "car_model"):
            info["model"] = val.strip()
        return info

    def _detect_data_source(self, block: str) -> Optional[str]:
        """Extract source tag from block header. Looks for patterns like [Что-то x3]."""
        # Look in first 300 chars of the block
        head = block[:300]
        
        # Try the strict regex first
        m = self.SOURCE_TAG_RE.search(head)
        if m:
            return m.group(1).strip()
        
        # Fallback: any [text] at the beginning of a line in the header area
        for line in head.splitlines()[:4]:
            line = line.strip()
            if line.startswith("[") and "]" in line[:40]:
                tag = line[1:line.find("]")].strip()
                # Clean common suffixes like " x3"
                tag = re.sub(r"\s*x\s*\d+$", "", tag, flags=re.I).strip()
                if tag and len(tag) > 1:
                    return tag
        return None

    def _promote_from_raw_data(self, rec: PersonRecord):
        """Aggressively classify and move valuable fields out of raw_data into structured slots.
        Uses both key hints and value patterns (more reliable for these messy dumps).
        """
        if not rec.raw_data:
            return

        to_remove = []

        for key, values in list(rec.raw_data.items()):
            key_lower = key.lower()

            for val in values:
                v = val.strip()

                # VIN (17 chars, mostly alphanum)
                if re.match(r"^[A-Z0-9]{17}$", v.replace(" ", "").upper()):
                    rec.vehicle_info["vin"] = v
                    to_remove.append(key)
                    continue

                # Looks like INN
                digits = re.sub(r"\D", "", v)
                if len(digits) in (10, 12):
                    rec.other_ids.setdefault("inn", []).append(v)
                    to_remove.append(key)
                    continue

                # Looks like a date
                if re.match(r"\d{2}\.\d{2}\.\d{4}", v):
                    rec.registration_events.append({"date": v, "raw_label": key})
                    to_remove.append(key)
                    continue

                # Looks like address (contains street-like words or numbers + city)
                if any(w in v.lower() for w in ["ул.", "ул ", "д.", "кв.", "г.", "обл."]) or len(v) > 25:
                    rec.addresses.append({"type": "unknown", "value": v, "raw_label": key})
                    to_remove.append(key)
                    continue

                # IP address
                if re.match(r"\d{1,3}(\.\d{1,3}){3}", v):
                    rec.registration_events.append({"ip": v, "raw_label": key})
                    to_remove.append(key)
                    continue

                # Translit name (lots of uppercase Latin letters)
                if re.search(r"[A-Z]{4,}.*[A-Z]{4,}", v) and len(v) > 8:
                    rec.translit_name = v
                    to_remove.append(key)
                    continue

                # Car model hints
                if any(m in v.upper() for m in ["MAZDA", "TOYOTA", "BMW", "MERCEDES", "CX-", "KIA"]):
                    rec.vehicle_info.setdefault("models", []).append(v)
                    to_remove.append(key)
                    continue

        # Remove duplicates
        for key in set(to_remove):
            rec.raw_data.pop(key, None)

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

        # Standard fields
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
                    elif canon == "translit_name":
                        rec.translit_name = v.strip()
                    elif canon == "inn":
                        rec.other_ids.setdefault("inn", []).append(v.strip())
                    elif canon == "vin":
                        rec.vehicle_info["vin"] = v.strip()

        # === AGGRESSIVE RICH-SPECIFIC EXTRACTION ===
        rec.translit_name = rec.translit_name or self._extract_translit_name(block)
        rec.addresses.extend(self._extract_addresses_aggressive(block))
        rec.registration_events.extend(self._extract_registration_events(block))
        rec.other_ids.update(self._extract_other_ids_aggressive(block))

        vehicle = self._extract_vehicle_info(block)
        if vehicle:
            rec.vehicle_info.update(vehicle)

        # Final fallback for anything still missed (kept for lossless guarantee)
        # We already captured everything in raw_data at the beginning of _parse_block

        # === POST-PROCESSING: Aggressively promote from raw_data into structured fields ===
        self._promote_from_raw_data(rec)

        rec.confidence = self._extract_confidence(block) or 0.55
        rec.parsing_strategy = "rich_detailed"
        return bool(rec.full_name or rec.phones)

    def _greedy_extract_fields(self, block: str) -> dict[str, list[str]]:
        """Capture EVERY 'Key: value' pair in the block. Nothing is lost."""
        fields: dict[str, list[str]] = defaultdict(list)
        for line in block.splitlines():
            if ':' not in line:
                continue
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip()
            if key and val and len(key) < 80:
                fields[key].append(val)
        return dict(fields)

    def _parse_block(self, block: str, source_file: str, block_id: str, data_source: Optional[str] = None) -> Optional[PersonRecord]:
        if len(block.strip()) < self.min_block_len:
            return None

        rec = PersonRecord(source_file=source_file, source_block_id=block_id, data_source=data_source)

        # Capture absolutely everything first (lossless)
        rec.raw_data = self._greedy_extract_fields(block)

        # Then do best-effort structured extraction
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
                source_tag = self._detect_data_source(block)
                rec = self._parse_block(block, str(fp), f"{fp.name}:{idx}", data_source=source_tag)
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
                source_tag = self._detect_data_source(block)
                rec = self._parse_block(block, str(fp), f"{fp.name}:{idx}", data_source=source_tag)
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
            make_snils, make_esia_account, make_address, make_vehicle,
            has_phone, has_email, has_document, owns_account, registered_at,
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
            if rec.data_source:
                p.properties["data_source"] = rec.data_source
            # Attach all raw captured fields so nothing is lost
            if rec.raw_data:
                p.properties.setdefault("raw_fields", {}).update(rec.raw_data)
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

            # Addresses from rich blocks
            for addr in rec.addresses:
                addr_str = addr.get("value") or addr.get("address")
                if addr_str:
                    ad = make_address(addr_str, source_ref=rec.source_block_id)
                    if ad.canonical_key not in entity_by_key:
                        entity_by_key[ad.canonical_key] = ad
                        graph.entities.append(ad)
                    graph.relationships.append(registered_at(person.id, ad.id, source=rec.source_block_id))

            # Vehicle
            if rec.vehicle_info.get("vin"):
                vin = rec.vehicle_info["vin"]
                key = "vehicle:" + vin
                if key not in entity_by_key:
                    veh = make_vehicle(vin, source_ref=rec.source_block_id)
                    entity_by_key[key] = veh
                    graph.entities.append(veh)
                # We could add a relationship here if needed later

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
