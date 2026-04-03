# Decisions Log — chicago-zoning-mcp

> Significant architectural and data decisions are recorded here by the Lead.
> Format: `### YYYY-MM-DD — [Agent] — [Decision Title]`

### 2026-04-02 — Lead — Backlog organized as phase files, not individual task files

**Context:** The problem statement referenced `backlog/tasks/` as a directory of individual
task files. The actual backlog uses a flat `backlog/phase-0N-*.md` structure.

**Decision:** Treat each phase file as the canonical task specification for that phase.
Created `backlog/README.md` and `backlog/data_sources.md` as the missing cross-cutting
reference documents. No restructuring of existing phase files needed.

**Rationale:** The phase files contain sufficient task-level detail. Restructuring would
create unnecessary churn with no implementation benefit.

### 2026-04-02 — Lead — Title 17 ingestion is a human-gated step, not a code blocker

**Context:** `search_zoning_code` and `get_zoning_section` tools depend on
`data/title_17/sections.json`, which is built from manually downloaded text.

**Decision:** Mark Title 17 ingestion as BLOCKED on human action in both `STATUS.md` and
`.squad/sprint.md`. All other tools (Phases 2–4) work without it. The code-search tools
return a structured error with instructions when the index is absent.

**Rationale:** We cannot automate downloading from American Legal Publishing without
potentially violating their ToS. The helper script (`download_title_17.py`) attempts
scraping as a best-effort approach; if it fails, manual copy-paste is the fallback.

### 2026-04-02 — Lead — Sprint Tier structure separates automated from manual validation

**Context:** Sprint planning needed to distinguish tasks that automated agents can execute
from tasks requiring a human or local Ollama setup.

**Decision:** Organized `.squad/sprint.md` into 6 tiers:
- Tier 1: Offline automated tests (run immediately)
- Tier 2: Network integration tests
- Tier 3: Title 17 ingestion (human-gated)
- Tier 4: MCP Inspector manual verification
- Tier 5: Ollama end-to-end testing
- Tier 6: Documentation/fresh-clone verification

**Rationale:** Agents can immediately execute Tiers 1–2 without human involvement. Tiers
3–6 gate on human setup but should not block sprint progress for automated work.

### 2026-04-02 — Tester — Tier 1 offline tests executed and all pass

**Context:** Coder phase kicked off. First automated action was running the full offline test suite.

**Decision:** Treat a green `pytest tests/ -m "not network"` run as the official sprint Tier 1
completion gate. Result: 69 passed, 5 deselected (network tests marked with `@pytest.mark.network`).

**Rationale:** All 8 tools are registered and callable; all data-layer, tool-layer, and
integration assertions pass with real CSV data and lightweight mocks for external APIs.

### 2026-04-02 — Lead — .gitignore was missing from repo

**Context:** Phase 1 backlog listed `.gitignore` creation as a completed task, but the file
was absent from the repository. Running tests before the file existed caused `__pycache__`
directories to be tracked by git.

**Decision:** Create `.gitignore` covering Python artifacts (`__pycache__`, `*.pyc`, `.venv`,
`dist/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`), the gitignored data directory
(`data/title_17/`), and common editor/OS files. Remove previously tracked `__pycache__`
entries from git history.

**Rationale:** Without `.gitignore`, every test run pollutes the repo with compiled bytecode.
The `data/title_17/` exclusion is intentional per Phase 5 design — Title 17 raw text and the
generated `sections.json` index must not be committed (large files, manually downloaded).

### 2026-04-03 — Ralph/Lead — Code quality pass: ruff lint fixes in src/ and tests/

**Context:** Running `ruff check src/ tests/` revealed 21 lint issues: import ordering (I001),
line-too-long (E501), unused imports (F401), and one unused variable (F841).

**Decision:** Fix all 21 issues. 14 were auto-fixed with `ruff --fix`; 7 were fixed manually
(long string literals broken across lines, unused `mcp` variable removed).

**Changes made:**
- `src/data_loader.py` — added `# noqa: E501` on docstring example line
- `src/tools/geospatial.py` — fixed import order; broke 3 long hint strings across lines
- `src/server.py`, `src/tools/district_lookup.py` — fixed import order
- `tests/test_code_search.py` — removed unused `json`, `pytest`, `load_section_index` imports;
  broke long text fixture string
- `tests/test_geospatial.py` — fixed import order; removed unused `mcp` variable and unused
  `register_geospatial_tools` import
- `tests/test_development.py`, `tests/test_district_lookup.py`, `tests/test_integration.py` —
  fixed import ordering; broke long mock fixture line

