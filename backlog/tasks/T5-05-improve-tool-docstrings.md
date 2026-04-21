# T5-05 — Improve Tool Docstrings for LLM Tool Selection

**Sprint tier:** 5 (Ollama / LLM End-to-End)  
**Owner:** Data Engineer  
**Status:** ✅ Done — 2026-04-21  
**Priority:** Medium  
**Depends on:** None (proactive; does not require Ollama installed)

## Objective

Proactively improve docstrings in all `src/tools/*.py` files so that LLMs
(especially smaller models like `llama3.1:8b`) reliably pick the correct tool
for each natural-language question.

## Background

Sprint task T5-05 says: *"If wrong tool called: tune docstring in `src/tools/*.py`
to clarify tool purpose/trigger phrases."* This task implements those improvements
proactively, before Ollama testing, so that baseline tool selection is as good as
possible from the first manual test run.

## Changes

### `src/tools/district_lookup.py`

- `lookup_district` — clarified that input is a **district code** (not an address)
  and that live geocoding is NOT performed; added example codes in docstring.
- `compare_districts` — added explicit mention of what `_differences` contains and
  that both codes must be known before calling.
- `list_district_types` — improved category list; added note that it returns a
  summary list and can be used to discover valid codes.

### `src/tools/development.py`

- `calculate_development_envelope` — clarified that you need a district code first
  (use `get_parcel_zoning` to look up from an address); listed all returned fields.

### `src/tools/geospatial.py`

- `get_parcel_zoning` — emphasized the address-or-coordinates choice; noted that
  this tool does live network I/O (Nominatim + Socrata) and is required as a first
  step when the user gives a street address.
- `get_zoning_map_url` — clarified it returns a URL to the official map viewer and
  does **not** look up the district code.

### `src/tools/code_search.py`

- `search_zoning_code` — strengthened trigger phrases; noted that this tool searches
  the full text of Title 17 (the Chicago Zoning Ordinance), not just district codes.
- `get_zoning_section` — clarified it is for **direct section retrieval by number**
  (faster than search) and requires the Title 17 index to be built.

## Acceptance Criteria

- [x] All tool docstrings updated to be more specific about inputs, outputs, and
  when to use this tool vs. alternatives.
- [x] `ruff check src/` passes with 0 issues after changes.
- [x] `pytest tests/ -m "not network"` still passes with 0 failures.

## Notes

- No functional code changes — only docstrings.  
- Docstring improvements do not require a new test but should not break existing ones.
