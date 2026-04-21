# T5-01–T5-06 — Ollama LLM End-to-End Testing (Manual)

**Sprint tier:** 5 (Ollama / LLM)  
**Owner:** Lead + Tester  
**Status:** ⏳ Pending — requires Ollama installed  
**Priority:** Medium  
**Depends on:** T4 (MCP Inspector verification recommended first)

## Objective

Connect the running MCP server to an Ollama-backed LLM and verify that the model
correctly selects and calls the right tool for each question category.

## Prerequisites

```bash
# Pull the model
ollama pull llama3.1:8b   # baseline
ollama pull llama3.1:70b  # higher accuracy (optional)

# Start the MCP server
python -m src.server
```

## Test Questions (from evals/zoning_qa.xml)

| Q# | Question | Expected tool | Expected answer |
|----|----------|--------------|-----------------|
| Q1 | What is the FAR for RS-3? | `lookup_district` | 0.9 |
| Q8 | How much floor area on a 5000 sqft RS-3 lot? | `calculate_development_envelope` | 4500 sqft |
| Q11 | What's the zoning at 233 S Wacker Dr? | `get_parcel_zoning` | DC-16 |
| Q14 | Link to Chicago zoning map at Willis Tower | `get_zoning_map_url` | gisapps URL |
| Q19 | Zoning at 4521 N Clark St + envelope for 3000 sqft? | `get_parcel_zoning` → `calculate_development_envelope` | district + sqft |
| Q20 | Compare RS-3 vs RT-4; units on 6000 sqft if rezoned? | `compare_districts` + `calculate_development_envelope` | 4 additional units |

## Acceptance Criteria

- [ ] LLM selects correct single-tool for Q1, Q8, Q14 (90%+ of the time)
- [ ] LLM chains tools correctly for Q19, Q20 (multi-step)
- [ ] No tool returns an exception or stack trace in the LLM's context
- [ ] If tool selection is wrong: tune docstrings per T5-05 and re-test

## Notes

- `llama3.1:8b` may struggle with multi-step tool chaining; `llama3.1:70b` is more reliable
- Docker Compose is available: `docker compose up` starts Ollama + MCP server together
- Tool descriptions are in `src/tools/*.py` — update docstrings if LLM picks wrong tool
