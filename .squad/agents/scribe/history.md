# Scribe — History

<!-- Session logs will be appended here by Scribe after each work cycle. -->

## 2026-04-03 — Sprint Coder Cycle Log

**Session summary:** Coder phase cycle executed by Coordinator (Squad).

**Work completed:**
- Code quality pass: 21 ruff lint issues fixed across `src/` and `tests/`
  (import ordering, line length, unused imports/variables)
- Tier 2 network tests attempted; DNS blocked in CI sandbox — documented in sprint.md
- `STATUS.md` updated with 2026-04-03 activity
- `.squad/decisions.md` updated with code quality decision
- `.squad/sprint.md` updated with Tier 1.5 (code quality) results and Tier 2 test outcome
- Ralph reviewed and signed off on code quality changes

**Artifacts updated:**
- `src/data_loader.py`, `src/tools/geospatial.py`, `src/server.py` — lint fixes
- `src/tools/district_lookup.py` — lint fixes
- `tests/test_code_search.py`, `tests/test_geospatial.py`, `tests/test_development.py`,
  `tests/test_district_lookup.py`, `tests/test_integration.py` — lint fixes
- `STATUS.md`, `.squad/decisions.md`, `.squad/sprint.md` — status updates
- `.squad/agents/ralph/history.md` — Ralph sign-off logged

**Next steps for human:**
1. Run `pytest tests/ -m network` from a machine with internet (Nominatim + Socrata)
2. Download Title 17 text (see `backlog/phase-05-code-text-search.md`)
3. Verify tools via MCP Inspector (`npx @modelcontextprotocol/inspector python -m src.server`)
4. Test with Ollama (`ollama pull llama3.1:8b && python -m src.server`)

---

## 2026-04-03 — Sprint Coder Cycle 2 Log

**Session summary:** Second coder pass — integration test completeness and tool enhancement.

**Work completed:**
- Enhanced `compare_districts` tool: now returns a `_differences` key (list of field names
  that differ between the two districts). Empty list when comparing a district to itself.
  Makes it easier for LLMs to identify changed fields without iterating every response key.
- Added 4 new integration tests to `tests/test_integration.py`:
  - `test_get_zoning_map_url_tool` — covers the sync map-URL tool (default + custom coords)
  - `test_get_zoning_section_tool_with_fixture` — covers happy-path for section lookup
  - `test_compare_districts_differences_key` — verifies `_differences` contains changed fields
  - `test_compare_same_district_no_differences` — verifies empty `_differences` on self-compare
- All 8 MCP tools now have at least one integration test in `tests/test_integration.py`
- `ruff check src/ tests/` → 0 errors
- `pytest tests/ -m "not network"` → **75 passed, 5 deselected**
- Updated `STATUS.md`, `.squad/decisions.md`, `.squad/sprint.md` with results

**Artifacts updated:**
- `src/tools/district_lookup.py` — `compare_districts` enhanced with `_differences` key
- `tests/test_integration.py` — 4 new tests (17 total in integration suite)
- `STATUS.md` — updated to 75 tests passing
- `.squad/decisions.md` — decision logged
- `.squad/sprint.md` — test result updated

**Next steps for human:**
1. Run `pytest tests/ -m network` from a machine with internet
2. Download Title 17 text (see `backlog/phase-05-code-text-search.md`)
3. Verify all 8 tools via MCP Inspector
4. Test with Ollama


---

## 2026-04-03 — Sprint Coder Cycle 3 Log

**Session summary:** Bug fix — geocoder resilience pass.

**Work completed:**
- Identified unhandled exception path: `geocode_address` raised `httpx.HTTPError` on
  Nominatim network failures (connect errors, timeouts, HTTP errors) instead of returning
  `None`. This caused `get_parcel_zoning` to propagate a raw exception to the MCP client
  rather than returning a structured error dict.
- Fixed `src/geocoder.py`: wrapped Nominatim request in `try/except httpx.HTTPError: return None`
- Added 2 new unit tests in `tests/test_geospatial.py`:
  - `test_geocode_address_network_error_returns_none` — verifies ConnectError → None
  - `test_geocode_address_timeout_returns_none` — verifies TimeoutException → None
- `ruff check src/ tests/` → 0 errors
- `pytest tests/ -m "not network"` → **77 passed, 5 deselected**
- Updated `STATUS.md`, `.squad/decisions.md`, `.squad/sprint.md` with results

**Artifacts updated:**
- `src/geocoder.py` — network error handling fix
- `tests/test_geospatial.py` — 2 new geocoder unit tests
- `STATUS.md` — updated to 77 tests passing
- `.squad/decisions.md` — decision logged
- `.squad/sprint.md` — test result updated to 77 passed

**Next steps for human:**
1. Run `pytest tests/ -m network` from a machine with internet (Nominatim + Socrata)
2. Download Title 17 text (see `backlog/phase-05-code-text-search.md`)
3. Verify all 8 tools via MCP Inspector (`npx @modelcontextprotocol/inspector python -m src.server`)
4. Test with Ollama (`ollama pull llama3.1:8b && python -m src.server`)
