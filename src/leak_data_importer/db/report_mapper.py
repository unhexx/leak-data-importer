"""
ReportMapper - maps ParsedReport into the PostgreSQL schema defined in db/schema.sql.

This layer handles:
- Insertion with proper normalization
- Handling of relationships (person -> documents, addresses, etc.)
- Source provenance
- Use of JSONB for flexible fields
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:
    psycopg2 = None

from leak_data_importer.parsers.dossier_models import ParsedReport, ParsedPerson


class ReportMapper:
    """
    Maps a ParsedReport into the database tables.
    """

    def __init__(self, dsn: str):
        if psycopg2 is None:
            raise ImportError("psycopg2-binary is required. Install with: pip install -e '.[db]'")

        self.dsn = dsn
        self.conn = None

    def __enter__(self):
        self.conn = psycopg2.connect(self.dsn)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()

    def insert_report(self, report: ParsedReport, created_by: Optional[str] = None) -> UUID:
        """
        Main entry point. Inserts the entire ParsedReport into DB.
        Returns the report UUID.
        """
        if not self.conn:
            raise RuntimeError("Mapper must be used as context manager")

        cur = self.conn.cursor()

        # 1. Insert report
        cur.execute("""
            INSERT INTO reports (filename, report_date, sources_count, records_count, 
                                 main_fio, main_birth_date, warnings, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (filename) DO UPDATE SET
                imported_at = now(),
                warnings = EXCLUDED.warnings
            RETURNING id
        """, (
            report.filename,
            report.report_date,
            report.sources_count,
            report.records_count,
            report.main_person.fio,
            report.main_person.birth_date,
            Json(report.warnings),
            created_by
        ))
        report_id = cur.fetchone()[0]

        # 2. Insert main person
        person_id = self._insert_person(cur, report_id, report.main_person)

        # 3. Documents
        for doc in report.documents:
            self._insert_document(cur, person_id, report_id, doc)

        # 4. Addresses
        for addr in report.addresses:
            self._insert_address(cur, person_id, report_id, addr)

        # 5. Employments
        for emp in report.employments:
            self._insert_employment(cur, person_id, report_id, emp)

        # 6. Connections
        for conn in report.connections:
            self._insert_connection(cur, person_id, report_id, conn)

        # 7. Vehicles (from main_person)
        for vehicle in report.main_person.vehicles:
            self._insert_vehicle(cur, person_id, report_id, vehicle)

        # 8. Events
        for event in report.border_events:
            self._insert_event(cur, person_id, report_id, event)

        # 9. Source findings (richest table)
        for idx, finding in enumerate(report.source_findings):
            self._insert_source_finding(cur, person_id, report_id, finding, idx)

        return report_id

    # --- Private insert helpers ---

    def _insert_person(self, cur, report_id: UUID, person: ParsedPerson) -> UUID:
        cur.execute("""
            INSERT INTO persons (
                report_id, fio, birth_date,
                main_passport, main_snils, main_inn, main_phone, main_email,
                passport_count, phone_count, email_count,
                extra_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            report_id,
            person.fio,
            person.birth_date,
            person.main_passport,
            person.snils,
            person.main_inn,
            person.main_phone,
            person.main_email,
            len(person.passports) + len(person.extra_passports),
            len(person.phones) + len(person.extra_phones),
            len(person.emails) + len(person.extra_emails),
            Json({
                "extra_phones": person.extra_phones,
                "extra_emails": person.extra_emails,
                "extra_passports": person.extra_passports,
                "extra_inns": person.extra_inns,
                "translit_name": getattr(person, 'translit_name', None),
            })
        ))
        return cur.fetchone()[0]

    def _insert_document(self, cur, person_id: UUID, report_id: UUID, doc: dict):
        doc_type = self._map_doc_type(doc.get("doc_type") or doc.get("doc_type_raw", "other"))

        cur.execute("""
            INSERT INTO documents (
                person_id, report_id, doc_type, number, series,
                issue_date, issuer, issuer_code, extra, source_section
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            person_id, report_id,
            doc_type,
            doc.get("number") or doc.get("number_raw"),
            doc.get("series"),
            doc.get("issue_date"),
            doc.get("fields", {}).get("Кем выдан") or doc.get("issuer"),
            doc.get("fields", {}).get("Код подразделения") or doc.get("issuer_code"),
            Json(doc.get("fields", {})),
            "ДОКУМЕНТЫ"
        ))

    def _insert_address(self, cur, person_id: UUID, report_id: UUID, addr: dict):
        cur.execute("""
            INSERT INTO addresses (person_id, report_id, address_type, full_text, extra, source)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            person_id, report_id,
            addr.get("type", "other"),
            addr.get("value") or addr.get("full_text"),
            Json(addr),
            addr.get("raw_label", "АДРЕСА")
        ))

    def _insert_employment(self, cur, person_id: UUID, report_id: UUID, emp: dict):
        cur.execute("""
            INSERT INTO employments (person_id, report_id, employer_name, position, 
                                     start_date, end_date, extra, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            person_id, report_id,
            emp.get("employer") or emp.get("employer_name"),
            emp.get("position"),
            emp.get("start_date"),
            emp.get("end_date"),
            Json(emp),
            "МЕСТО РАБОТЫ"
        ))

    def _insert_connection(self, cur, person_id: UUID, report_id: UUID, conn: dict):
        cur.execute("""
            INSERT INTO person_connections (person_id, report_id, related_fio, 
                                            connection_type, source, context, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            person_id, report_id,
            conn.get("related_fio"),
            conn.get("connection_type", "other"),
            conn.get("source"),
            Json(conn),
            conn.get("confidence", 0.7)
        ))

    def _insert_vehicle(self, cur, person_id: UUID, report_id: UUID, vehicle: dict):
        cur.execute("""
            INSERT INTO vehicles (person_id, report_id, vin, make_model, year, extra)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            person_id, report_id,
            vehicle.get("vin"),
            vehicle.get("make_model") or vehicle.get("model"),
            vehicle.get("year"),
            Json(vehicle)
        ))

    def _insert_event(self, cur, person_id: UUID, report_id: UUID, event: dict):
        cur.execute("""
            INSERT INTO events (person_id, report_id, event_type, event_date, 
                                flight_number, airline, departure, arrival, extra, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            person_id, report_id,
            event.get("event_type", "other"),
            event.get("date") or event.get("event_date"),
            event.get("flight_number"),
            event.get("airline"),
            event.get("departure"),
            event.get("arrival"),
            Json(event),
            event.get("source")
        ))

    def _insert_source_finding(self, cur, person_id: UUID, report_id: UUID, finding: dict, idx: int):
        cur.execute("""
            INSERT INTO source_findings (person_id, report_id, source_name, record_index, data, raw_text)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            person_id, report_id,
            finding.get("source_name", "Unknown"),
            idx,
            Json(finding.get("data", {})),
            finding.get("raw_text")
        ))

    # Helper
    def _map_doc_type(self, raw_type: str) -> str:
        raw = (raw_type or "").lower()
        if "паспорт" in raw and "загран" not in raw:
            return "passport_rf"
        if "загран" in raw or "иностран" in raw:
            return "foreign_passport"
        if "снилс" in raw:
            return "snils"
        if "инн" in raw:
            return "inn"
        if "водитель" in raw:
            return "driver_license"
        if "полис" in raw or "омс" in raw:
            return "oms_policy"
        return "other"
