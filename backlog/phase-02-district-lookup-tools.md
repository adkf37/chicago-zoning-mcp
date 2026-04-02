# Phase 2: Core Zoning Lookup Tools

**Status:** Complete
**Depends on:** Phase 1
**Estimated scope:** S

## Objective

Implement the three structured-data tools that answer questions about zoning districts using the
CSV reference data. These require no external API calls and form the backbone of the server.

## Inputs

- `src/data_loader.py` — `get_district()`, `get_all_districts()`, `get_districts_by_category()`
- `data/zoning_codes.csv` — all district data

## Outputs

- `src/tools/district_lookup.py` — three MCP tools:
  - `lookup_district(district_code: str) -> dict` — full district detail or error dict
  - `compare_districts(district_a: str, district_b: str) -> dict` — side-by-side field diff
  - `list_district_types(category: str = "") -> list[dict]` — summary list, optional category filter
- `tests/test_district_lookup.py` — unit tests

## Tasks

- [x] Implement `lookup_district` tool — exact match by district code, returns full details
- [x] Implement `compare_districts` tool — side-by-side diff of two districts
- [x] Implement `list_district_types` tool — list all or filter by category
- [x] Write unit tests for edge cases (unknown district, empty category filter, same-district comparison)
- [ ] **[MANUAL]** Test all three tools via MCP Inspector
  - `npx @modelcontextprotocol/inspector python -m src.server`
  - Verify tools appear in the inspector UI and return expected output
- [ ] **[POST-MANUAL]** Verify tool descriptions are clear enough for LLM tool selection
  - Test with Ollama: *"What's the FAR for RS-3?"*, *"Compare RS-3 and RT-4"*, *"List all residential districts"*
  - Adjust docstrings if LLM calls wrong tool

## Key Files

- `src/tools/district_lookup.py` — all three tool implementations
- `tests/test_district_lookup.py` — unit tests

## Acceptance Criteria

- [x] `lookup_district("RS-3")` returns structured data with all fields
- [x] `compare_districts("RS-3", "RT-4")` shows differences clearly
- [x] `list_district_types("Residential")` returns only residential districts
- [x] `lookup_district("INVALID")` returns a structured error dict (not an exception)
- [x] All tests pass: `pytest tests/test_district_lookup.py`
- [ ] Tools appear and are callable in MCP Inspector *(manual verification)*
