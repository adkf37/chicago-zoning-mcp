# Phase 6: Integration, Testing & Evaluation

**Status:** Complete
**Depends on:** Phases 2, 3, 4, 5
**Estimated scope:** M

## Objective

Wire everything together, test end-to-end with Ollama, and create evaluation Q&A pairs to measure answer quality.

## Tasks

- [x] End-to-end test: `test_integration.py` verifies all 8 tools are registered and callable
- [ ] Test with Ollama directly *(manual step — requires Ollama + Continue.dev)*
  - Ask multi-step questions that require tool chaining
- [ ] Tune tool descriptions if LLM picks wrong tools *(post-Ollama testing)*
- [x] Test error handling (all covered in `test_integration.py`):
  - Bad district codes
  - Addresses outside Chicago
  - Network failures (Socrata timeout)
  - Missing Title 17 index
- [x] Created `evals/zoning_qa.xml` with 20 Q&A pairs:
  - Mix of factual lookup, comparison, geospatial, code search, and multi-step questions
- [x] Performance check: lookup_district and calculate_development_envelope both < 100ms avg

## Key Files

- `evals/zoning_qa.xml` — evaluation Q&A pairs
- `tests/` — all test files

## Acceptance Criteria

- All 7 tools callable from MCP Inspector without errors
- 10+ eval Q&A pairs written and passing
- Ollama + MCP server produces correct, natural-language answers to common zoning questions
- Error messages are helpful (not stack traces)

## Notes

- Model choice matters. Test with both llama3.1:8b and llama3.1:70b. The 8b model may struggle with multi-tool orchestration but should handle single-tool calls fine.
- Tool descriptions are the primary lever for getting the LLM to call the right tool. Iterate on wording based on what you observe in testing.
