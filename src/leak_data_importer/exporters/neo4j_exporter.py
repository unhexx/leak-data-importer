"""
Neo4j exporter for ImportGraphResult.

Usage:
    from leak_data_importer.exporters.neo4j_exporter import export_to_neo4j

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


def export_to_neo4j(
    result: "ImportGraphResult",
    uri: str,
    user: str,
    password: str,
    database: str = "neo4j",
    clear_existing: bool = False,
) -> dict:
    """
    Export entities and relationships to Neo4j.

    Returns a dict with counts of created nodes and relationships.
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
