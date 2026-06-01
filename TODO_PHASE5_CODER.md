# TODO Phase 5 — Cycle 6 Tasks (Orchestrator Planned)

## Priority 1: CSV Exporter (First Coder Task) ✓ Planned

### Task 1.1: Create base exporter architecture
- [ ] Create BaseExporter abstract class in `exporters/base.py`
- [ ] Define common interface: export(entities, output_path), format options
- [ ] Add PII-safe export flags (redact_by_default=True)

### Task 1.2: Implement CSV exporter for Person entities  
- [ ] Create `src/leak_data_importer/exporters/csv_exporter.py`
- [ ] Support Person entity properties: full_name, birth_date, phones, emails, passports
- [ ] Handle multiple values (comma-separated)
- [ ] Add redact option for PII-safe output

### Task 1.3: CLI integration for CSV export
- [ ] Add `export csv` subcommand in cli.py
- [ ] Add help text and examples

---

## Priority 2-6: Later Cycles
- JSON Lines exporter
- Parquet exporter (optional)
- Streamlit enhancements  
- CLI expansions (analyze, link commands)
- GitHub Actions CI
- Documentation improvements

---

## Current Status: ORCHESTRATOR_PLANNING_COMPLETE

Orchestrator has completed Phase 5 planning. Ready for Coder to start first task.
