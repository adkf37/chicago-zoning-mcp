# Sprint Plan — chicago-zoning-mcp

**Created:** 2026-04-02  
**Status:** Sprint 1 — ready to execute  
**Phase gate:** Lead must approve before closing sprint

---

## Sprint Summary

All automated code tasks across Phases 1–7 are **complete**. The codebase has 8 registered
MCP tools, full test coverage for offline scenarios, 20 evaluation Q&A pairs, and complete
documentation. The remaining open items are either manual human steps (Title 17 download,
Ollama/LLM testing) or post-manual cleanup (tool description tuning).

This sprint plan formalizes remaining work and provides the ordered execution guide for
the Coder phase. Since no new code tasks were uncovered during review, the sprint is
lightweight and focused on validation and any gap-filling that emerges from manual testing.

---

## Task Execution Order

### Tier 1 — Automated Tests (Run immediately; no blockers)

| # | Task | Owner | File | Status |
|---|------|-------|------|--------|
| T1-01 | Run full offline test suite | Tester | `tests/` | ✓ Ready |
| T1-02 | Verify all 8 tools register and respond | Tester | `tests/test_integration.py` | ✓ Ready |
| T1-03 | Verify district lookup tools pass all edge cases | Tester | `tests/test_district_lookup.py` | ✓ Ready |
| T1-04 | Verify development calculator accuracy (RS-3, DC-16) | Tester | `tests/test_development.py` | ✓ Ready |
| T1-05 | Verify geospatial tools (unit — no network) | Tester | `tests/test_geospatial.py` | ✓ Ready |
| T1-06 | Verify code search tools (fixture-based) | Tester | `tests/test_code_search.py` | ✓ Ready |

**Run command:** `pytest tests/ -m "not network" --tb=short`

---

### Tier 2 — Network Integration Tests (Run with network access)

| # | Task | Owner | File | Status |
|---|------|-------|------|--------|
| T2-01 | Geocode known Chicago addresses via Nominatim | Tester | `tests/test_geospatial.py` | Needs network |
| T2-02 | Query Socrata parcel API for Wrigley Field, Willis Tower | Tester | `tests/test_geospatial.py` | Needs network |
| T2-03 | Confirm `get_parcel_zoning("233 S Wacker Dr")` returns DC-16 | Tester | `tests/test_geospatial.py` | Needs network |

**Run command:** `pytest tests/ -m network --tb=short`  
**Note:** Requires network access to `nominatim.openstreetmap.org` and `data.cityofchicago.org`

---

### Tier 3 — Title 17 Ingestion (BLOCKED — requires human action)

| # | Task | Owner | Blocker | Status |
|---|------|-------|---------|--------|
| T3-01 | Download Title 17 raw text from amlegal.com | **HUMAN** | Manual copy-paste required | ❌ BLOCKED |
| T3-02 | Save chapter text to `data/title_17/raw/chapter_17-N.txt` | **HUMAN** | Depends on T3-01 | ❌ BLOCKED |
| T3-03 | Run ingestion: `python scripts/ingest_title_17.py` | Data Engineer | Depends on T3-01, T3-02 | ❌ BLOCKED |
| T3-04 | Validate index: `python scripts/ingest_title_17.py --validate` | Data Engineer | Depends on T3-03 | ❌ BLOCKED |
| T3-05 | Confirm `search_zoning_code("accessory dwelling unit")` returns results | Tester | Depends on T3-04 | ❌ BLOCKED |

**Unblock action:** A human must manually download Title 17 from American Legal Publishing.
See `backlog/phase-05-code-text-search.md` for step-by-step instructions.

---

### Tier 4 — MCP Inspector Verification (Manual — requires local toolchain)

| # | Task | Owner | Status |
|---|------|-------|--------|
| T4-01 | Start server: `python -m src.server` | Lead | Manual |
| T4-02 | Open MCP Inspector: `npx @modelcontextprotocol/inspector python -m src.server` | Lead | Manual |
| T4-03 | Verify all 8 tools appear in inspector UI | Tester | Manual |
| T4-04 | Call `lookup_district` with `RS-3` — verify response | Tester | Manual |
| T4-05 | Call `compare_districts` with `RS-3` / `RT-4` — verify response | Tester | Manual |
| T4-06 | Call `list_district_types` with `Residential` — verify response | Tester | Manual |
| T4-07 | Call `calculate_development_envelope` with `RS-3`, 5000 — verify 4500 sqft | Tester | Manual |
| T4-08 | Call `get_parcel_zoning` with `"233 S Wacker Dr"` — verify DC-16 | Tester | Manual |
| T4-09 | Call `get_zoning_map_url` — verify URL returned | Tester | Manual |
| T4-10 | Call `search_zoning_code` — verify graceful error when index not built | Tester | Manual |

