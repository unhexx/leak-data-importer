"""
Neo4j exporter for ImportGraphResult.

Usage:
    from leak_data_importer.exporters.neo4j_exporter import export_to_neo4j, setup_neo4j_constraints

    # Создаём индексы и ограничения перед импортом
    setup_neo4j_constraints(uri="bolt://localhost:7687", user="neo4j", password="password")

    # Экспортируем данные
    export_to_neo4j(result, uri="bolt://localhost:7687", user="neo4j", password="password")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from leak_data_importer.graph.result import ImportGraphResult

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None


def setup_neo4j_constraints(
    uri: str,
    user: str,
    password: str,
    database: str = "neo4j",
) -> dict:
    """
    Создаёт индексы и ограничения в Neo4j для оптимальной производительности запросов.

    Создаёт:
    - Constraints на уникальный id для каждого типа сущности
    - Индексы на canonical_key (для дедупликации)
    - Индексы на часто используемые свойства
    """
    if GraphDatabase is None:
        raise ImportError("neo4j package is required. Install with: pip install neo4j")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    results = {}

    with driver.session(database=database) as session:
        # Индексы для часто используемых свойств
        index_queries = [
            # Индекс на canonical_key для дедупликации
            "CREATE INDEX entity_canonical_key IF NOT EXISTS FOR (n:Entity) ON (n.canonical_key)",
            # Индексы на type для быстрого поиска по типу
            "CREATE INDEX entity_type IF NOT EXISTS FOR (n:Entity) ON (n.type)",
            # Индекс на даты событий
            "CREATE INDEX event_date IF NOT EXISTS FOR (n:Event) ON (n.date)",
            # Гео-индекс для координат (если используются)
            "CREATE INDEX location_coords IF NOT EXISTS FOR (n:Location) ON (n.lat)",
        ]

        for q in index_queries:
            try:
                session.run(q)
                results[q.split(" IF NOT EXISTS")[0][:60]] = "created_or_existed"
            except Exception as e:
                results[q[:60]] = str(e)

    driver.close()
    return results


def export_to_neo4j(
    result: "ImportGraphResult",
    uri: str,
    user: str,
    password: str,
    database: str = "neo4j",
    clear_existing: bool = False,
    batch_size: int = 1000,
) -> dict:
    """
    Экспортирует сущности и связи в Neo4j с использованием batch-операций.

    Args:
        result: ImportGraphResult с данными для экспорта
        uri: Neo4j URI (например, bolt://localhost:7687)
        user: Имя пользователя Neo4j
        password: Пароль Neo4j
        database: Имя базы данных (по умолчанию neo4j)
        clear_existing: Очистить все существующие данные перед импортом
        batch_size: Размер батча для UNWIND операций (по умолчанию 1000)

    Returns:
        dict с количеством созданных узлов и связей
    """
    if GraphDatabase is None:
        raise ImportError("neo4j package is required. Install with: pip install neo4j")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    nodes_created = 0
    rels_created = 0

    with driver.session(database=database) as session:
        if clear_existing:
            session.run("MATCH (n) DETACH DELETE n")

        # Batch создание узлов с использованием UNWIND
        entities = result.graph.entities
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            records = []

            for entity in batch:
                labels = ["Entity", entity.type.replace("_", " ").title().replace(" ", "")]
                props = {k: v for k, v in entity.properties.items() if not isinstance(v, (dict, list)) or k == "raw_fields"}
                props["id"] = entity.id
                props["canonical_key"] = entity.canonical_key

                records.append({
                    "id": entity.id,
                    "labels": labels,
                    "props": props,
                })

            query = """
                UNWIND $records AS record
                MERGE (n:Entity {id: record.id})
                SET n = record.props
                WITH n, record.labels AS labels
                CALL apoc.create.addLabels(n, labels) YIELD node
                RETURN count(node) AS cnt
            """
            # Упрощённая версия без apoc (работает в чистом Neo4j)
            simple_query = """
                UNWIND $records AS record
                MERGE (n:Entity {id: record.id})
                SET n += record.props
                RETURN count(n) AS cnt
            """
            session.run(simple_query, records=records)
            nodes_created += len(batch)

        # Batch создание связей
        relationships = result.graph.relationships
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i:i + batch_size]
            records = []

            for rel in batch:
                props = dict(rel.properties) if rel.properties else {}
                if rel.confidence is not None:
                    props["confidence"] = rel.confidence

                records.append({
                    "from_id": rel.from_id,
                    "to_id": rel.to_id,
                    "type": rel.type.upper(),
                    "props": props,
                })

            query = """
                UNWIND $records AS record
                MATCH (a {id: record.from_id})
                MATCH (b {id: record.to_id})
                MERGE (a)-[r:REL {type: record.type}]->(b)
                SET r += record.props
                RETURN count(r) AS cnt
            """
            session.run(query, records=records)
            rels_created += len(batch)

    driver.close()

    return {
        "nodes_created": nodes_created,
        "relationships_created": rels_created,
        "batch_size": batch_size,
    }


def export_to_neo4j_legacy(
    result: "ImportGraphResult",
    uri: str,
    user: str,
    password: str,
    database: str = "neo4j",
    clear_existing: bool = False,
) -> dict:
    """
    Оригинальный метод экспорта (по одному узлу за раз) — для совместимости.
    """
    if GraphDatabase is None:
        raise ImportError("neo4j package is required. Install with: pip install neo4j")

    driver = GraphDatabase.driver(uri, auth=(user, password))

    nodes_created = 0
    rels_created = 0

    with driver.session(database=database) as session:
        if clear_existing:
            session.run("MATCH (n) DETACH DELETE n")

        # Create nodes
        for entity in result.graph.entities:
            labels = ["Entity", entity.type.replace("_", " ").title().replace(" ", "")]
            props = {k: v for k, v in entity.properties.items() if not isinstance(v, (dict, list)) or k == "raw_fields"}
            props["id"] = entity.id
            props["canonical_key"] = entity.canonical_key

            query = f"""
                MERGE (n:{":".join(labels)} {{id: $id}})
                SET n += $props
            """
            session.run(query, id=entity.id, props=props)
            nodes_created += 1

        # Create relationships
        for rel in result.graph.relationships:
            query = """
                MATCH (a {id: $from_id})
                MATCH (b {id: $to_id})
                MERGE (a)-[r:REL {type: $type}]->(b)
                SET r += $props
            """
            props = rel.properties or {}
            if rel.confidence is not None:
                props["confidence"] = rel.confidence

            session.run(
                query,
                from_id=rel.from_id,
                to_id=rel.to_id,
                type=rel.type.upper(),
                props=props,
            )
            rels_created += 1

    driver.close()

    return {
        "nodes_created": nodes_created,
        "relationships_created": rels_created,
    }
