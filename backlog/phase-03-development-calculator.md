# Phase 3: Development Envelope Calculator

**Status:** Complete (scaffolded)
**Depends on:** Phase 1
**Estimated scope:** S

## Objective

Implement the development envelope calculator that combines district rules with a specific lot size to answer "what can I build here?" questions with concrete numbers.

## Tasks

- [x] Implement `calculate_development_envelope` tool — FAR × lot area, unit count, height, setbacks
- [x] Handle text-format fields gracefully (height limits, setbacks that aren't simple numbers)
- [x] Add tests for numeric FAR districts and text-based height districts
- [x] Test with downtown districts (DC-16 has FAR=16) and residential (RS-1 has FAR=0.5)
- [x] Verify disclaimer is included in output

## Key Files

- `src/tools/development.py` — tool implementation
- `tests/test_development.py` — unit tests

## Acceptance Criteria

- `calculate_development_envelope("RS-3", 5000)` returns max floor area of 4,500 sqft
- `calculate_development_envelope("DC-16", 10000)` returns max floor area of 160,000 sqft
- Text-based fields (height, setbacks) are passed through without crashing
- Disclaimer always present in output

## Notes

- FAR is numeric for all districts but height and setbacks are often text descriptions with conditionals. Parse what you can, pass through the rest.
