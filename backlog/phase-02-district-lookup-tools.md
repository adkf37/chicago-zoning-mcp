# Phase 2: Core Zoning Lookup Tools

**Status:** Complete (scaffolded)
**Depends on:** Phase 1
**Estimated scope:** S

## Objective

Implement the three structured-data tools that answer questions about zoning districts using the CSV reference data. These require no external API calls and form the backbone of the server.

## Tasks

- [x] Implement `lookup_district` tool — exact match by district code, returns full details
- [x] Implement `compare_districts` tool — side-by-side diff of two districts
- [x] Implement `list_district_types` tool — list all or filter by category
- [ ] Test all three tools via MCP Inspector *(manual step)*
- [ ] Verify tool descriptions are clear enough for LLM tool selection *(post-Ollama testing)*
- [x] Write unit tests for edge cases (unknown district, empty category filter, same-district comparison)

## Key Files

- `src/tools/district_lookup.py` — all three tool implementations
- `tests/test_district_lookup.py` — unit tests

## Acceptance Criteria

- `lookup_district("RS-3")` returns structured data with all fields
- `compare_districts("RS-3", "RT-4")` shows differences clearly
- `list_district_types("Residential")` returns only residential districts
- All tests pass: `pytest tests/test_district_lookup.py`
- Tools appear and are callable in MCP Inspector
