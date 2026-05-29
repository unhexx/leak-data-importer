# TODO - Phase 4: Testing, Quality & PII Safety

## Status: IN_PROGRESS (Cycle 4 starting)

### Testing Coverage
- [x] Add unit tests for PersonLinker - DONE (19 tests, all passing)
- [x] Run existing test suite to verify compatibility - DONE
- [ ] Add unit tests for database repositories
- [ ] Add integration tests for import pipeline
- [x] Fix test failures in person_linker - weights sum to 1.0, exact passport returns 1.0

### Code Quality
- [ ] Run Ruff linter and fix issues
- [ ] Run MyPy type checker and fix issues  
- [ ] Verify schema compatibility with migrations

### PII Safety Strategy
- [x] Document PII classification - DONE
- [ ] Add PII redaction utilities
- [ ] Ensure no PII in logs or debug output
- [ ] Add data masking for exports

---

## Previous: Phase 3 Complete

### Phase 3 Tasks (Completed in Cycle 3)
- [x] 3.1: PersonLinker с множественными стратегиями - DONE (7 strategies)
- [x] 3.2: PersonLink model и repository - DONE
- [x] 3.3: Graph integration - DONE
- [x] 3.4: EvaluationHarness - DONE

### Phase 3 Summary
- PersonLinker: MatchStrategy enum + weighted scoring (passport=0.35, SNILS=0.25, INN=0.20, phone=0.10, fio=0.15, fuzzy_phone=0.05, birthdate=0.05)
- PersonLink: SQLAlchemy model с review полями
- PersonLinkRepository: полный CRUD
- Graph: make_person_link() factory, SAME_AS relationship
- Neo4j: export_person_links() batch export
- Evaluation: EvaluationHarness для review
- Tests: 38+ unit tests на все стратегии
