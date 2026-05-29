# Phase 3 Implementation Plan: Entity Resolution & Deduplication

## Overview

Phase 3 focuses on implementing entity resolution and deduplication capabilities to identify the same real person across different reports using multiple matching strategies.

---

## Information Gathered

### Current State
- **PersonLinker** (`src/leak_data_importer/linkers/person_linker.py`): Basic implementation with rapidfuzz, FIO similarity, birth date matching, passport boosting
- **SQLAlchemy Models** (`src/leak_data_importer/db/models.py`): `PersonConnection` table with `confidence` field exists
- **Graph Layer** (`src/leak_data_importer/graph/`): `Entity`, `Relationship`, `ImportGraph` models exist
- **Neo4j Exporter** (`src/leak_data_importer/exporters/neo4j_exporter.py`): Basic batch export exists
- **Repositories**: Person, Document, Report repositories exist

### What's Missing
1. Enhanced PersonLinker with multiple matching strategies (name + birthdate + phone + document)
2. DB storage for linking decisions (`person_links` table)
3. Graph integration for linked entities
4. Evaluation harness for linking quality

---

## Implementation Plan

### Step 1: Enhance PersonLinker with Multiple Strategies

**Files to modify:**
- `src/leak_data_importer/linkers/person_linker.py`

**Changes:**
1. Add additional matching strategies:
   - Exact document matching (passport, SNILS, INN)
   - Phone number partial matching
   - Birth date fuzzy matching (within N days tolerance)
2. Add weighted scoring for each strategy
3. Add configurable thresholds
4. Add strategy report showing which fields matched

### Step 2: Add DB Storage for Linking Decisions

**Files to create:**
- `migrations/versions/002_entity_resolution.py`

**New table: `person_links`**
```python
class PersonLink(Base):
    __tablename__ = "person_links"
    
    id = Column(UUID, primary_key=True)
    person_a_id = Column(UUID, ForeignKey("persons.id"))
    person_b_id = Column(UUID, ForeignKey("persons.id"))
    confidence = Column(Float)  # 0.0-1.0
    match_strategy = Column(String)  # "exact_passport", "fuzzy_fio", "phone_match", etc.
    is_reviewed = Column(Boolean, default=False)
    is_confirmed = Column(Boolean, nullable=True)
    reviewed_by = Column(String)
    created_at = Column(TIMESTAMP)
```

**Files to modify:**
- `src/leak_data_importer/db/models.py` - Add PersonLink model
- `src/leak_data_importer/db/repositories/` - Add PersonLinkRepository

### Step 3: Graph Integration for Linked Entities

**Files to modify:**
- `src/leak_data_importer/graph/factories.py` - Add `make_person_link()`
- `src/leak_data_importer/exporters/neo4j_exporter.py` - Add link export

**Changes:**
1. Add `make_person_link()` factory for linked person entity clusters
2. Modify Neo4j exporter to export person links as "SAME_AS" relationships
3. Add batch export for linked entity clusters

### Step 4: Evaluation Harness

**Files to create:**
- `src/leak_data_importer/evaluation/harness.py`

**Features:**
1. Load reports and run linker
2. Show match clusters with confidence scores
3. Simple CLI for manual review
4. Export evaluation results

---

## Dependent Files

| File | Action |
|------|--------|
| `src/leak_data_importer/linkers/person_linker.py` | Modify - enhance matching |
| `src/leak_data_importer/db/models.py` | Modify - add PersonLink |
| `src/leak_data_importer/graph/factories.py` | Modify - add link factory |
| `src/leak_data_importer/exporters/neo4j_exporter.py` | Modify - add link export |
| `migrations/versions/002_entity_resolution.py` | Create - new migration |
| `src/leak_data_importer/db/repositories/person.py` | Modify - add link methods |
| `src/leak_data_importer/evaluation/harness.py` | Create - evaluation tool |

---

## Follow-up Steps

1. Run database migration to create person_links table
2. Test enhanced PersonLinker with sample reports
3. Verify graph export includes linked entities
4. Run evaluation harness to review quality

---

## Status: PLANNED

This plan is ready for Coder implementation.
