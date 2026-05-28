# Entity & Relationship Model for Leak Data Analysis

This document defines the **object model** used by the importer when working in graph mode (`parse_to_graph()`).

The goal is to move from flat records (`PersonRecord`) to a proper **entity-relationship graph** that makes connection search, clustering, and investigation much more powerful.

## Core Concepts

### Entity
A real-world object extracted from leak data.

**Common types** (as of current version):

| Type                | Description                              | Key Properties                     | Canonical Key Example      |
|---------------------|------------------------------------------|------------------------------------|----------------------------|
| `person`            | Physical person                          | `full_name`, `birth_date`          | `ivanov_ivan_ivanovich`    |
| `phone_number`      | Phone number                             | `number` (E.164)                   | `+79161234567`             |
| `email_address`     | Email                                    | `address`                          | `user@example.com`         |
| `passport`          | Russian internal passport                | `number`                           | `4506123456`               |
| `snils`             | SNILS                                    | `number` (formatted)               | `123-456-789 01`           |
| `esia_account`      | Gosuslugi / ESIA account                 | `esia_id`                          | `1076827674`               |
| `physical_address`  | Registered or residential address        | `address`                          | (normalized string)        |
| `vehicle`           | Vehicle (VIN)                            | `vin`                              | `...`                      |
| `sim_card`          | SIM card (ICCID / IMSI)                  | `iccid`, `imsi`                    | -                          |

### Relationship
A directed connection between two entities.

**Common relationship types**:

- `has_phone`
- `has_email`
- `has_document` (passport / snils / other)
- `owns_account` (ESIA, etc.)
- `registered_at` (person → address, with date)
- `associated_with` (generic)

Each relationship can carry `properties` (e.g. registration date, confidence, IP address at the time).

## Usage Example

```python
from leak_data_importer.importers.txt_report import TxtReportImporter

imp = TxtReportImporter("data/raw/report_....txt")
result = imp.parse_to_graph()

print(result.summary())
print(result.graph.entity_count_by_type())

# Example: find all phones belonging to one person
for rel in result.graph.relationships:
    if rel.type == "has_phone":
        person = next(e for e in result.graph.entities if e.id == rel.from_id)
        phone = next(e for e in result.graph.entities if e.id == rel.to_id)
        print(person.properties["full_name"], "→", phone.properties["number"])
```

## Design Principles

1. **Deduplication is per-source-block for now** — we are conservative. Later we will add fuzzy matching across the whole dataset.
2. **Lossless** — we keep the original flat records in `flat_records`.
3. **Extensible** — easy to add new entity types and relationship types.
4. **Analysis-ready** — designed to be exported to Neo4j, NetworkX, or custom investigation tools.

## Future Work (Roadmap)

- Cross-file entity resolution (same person appears in multiple reports)
- Stronger normalization + validation (passport checksum, SNILS checksum)
- Temporal relationships (`registered_at` with date + source)
- Event entities (registration events, authorization events)
- Export to Cypher / GraphML / JSON-Lines for graph DBs

This model is the foundation for the "search for connections" use case of the project.