**Rationale:** Clean lint state ensures ruff can be used as a CI gate without noise,
and removes genuinely unused code (F401, F841) that can confuse future contributors.
All 69 offline tests pass after changes.


### 2026-04-03 — Tester/Lead — Gap-fill pass: fixed broken test, added missing coverage

**Context:** Review of `tests/test_development.py` and `tests/test_integration.py` revealed
two coverage gaps against Phase 3 acceptance criteria:

1. `test_development_envelope_has_disclaimer` called `get_district()` directly and checked
   FAR arithmetic — it never called the MCP tool and never verified the `disclaimer` key.
2. The Phase 3 acceptance criterion "DC-16, 10,000 sqft lot → 160,000 sqft max floor area"
   was only verified at the data layer (test_dc16_high_density), not through the MCP tool.
3. `list_district_types` had no entry in `tests/test_integration.py`.

**Decision:** Fix the broken test to actually call the tool and assert `disclaimer` is
present; add `test_development_envelope_dc16_10000sqft` to verify the DC-16 criterion via
the tool; add `test_list_district_types_tool` to cover the missing integration path.
Updated `backlog/phase-03-development-calculator.md` to mark acceptance criteria with
checkboxes.

**Changes made:**
- `tests/test_development.py` — fixed `test_development_envelope_has_disclaimer`; added
  `test_development_envelope_dc16_10000sqft`
- `tests/test_integration.py` — added `test_list_district_types_tool`
- `backlog/phase-03-development-calculator.md` — added `[x]` checkboxes to acceptance criteria

**Rationale:** Phase 3 acceptance criteria must be verified through the actual MCP tool
interface (not just the underlying data functions) to confirm end-to-end correctness.
Offline test count increases from 69 to 71. `ruff check src/ tests/` remains clean at
0 errors.


### 2026-04-03 — Coder/Lead — Integration suite completeness pass: all 8 tools now covered

**Context:** Review of `tests/test_integration.py` revealed two tools had no integration
test covering their happy-path: `get_zoning_map_url` (sync tool, no mocking needed) and
`get_zoning_section` (async/sync tool, needs a fixture index). `compare_districts` lacked
a test for the new `_differences` summary key.

**Decision:**
1. Add `test_get_zoning_map_url_tool` — exercises default and custom-coordinate calls.
2. Add `test_get_zoning_section_tool_with_fixture` — patches `load_section_index` with a
   one-entry fixture and asserts the tool returns section/title/text.
3. Add `test_compare_districts_differences_key` and `test_compare_same_district_no_differences`
   to cover the new `_differences` list.

**Changes made:**
- `src/tools/district_lookup.py` — `compare_districts` now appends `_differences` key:
  a list of field names where the two districts differ. Empty list when comparing a
  district to itself. LLMs can use this for targeted follow-up lookups.
- `tests/test_integration.py` — 4 new tests added; all 8 tools now have at least one
  integration test in the suite.

**Rationale:** Complete integration test coverage across all 8 tools ensures regressions
are caught immediately. The `_differences` key makes `compare_districts` output more
directly consumable by LLMs without requiring them to iterate through every field.
Offline test count increases from 71 to 75. `ruff check src/ tests/` remains clean at
0 errors.


### 2026-04-03 — Coder/Lead — Geocoder resilience: network errors return None instead of raising

**Context:** `geocode_address` in `src/geocoder.py` used a bare `async with httpx.AsyncClient()`
call with no exception handling. If Nominatim was unreachable (DNS failure, timeout, HTTP error),
an `httpx.HTTPError` would propagate all the way out of `get_parcel_zoning`, resulting in an
unhandled exception exposed to the MCP client instead of a structured error dict.

**Decision:** Wrap the Nominatim HTTP call in a `try/except httpx.HTTPError` block in
`geocode_address`. On any HTTP-level error, return `None`. The existing `get_parcel_zoning`
code already handles `None` from `geocode_address` by returning a structured error dict with
a hint — this means all Nominatim failure modes now produce user-friendly responses.

**Changes made:**
- `src/geocoder.py` — added `try/except httpx.HTTPError: return None` around the Nominatim
  request block
- `tests/test_geospatial.py` — added `test_geocode_address_network_error_returns_none` and
  `test_geocode_address_timeout_returns_none`; imported `httpx` and `geocode_address`

**Rationale:** A production MCP server should never surface raw stack traces to LLM clients.
Nominatim is an external dependency that can fail; treating all its failure modes as
"could not geocode" (return None) is the correct abstraction. Offline test count increases
from 75 to 77. `ruff check src/ tests/` remains clean at 0 errors.

