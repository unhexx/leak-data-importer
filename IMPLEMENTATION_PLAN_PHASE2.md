# Comprehensive Implementation Plan: Phase 2 — Database Layer Modernization

## Current State Analysis

| Component | Status | Location |
|-----------|--------|----------|
| SQLAlchemy 2.0 models | ✅ DONE | src/leak_data_importer/db/models.py |
| ReportMapper legacy | ✅ EXISTS | src/leak_data_importer/db/report_mapper.py |
| Database schema | ✅ EXISTS | db/schema.sql |
| Alembic config | ❌ MISSING | - |
| Migrations | ❌ MISSING | - |
| Repository layer | ❌ MISSING | - |

## Implementation Steps

### Step 1: Initialize Alembic

Create the following files:

```
alembic.ini                    # Alembic config
migrations/
├── env.py                    # SQLAlchemy 2.0 URL processing
├── script.py.mako            # Migration template
└── versions/
    └── 001_initial.py       # Initial migration from models
```

**Key considerations:**
- Must create PostgreSQL enum types before tables
- Use SQLAlchemy 2.0 with uuid-ossp extension
- Set up revision/downgrade properly

### Step 2: Create Repository Layer

Create the following files:

```
src/leak_data_importer/db/repositories/
├── __init__.py              # Exports all repositories
├── base.py                 # BaseRepository with common CRUD
├── report.py               # ReportRepository
├── person.py               # PersonRepository
└── document.py             # DocumentRepository
```

**BaseRepository includes:**
- `create()` - Insert with session
- `get_by_id()` - Fetch by UUID
- `get_all()` - Paginated list
- `update()` - Update fields
- `delete()` - Soft or hard delete

**Typed Query Finders:**
- `get_by_filename()` for Report
- `get_by_fio()` for Person  
- `get_by_doc_type_and_number()` for Document

### Step 3: Update Exports

Update `src/leak_data_importer/db/__init__.py` to export repositories.

## File Changes Summary

| File Path | Action |
|-----------|--------|
| alembic.ini | CREATE |
| migrations/env.py | CREATE |
| migrations/script.py.mako | CREATE |
| migrations/versions/001_initial.py | CREATE |
| src/leak_data_importer/db/repositories/__init__.py | CREATE |
| src/leak_data_importer/db/repositories/base.py | CREATE |
| src/leak_data_importer/db/repositories/report.py | CREATE |
| src/leak_data_importer/db/repositories/person.py | CREATE |
| src/leak_data_importer/db/repositories/document.py | CREATE |
| src/leak_data_importer/db/__init__.py | UPDATE - add repo exports |

## Implementation Order

1. Initialize Alembic: `alembic init migrations`
2. Configure env.py for SQLAlchemy 2.0 with proper URL handling
3. Create initial migration using model metadata
4. Create base repository class with standard CRUD
5. Implement concrete repositories for main entities
6. Update exports in db/__init__.py

## Testing Strategy

- Use in-memory SQLite for unit tests
- Create real PostgreSQL integration tests if DB available
- Verify `alembic upgrade head` works from clean state
