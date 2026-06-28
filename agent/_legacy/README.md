# Legacy Agent Modules

These modules are from the pre-v2 architecture (XML/TDML-based Tally client, old orchestrator pattern).

They have been superseded by:
- `agent/fetcher/` — JSON API fetchers (replaced `extractor/`)
- `agent/engine.py` — Command routing (replaced `orchestrator.py`)
- `agent/poller.py` — Cloud polling + upload (replaced `transmitter/`)
- `agent/connector.py` — Tally launch management (replaced `setup/`)

**Do not import from this directory.** It exists only for git history reference.

If Phase 4 (Windows service) needs service/telemetry code, rewrite it against the current engine/poller architecture.
