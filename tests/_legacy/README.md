# Legacy Tests

These tests were written against the pre-v2 agent architecture (XML client, orchestrator, old transmitter).

They reference modules that have been moved to `agent/_legacy/` and will not pass against the current codebase.

**Active test suites** (in `tests/`):
- `test_full_pipeline.py` — End-to-end pipeline test
- `test_multi_company.py` — Multi-company support (37 tests)
- `test_offline_queue.py` — Offline queue + retry (32 tests)
- `seed_e2e.py` — Database seeding utility
