"""
Интеграционные тесты для графового слоя и Neo4j экспорта.

Эти тесты проверяют создание сущностей, связей и батч-экспорт в Neo4j.
"""

import pytest
from datetime import date

from leak_data_importer.graph import (
    Entity,
    Relationship,
    ImportGraph,
    make_person,
    make_phone,
    make_email,
    make_passport,
    make_snils,
    make_esia_account,
    make_address,
    make_vehicle,
    make_event,
    make_location,
    make_document,
    has_phone,
    has_email,
    has_document,
    registered_at,
    owns_account,
    event_at,
    located_at,
    issued_to,
    related_to,
    ImportGraphResult,
)


class TestEntityFactories:
    """Тесты фабрик сущностей."""

    def test_make_person(self):
        """Тест создания персоны."""
        person = make_person(
            full_name="Иванов Иван Иванович",
            birth_date=date(1985, 3, 15),
            source_ref="test_block_1",
        )
        assert person.type == "person"
        assert person.properties["full_name"] == "Иванов Иван Иванович"
        assert person.properties["birth_date"] == "1985-03-15"
        assert person.source_refs == ["test_block_1"]
        assert person.canonical_key is not None

    def test_make_phone(self):
        """Тест создания телефона."""
        phone = make_phone("+79161234567", source_ref="test_block_1")
        assert phone.type == "phone_number"
        assert phone.properties["number"] == "+79161234567"
        assert phone.canonical_key == "+79161234567"

    def test_make_email(self):
        """Тест создания email."""
        email = make_email("test@example.com", source_ref="test_block_1")
        assert email.type == "email_address"
        assert email.properties["address"] == "test@example.com"
        assert email.canonical_key == "test@example.com"

    def test_make_passport(self):
        """Тест создания паспорта."""
        passport = make_passport("45 06 123456", source_ref="test_block_1")
        assert passport.type == "passport"
        assert passport.properties["number"] == "45 06 123456"

    def test_make_snils(self):
        """Тест создания СНИЛС."""
        snils = make_snils("123-456-789 01", source_ref="test_block_1")
        assert snils.type == "snils"
        assert snils.properties["number"] == "123-456-789 01"

    def test_make_esia_account(self):
        """Тест создания аккаунта ЕСИА."""
        esia = make_esia_account("1234567890", source_ref="test_block_1")
        assert esia.type == "esia_account"
        assert esia.properties["esia_id"] == "1234567890"

    def test_make_address(self):
        """Тест создания адреса."""
        address = make_address("г. Москва, ул. Ленина 1", source_ref="test_block_1")
        assert address.type == "physical_address"
        assert address.properties["address"] == "г. Москва, ул. Ленина 1"

    def test_make_vehicle(self):
        """Тест создания ТС."""
        vehicle = make_vehicle("XW8AN52Y9C P12345", source_ref="test_block_1")
        assert vehicle.type == "vehicle"
        assert vehicle.properties["vin"] == "XW8AN52Y9C P12345"

    def test_make_event(self):
        """Тест создания события."""
        event = make_event(
            event_type="registration",
            name="Регистрация на госуслугах",
            date="2024-01-15",
            source_ref="test_block_1",
        )
        assert event.type == "event"
        assert event.properties["event_type"] == "registration"
        assert event.properties["name"] == "Регистрация на госуслугах"
        assert event.properties["date"] == "2024-01-15"
        assert event.canonical_key is not None

    def test_make_location(self):
        """Тест создания местоположения."""
        location = make_location(
            location_type="registration",
            address="г. Москва, ул. Ленина 1",
            coordinates=(55.7558, 37.6173),
            source_ref="test_block_1",
        )
        assert location.type == "location"
        assert location.properties["location_type"] == "registration"
        assert location.properties["address"] == "г. Москва, ул. Ленина 1"
        assert location.properties["lat"] == 55.7558
        assert location.properties["lon"] == 37.6173

    def test_make_document(self):
        """Тест создания документа."""
        doc = make_document(
            doc_type="certificate",
            number="123456",
            issued_by="МВД",
            issue_date="2020-01-15",
            source_ref="test_block_1",
        )
        assert doc.type == "document"
        assert doc.properties["document_type"] == "certificate"
        assert doc.properties["number"] == "123456"
        assert doc.properties["issued_by"] == "МВД"
        assert doc.properties["issue_date"] == "2020-01-15"