---

### Tier 5 — Ollama / LLM End-to-End Testing (Manual — requires Ollama)

| # | Task | Owner | Depends on | Status |
|---|------|-------|------------|--------|
| T5-01 | Pull model: `ollama pull llama3.1:8b` | Lead | Ollama installed | Manual |
| T5-02 | Connect MCP server to Continue.dev or Claude Desktop | Lead | T5-01 | Manual |
| T5-03 | Ask single-tool questions from `evals/zoning_qa.xml` | Tester | T5-02 | Manual |
| T5-04 | Ask multi-step question: *"What's the zoning at 4521 N Clark St, and what can I build on a 3,000 sqft lot?"* | Tester | T5-02 | Manual |
| T5-05 | If wrong tool called: tune docstring in `src/tools/*.py` | Data Engineer | T5-03, T5-04 | Conditional |
| T5-06 | Re-test with `llama3.1:70b` for higher accuracy (optional) | Tester | T5-01 | Optional |

---

### Tier 6 — Documentation Verification (Manual)

| # | Task | Owner | Status |
|---|------|-------|--------|
| T6-01 | Fresh-clone test: `git clone` → `pip install -e "[dev]"` → `pytest` | Scribe | Manual |
| T6-02 | Docker test: `docker compose up` → verify both services start and model auto-pulls | Lead | Manual |
| T6-03 | Cross-reference from parent repo README | **HUMAN** | Requires parent repo access |

---

## Agent Assignments

| Agent | Sprint Responsibilities |
|-------|------------------------|
| **Lead** | Gates sprint completion; own STATUS.md updates; owns `src/server.py` for any tool-wiring changes; oversees Tier 4–6 |
| **Data Engineer** | Executes T3-03/T3-04 once unblocked; handles T5-05 tool description tuning if LLM misbehaves |
| **Geo Developer** | Available if Nominatim/Socrata issues surface during T2 or T5 testing |
| **Tester** | Owns Tier 1 test execution; documents results of T4 and T5 manual testing |
| **Scribe** | Executes T6-01 fresh-clone test; updates README if any step fails |
| **Ralph** | Reviews all code changes from T5-05 (tool description edits) before merge; signs off on sprint completion |

---

## Blocked Tasks (Summary)

| Task | Blocked By | Owner |
|------|-----------|-------|
| T3-01 through T3-05 | Human must download Title 17 from amlegal.com | **HUMAN** |
| T6-03 | Human must have access to parent repo | **HUMAN** |

---

## Definition of Done

The sprint is **Done** when all of the following are true:

- [ ] `pytest tests/ -m "not network"` passes with 0 failures and 0 errors
- [ ] `pytest tests/ -m network` passes (or failures are documented network flakiness)
- [ ] All 8 tools verified callable in MCP Inspector (Tier 4)
- [ ] Ollama end-to-end test confirms single-tool calls work for all tool categories (Tier 5)
- [ ] No tool description issues requiring a code change, OR changes have been made and reviewed by Ralph
- [ ] `STATUS.md` updated to reflect sprint outcome
- [ ] Scribe has logged the sprint completion in `.squad/agents/scribe/history.md`

**Note:** Title 17 ingestion (Tier 3) and parent repo cross-reference (T6-03) are
explicitly out of scope for automated sprint completion — they require human action.
Sprint can be marked Done without them; they become backlog items for a future human-action sprint.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Socrata `intersects()` returns 0 features for valid Chicago coordinates | Medium | Medium | Fallback to city zoning map URL; document in tool response |
| Nominatim rate limit hit during network tests | Low | Low | Tests use 1-second delay; mark `@pytest.mark.network` to skip in CI |
| amlegal.com changes format, breaking ingestion parser | Medium (long-term) | Medium | Parser regex tested; re-run `--validate` after each ingest |
| LLM picks wrong tool (8b model limitation) | Medium | Low | Improve tool docstrings; `llama3.1:70b` is more reliable for multi-tool |
| Title 17 not downloaded within sprint window | High | Low | All other tools work without it; code search returns helpful error |
