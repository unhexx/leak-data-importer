# TODO - Phase 3: Entity Resolution & Deduplication

## Status: PLANNED

### Step 1: Enhance PersonLinker ⏳
- [ ] Add document number matching (passport, SNILS, INN)
- [ ] Add phone number partial matching
- [ ] Add birth date fuzzy matching within tolerance
- [ ] Add weighted scoring for each strategy
- [ ] Add strategy report showing matched fields

### Step 2: Add DB Storage for Links ⏳
- [ ] Create PersonLink SQLAlchemy model
- [ ] Create PersonLinkRepository
- [ ] Create migration 002_entity_resolution.py

### Step 3: Graph Integration ⏳
- [ ] Add make_person_link() factory function
- [ ] Modify Neo4j exporter for linked entities
- [ ] Add SAME_AS relationship export

### Step 4: Evaluation Harness ⏳
- [ ] Create evaluation harness module
- [ ] Add CLI for manual review
- [ ] Document limitations and edge cases

---

## Next Steps (Future)

### Phase 4: Testing, Quality & PII Safety
- [ ] Increase test coverage
- [ ] Add PII handling strategy
- [ ] Improve normalization
