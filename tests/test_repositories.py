from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from leak_data_importer.db.models import Base, DocType, Document, Person, PersonLink, Report
from leak_data_importer.db.repositories.document import DocumentRepository
from leak_data_importer.db.repositories.person import PersonRepository
from leak_data_importer.db.repositories.person_link import PersonLinkRepository
from leak_data_importer.db.repositories.report import ReportRepository


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _seed_report(session: Session, filename: str, status: str = "imported", main_fio: str = "Иванов Иван") -> Report:
    report = Report(
        id=uuid4(),
        filename=filename,
        imported_at=datetime.utcnow(),
        status=status,
        main_fio=main_fio,
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    return report


def _seed_person(
    session: Session,
    report_id,
    fio: str,
    birth_date: date | None = None,
    passport: str | None = None,
    snils: str | None = None,
    inn: str | None = None,
) -> Person:
    person = Person(
        id=uuid4(),
        report_id=report_id,
        fio=fio,
        birth_date=birth_date,
        main_passport=passport,
        main_snils=snils,
        main_inn=inn,
    )
    session.add(person)
    session.commit()
    session.refresh(person)
    return person


def _seed_document(
    session: Session,
    person_id,
    report_id,
    doc_type: DocType,
    number: str,
    series: str | None = None,
    issuer: str | None = None,
    status: str | None = "active",
    expiry_date: date | None = None,
) -> Document:
    doc = Document(
        id=uuid4(),
        person_id=person_id,
        report_id=report_id,
        doc_type=doc_type,
        number=number,
        series=series,
        issuer=issuer,
        status=status,
        expiry_date=expiry_date,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


class TestPersonRepository:
    def test_get_by_fio(self, session: Session) -> None:
        report = _seed_report(session, "r1.txt")
        p1 = _seed_person(session, report.id, "Иванов Иван Иванович")
        _seed_person(session, report.id, "Петров Петр Петрович")

        repo = PersonRepository(session)
        results = repo.get_by_fio("Иванов Иван Иванович")

        assert len(results) == 1
        assert results[0].id == p1.id

    def test_get_by_fio_like(self, session: Session) -> None:
        report = _seed_report(session, "r2.txt")
        _seed_person(session, report.id, "Иванов Иван Иванович")
        _seed_person(session, report.id, "Иванова Анна Сергеевна")

        repo = PersonRepository(session)
        results = repo.get_by_fio_like("Иванов", limit=10)

        assert len(results) == 2

    def test_get_by_birth_date_and_documents(self, session: Session) -> None:
        report = _seed_report(session, "r3.txt")
        target_date = date(1990, 1, 1)
        p1 = _seed_person(
            session,
            report.id,
            "Сидоров Сидор Сидорович",
            birth_date=target_date,
            passport="4506123456",
            snils="123-456-789 01",
            inn="1234567890",
        )

        repo = PersonRepository(session)
        assert repo.get_by_birth_date(target_date)[0].id == p1.id
        assert repo.get_by_passport("4506123456")[0].id == p1.id
        assert repo.get_by_snils("123-456-789 01")[0].id == p1.id
        assert repo.get_by_inn("1234567890")[0].id == p1.id
        assert repo.get_by_report_id(report.id)[0].id == p1.id


class TestDocumentRepository:
    def test_get_by_doc_type_and_number(self, session: Session) -> None:
        report = _seed_report(session, "d1.txt")
        person = _seed_person(session, report.id, "Тест Тест")
        doc = _seed_document(
            session,
            person.id,
            report.id,
            DocType.PASSPORT_RF,
            "4506123456",
            series="4506",
            issuer="МВД Москва",
        )

        repo = DocumentRepository(session)
        results = repo.get_by_doc_type_and_number(DocType.PASSPORT_RF, "4506123456")

        assert len(results) == 1
        assert results[0].id == doc.id

    def test_get_by_person_report_type_series_issuer(self, session: Session) -> None:
        report = _seed_report(session, "d2.txt")
        person = _seed_person(session, report.id, "Тест Документ")
        doc = _seed_document(
            session,
            person.id,
            report.id,
            DocType.SNILS,
            "12345678901",
            series="123",
            issuer="ПФР",
        )

        repo = DocumentRepository(session)
        assert repo.get_by_person_id(person.id)[0].id == doc.id
        assert repo.get_by_report_id(report.id)[0].id == doc.id
        assert repo.get_by_type(DocType.SNILS)[0].id == doc.id
        assert repo.get_by_series("123")[0].id == doc.id
        assert repo.get_by_issuer("ПФР")[0].id == doc.id

    def test_get_active(self, session: Session) -> None:
        report = _seed_report(session, "d3.txt")
        person = _seed_person(session, report.id, "Актив Док")
        active_doc = _seed_document(session, person.id, report.id, DocType.INN, "1234567890", status="active")
        _seed_document(session, person.id, report.id, DocType.OTHER, "ABC123", status="expired", expiry_date=date(2020, 1, 1))

        repo = DocumentRepository(session)
        active = repo.get_active()

        assert any(d.id == active_doc.id for d in active)


class TestReportRepository:
    def test_report_queries(self, session: Session) -> None:
        older = _seed_report(session, "old.txt", status="imported", main_fio="Иванов Иван")
        newer = _seed_report(session, "new.txt", status="parsed", main_fio="Петров Петр")

        repo = ReportRepository(session)

        by_filename = repo.get_by_filename("old.txt")
        assert by_filename is not None
        assert by_filename.id == older.id

        by_status = repo.get_by_status("parsed")
        assert len(by_status) == 1
        assert by_status[0].id == newer.id

        by_fio = repo.get_by_main_fio("Иванов Иван")
        assert len(by_fio) == 1
        assert by_fio[0].id == older.id

        recent = repo.get_recent(limit=1)
        assert len(recent) == 1


class TestPersonLinkRepository:
    def test_create_and_get_by_persons(self, session: Session) -> None:
        report = _seed_report(session, "pl1.txt")
        p1 = _seed_person(session, report.id, "А")
        p2 = _seed_person(session, report.id, "Б")

        repo = PersonLinkRepository(session)
        link = repo.create_link(
            person_a_id=p1.id,
            person_b_id=p2.id,
            confidence=0.9,
            match_strategy="exact_passport",
        )

        assert isinstance(link, PersonLink)

        same = repo.get_by_persons(p1.id, p2.id)
        reverse = repo.get_by_persons(p2.id, p1.id)

        assert same is not None
        assert reverse is not None
        assert same.id == link.id
        assert reverse.id == link.id

    def test_filters_and_review(self, session: Session) -> None:
        report = _seed_report(session, "pl2.txt")
        p1 = _seed_person(session, report.id, "П1")
        p2 = _seed_person(session, report.id, "П2")
        p3 = _seed_person(session, report.id, "П3")

        repo = PersonLinkRepository(session)
        l1 = repo.create_link(p1.id, p2.id, 0.92, "exact_passport")
        l2 = repo.create_link(p1.id, p3.id, 0.55, "fuzzy_fio")

        by_a = repo.get_by_person_a(p1.id)
        by_b = repo.get_by_person_b(p3.id)
        by_conf = repo.get_by_confidence_range(0.5, 0.6)
        unreviewed = repo.get_unreviewed()
        by_strategy = repo.search_by_strategy("fuzzy_fio")

        assert len(by_a) >= 2
        assert len(by_b) == 1
        assert any(x.id == l2.id for x in by_conf)
        assert any(x.id == l1.id for x in unreviewed)
        assert len(by_strategy) == 1
        assert by_strategy[0].id == l2.id

        reviewed = repo.mark_reviewed(
            link_id=l1.id,
            is_confirmed=True,
            reviewed_by="qa-user",
            notes="verified",
        )
        assert reviewed is not None
        assert reviewed.is_reviewed is True
        assert reviewed.is_confirmed is True
        assert reviewed.reviewed_by == "qa-user"

        confirmed = repo.get_confirmed()
        assert any(x.id == l1.id for x in confirmed)