class TestRelationshipFactories:
    """Тесты фабрик связей."""

    def test_has_phone(self):
        """Тест связи has_phone."""
        person_id = "person_1"
        phone_id = "phone_1"
        rel = has_phone(person_id, phone_id, source="test_block_1")
        assert rel.from_id == person_id
        assert rel.to_id == phone_id
        assert rel.type == "has_phone"

    def test_has_email(self):
        """Тест связи has_email."""
        person_id = "person_1"
        email_id = "email_1"
        rel = has_email(person_id, email_id, source="test_block_1")
        assert rel.type == "has_email"

    def test_has_document(self):
        """Тест связи has_document."""
        person_id = "person_1"
        doc_id = "passport_1"
        rel = has_document(person_id, doc_id, "passport", source="test_block_1")
        assert rel.type == "has_document"
        assert rel.properties["document_type"] == "passport"

    def test_registered_at(self):
        """Тест связи registered_at."""
        person_id = "person_1"
        address_id = "address_1"
        rel = registered_at(person_id, address_id, date="2020-01-15", source="test_block_1")
        assert rel.type == "registered_at"
        assert rel.properties["date"] == "2020-01-15"

    def test_owns_account(self):
        """Тест связи owns_account."""
        person_id = "person_1"
        account_id = "esia_1"
        rel = owns_account(person_id, account_id, "esia", source="test_block_1")
        assert rel.type == "owns_account"
        assert rel.properties["account_type"] == "esia"

    def test_event_at(self):
        """Тест связи event_at."""
        person_id = "person_1"
        event_id = "event_1"
        rel = event_at(person_id, event_id, date="2024-01-15", source="test_block_1")
        assert rel.type == "event_at"
        assert rel.properties["date"] == "2024-01-15"

    def test_located_at(self):
        """Тест связи located_at."""
        person_id = "person_1"
        location_id = "location_1"
        rel = located_at(person_id, location_id, "residence", date="2020-01-15", source="test_block_1")
        assert rel.type == "located_at"
        assert rel.properties["location_type"] == "residence"

    def test_issued_to(self):
        """Тест связи issued_to."""
        person_id = "person_1"
        doc_id = "doc_1"
        rel = issued_to(person_id, doc_id, "certificate", source="test_block_1")
        assert rel.type == "issued_to"
        assert rel.properties["document_type"] == "certificate"

    def test_related_to(self):
        """Тест связи related_to."""
        from_id = "entity_1"
        to_id = "entity_2"
        rel = related_to(from_id, to_id, "family", confidence=0.95, source="test_block_1")
        assert rel.type == "family"
        assert rel.confidence == 0.95


class TestImportGraph:
    """Тесты графа импорта."""

    def test_import_graph_creation(self):
        """Тест создания графа."""
        graph = ImportGraph()
        assert graph.entities == []
        assert graph.relationships == []
        assert graph.metadata == {}

    def test_add_entity_to_graph(self):
        """Тест добавления сущности в граф."""
        graph = ImportGraph()
        person = make_person("Тестов Тест Тестович", birth_date=date(1985, 3, 15))
        graph.entities.append(person)
        assert len(graph.entities) == 1
        assert graph.entities[0].type == "person"

    def test_add_relationship_to_graph(self):
        """Тест добавления связи в граф."""
        graph = ImportGraph()
        person = make_person("Тестов Тест Тестович")
        phone = make_phone("+79161234567")
        graph.entities.extend([person, phone])

        rel = has_phone(person.id, phone.id)
        graph.relationships.append(rel)

        assert len(graph.entities) == 2
        assert len(graph.relationships) == 1

    def test_entity_count_by_type(self):
        """Тест подсчёта сущностей по типу."""
        graph = ImportGraph()
        person1 = make_person("Человек 1")
        person2 = make_person("Человек 2")
        phone = make_phone("+79161234567")

        graph.entities.extend([person1, person2, phone])
        counts = graph.entity_count_by_type()

        assert counts["person"] == 2
        assert counts["phone_number"] == 1


class TestImportGraphResult:
    """Тесты результата графа."""

    def test_import_graph_result_creation(self):
        """Тест создания результата графа."""
        graph = ImportGraph()
        result = ImportGraphResult(
            graph=graph,
            flat_records=[],
            stats={"entities": 0, "relationships": 0},
        )
        assert result.graph == graph
        assert result.flat_records == []

    def test_graph_to_dict(self):
        """Тест сериализации графа в словарь."""
        graph = ImportGraph()
        person = make_person("Тестов Тест Тестович")
        graph.entities.append(person)

        graph_dict = graph.to_dict()
        assert "entities" in graph_dict
        assert "relationships" in graph_dict
        assert "metadata" in graph_dict
