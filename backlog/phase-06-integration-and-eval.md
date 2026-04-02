# Phase 6: Integration, Testing & Evaluation

**Status:** Code complete — manual Ollama/LLM testing pending
**Depends on:** Phases 2, 3, 4, 5
**Estimated scope:** M

## Objective

Wire everything together, test end-to-end with Ollama, create evaluation Q&A pairs to measure
answer quality, and confirm all error paths behave gracefully.

## Inputs

- All tool implementations from Phases 2–5
- `evals/zoning_qa.xml` — Q&A evaluation pairs
- A running Ollama instance with `llama3.1:8b` or `llama3.1:70b` pulled (for manual testing only)

## Outputs

- `tests/test_integration.py` — automated end-to-end tool registration and callability tests
- `evals/zoning_qa.xml` — 20 Q&A pairs covering all tool categories
- Confirmed tool descriptions effective for LLM tool selection (post-Ollama)

## Tasks

### Automated (code complete ✓)

- [x] End-to-end test: `tests/test_integration.py` verifies all 8 tools are registered and callable
  - `test_all_tools_registered` — checks tool names present in FastMCP registry
  - `test_lookup_district_tool` — live call with `RS-3`
  - `test_compare_districts_tool` — live call with `RS-3` vs `RT-4`
  - `test_list_district_types_tool` — full list and filtered
  - `test_calculate_development_envelope_tool` — 5000 sqft RS-3 lot
  - `test_get_zoning_map_url_tool` — default and custom coordinates
  - `test_search_zoning_code_no_index` — returns helpful error when index missing
  - `test_get_zoning_section_no_index` — returns helpful error when index missing
- [x] Error handling tests (all covered in `tests/test_integration.py`):
  - Bad district codes → structured error dict, no exception
  - Addresses outside Chicago → structured error dict
  - Network failures (Socrata timeout) → structured error dict with hint
  - Missing Title 17 index → helpful error with `hint` pointing to ingestion command
- [x] Performance check: `lookup_district` and `calculate_development_envelope` both < 100ms avg
- [x] `evals/zoning_qa.xml` — 20 Q&A pairs:
  - 5 factual district lookup questions
  - 4 development calculator questions
  - 4 district comparison questions
  - 4 geospatial lookup questions
  - 3 zoning code text search questions

### Manual / Human-gated

- [ ] **[MANUAL]** Test with Ollama directly (requires Ollama + Continue.dev or Claude Desktop)
  - Start server: `python -m src.server`
  - Connect via MCP Inspector: `npx @modelcontextprotocol/inspector python -m src.server`
  - Ask multi-step questions from `evals/zoning_qa.xml` and verify answers
  - Target models: `llama3.1:8b` (minimum) and `llama3.1:70b` (recommended)
  - Key multi-step question: *"What's the zoning at 4521 N Clark St, and what could I build
    on a 3,000 sq ft lot there?"* — should call `get_parcel_zoning` then
    `calculate_development_envelope`
- [ ] **[POST-MANUAL]** Tune tool descriptions if LLM picks wrong tools
  - Edit docstrings in `src/tools/*.py` to clarify tool purpose/trigger phrases
  - Re-test with same Q&A set until LLM consistently picks correct tools

## Key Files

| File | Owner | Status |
|------|-------|--------|
| `tests/test_integration.py` | Tester | ✓ Complete |
| `evals/zoning_qa.xml` | Tester / Scribe | ✓ Complete |

## Acceptance Criteria

- [x] All 8 tools callable from `tests/test_integration.py` without errors
- [x] 20 eval Q&A pairs written and categorized
- [x] Error messages are helpful dicts (not stack traces) for all known failure modes
- [x] `pytest tests/ -m "not network"` passes clean (100% green, no warnings)
- [ ] Ollama + MCP server produces correct, natural-language answers to common zoning questions
      *(manual verification — not automated)*
- [ ] Tool descriptions confirmed effective — LLM selects correct tool 90%+ of the time
      *(manual verification — not automated)*

## Notes

- Model choice matters. Test with both `llama3.1:8b` and `llama3.1:70b`. The 8b model may
  struggle with multi-tool orchestration but should handle single-tool calls fine.
- Tool descriptions are the primary lever for getting the LLM to call the right tool.
  Iterate on wording based on what you observe in testing.
- Network tests (`@pytest.mark.network`) are excluded from CI by default. Run manually
  with `pytest tests/ -m network` against the live Chicago Data Portal and Nominatim.
