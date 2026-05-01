# STATUS — chicago-zoning-mcp

| Field | Value |
|---|---|
| Phase | Web Deployment (in progress) |
| Last Updated | 2026-04-30 |
| Squad Template | data_pipeline |
| Priority | low |
| Blocking | None for automated work — see "Needs Human Input" below for manual follow-ups |
| GitHub Repo | https://github.com/adkf37/chicago-zoning-mcp |

## Current Objective

**Adding Gemini + Flask web layer for Google Cloud Run deployment (mirroring Homicide Bot architecture).**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **109 passed, 5 deselected** ✅
- `ruff check src/ tests/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

The following items remain open but **require human action or local toolchain** and are
explicitly out of scope for automated sprint completion (see `sprint.md` Definition of Done):

| Item | Blocker | Effort |
|------|---------|--------|
| Title 17 ingestion (T3-01–T3-05) | ✅ Done — 16 chapters in `data/title_17/raw/`, 1.1 MB `sections.json` | — |
| MCP Inspector verification (T4) | Needs local Node.js | ~30 min |
| Ollama end-to-end testing (T5) | Superseded — replacing with Gemini/Cloud Run deployment | closed |
| Parent repo cross-reference (T6-03) | Human needs access to parent repo | ~15 min |

See `.squad/decisions.md` for full validation evidence and final closeout notes.

## Recent Activity

- 2026-04-30: Web deployment phase started — adding `web/` (Flask+Gemini) layer + GitHub Actions CI/CD for Cloud Run. Title 17 confirmed already ingested locally. Ollama testing superseded by Gemini approach.
- 2026-04-30: Web layer complete — `web/app.py`, `web/gemini_client.py`, `web/tool_bridge.py`, `web/templates/index.html`, `.github/workflows/deploy-cloud-run.yml`, updated `Dockerfile` and `pyproject.toml`.
- 2026-04-22: Closeout complete — all automated acceptance criteria verified; STATUS.md updated
  to "Closeout (complete)"; final closeout notes logged in `.squad/decisions.md`. Remaining
  open items (Title 17 ingestion, MCP Inspector, Ollama, parent repo cross-reference) are
  explicitly human-gated and documented as follow-up work.
- 2026-04-21: Validate phase — ran all automatable checks; 109 offline tests pass, ruff clean,
  8 tools verified callable, RS-3 lookup and dev envelope values correct; phase advanced to closeout.
  Full evidence recorded in `.squad/decisions.md`.
- 2026-04-21: T5-05 — Proactive tool docstring improvements for LLM tool selection across all 8 tools.
- 2026-04-21: Eval coverage pass — added 4 automated eval tests for code-search Q&A pairs (Q15–Q18).
- 2026-04-21: Robustness passes 4–5 — OverflowError/ZeroDivisionError guards, input validation,
  consistency fix in code search; 109 offline tests pass.
- 2026-04-21: Robustness pass — bug fix + input validation:
  - `src/tools/geospatial.py`: added `except httpx.HTTPError` catch after the existing
    `TimeoutException` and `HTTPStatusError` handlers in the Socrata query block; now
    `httpx.ConnectError` and other transport-layer errors return a structured error
    dict instead of propagating as unhandled exceptions to MCP clients.
  - `src/tools/development.py`: added `lot_area_sqft <= 0` guard that returns a
    structured error dict immediately, preventing nonsense outputs for invalid inputs.
  - `tests/test_geospatial.py`: added `test_parcel_zoning_socrata_connect_error`.
  - `tests/test_integration.py`: added `test_development_envelope_zero_lot_area` and
    `test_development_envelope_negative_lot_area`. 99 offline tests now pass (up from
    96); `ruff check` still 0 issues.
- 2026-04-03: Gap-fill pass 2 — 5 new edge-case integration tests added:
  `test_compare_districts_first_invalid`, `test_compare_districts_second_invalid`,
  `test_compare_districts_both_invalid` (Phase 2 "unknown district" coverage for
  `compare_districts`); `test_development_envelope_pd_nonnumeric_far`,
  `test_development_envelope_commercial_no_units` (Phase 3 "text-format fields"
  coverage at tool level). 96 offline tests now pass (up from 91); `ruff check`
  still 0 issues.
- 2026-04-03: Bug fix — `get_parcel_zoning` now validates `is_in_chicago` after geocoding
  an address; previously this check was only applied for direct lat/lng inputs. Added
  `test_parcel_zoning_address_outside_chicago` to `tests/test_geospatial.py` and eval Q13
  test (`test_eval_q13_address_outside_chicago`) to `tests/test_evals.py`; 91 offline tests
  now pass (up from 89); `ruff check` still 0 issues
- 2026-04-03: Bug fix — `geocode_address` now catches `httpx.HTTPError` (connect errors,
  timeouts, HTTP errors) and returns `None` so `get_parcel_zoning` always returns a structured
  error dict instead of raising; 2 new geocoder unit tests added; 77 offline tests pass (up
  from 75)
- 2026-04-03: Coder pass 2 — enhanced `compare_districts` with `_differences` summary key;
  added `test_get_zoning_map_url_tool`, `test_get_zoning_section_tool_with_fixture`,
  `test_compare_districts_differences_key`, `test_compare_same_district_no_differences` to
  `tests/test_integration.py`; 75 offline tests now pass (up from 71)
- 2026-04-03: Gap-fill pass — fixed broken `test_development_envelope_has_disclaimer` (was
  calling data layer, not the MCP tool); added `test_development_envelope_dc16_10000sqft`
  (Phase 3 acceptance criterion tested via tool); added `test_list_district_types_tool`
  integration test; 71 offline tests now pass (up from 69)
- 2026-04-03: Code quality pass — fixed 21 ruff lint issues in `src/` and `tests/` (import
  ordering, line length, unused imports/variables); all 69 offline tests still pass
- 2026-04-02: Sprint Tier 1 executed — `pytest tests/ -m "not network"` → 69 passed, 5 deselected
- 2026-04-02: `.gitignore` created (was missing; prevented `__pycache__` from being ignored)
- 2026-04-02: Squad review complete — backlog gaps filled, sprint plan created
- 2026-04-01: Squad initialized — team roster, routing rules, and agent charters created
- 2026-04-01: Project activated by Maestro — GitHub repo created, agent task dispatched to Copilot

## Artifacts

| Artifact | Location | Status |
|---|---|---|
| STATUS.md | `./STATUS.md` | updated |
| FEEDBACK.md | `./FEEDBACK.md` | created |
| Backlog README | `backlog/README.md` | created |
| Data sources doc | `backlog/data_sources.md` | created |
| `.gitignore` | `.gitignore` | created (was missing from repo) |
| Phase 1 — Scaffold | `backlog/phase-01-scaffold-and-data.md` | complete — inputs/outputs added |
| Phase 2 — District Lookup | `backlog/phase-02-district-lookup-tools.md` | complete — inputs/outputs added |
| Phase 3 — Dev Calculator | `backlog/phase-03-development-calculator.md` | complete |
| Phase 4 — Geospatial | `backlog/phase-04-geospatial-tools.md` | complete |
| Phase 5 — Code Search | `backlog/phase-05-code-text-search.md` | code complete; blocked on human Title 17 download |
| Phase 6 — Integration | `backlog/phase-06-integration-and-eval.md` | code complete; manual Ollama testing pending |
| Phase 7 — Docs | `backlog/phase-07-documentation.md` | complete; manual fresh-clone check pending |
| Squad team roster | `.squad/team.md` | created |
| Squad routing rules | `.squad/routing.md` | created |
| Squad decisions log | `.squad/decisions.md` | created |
| Sprint plan | `.squad/sprint.md` | created |
| Agent charters | `.squad/agents/*/charter.md` | created |
| Agent histories | `.squad/agents/*/history.md` | created |

## Needs Human Input

> ⚠️ These items are the only remaining blockers for full feature completeness. All other tools work today.

- **Title 17 download** (~2 hrs) — A human must manually copy-paste Title 17 chapters from
  American Legal Publishing into `data/title_17/raw/`. See `backlog/phase-05-code-text-search.md`
  for step-by-step instructions. Until done, `search_zoning_code` and `get_zoning_section` return
  a helpful error — all other 6 tools work normally.

- **MCP Inspector verification** (~30 min) — Requires local Node.js. Run:
  `npx @modelcontextprotocol/inspector python -m src.server` and verify all 8 tools appear
  and respond. See `backlog/tasks/T4-mcp-inspector-verification.md`.

- **Ollama end-to-end test** (~1 hr) — Requires local Ollama installation. Pull
  `ollama pull llama3.1:8b`, connect via Claude Desktop or Continue.dev, and test
  the Q&A pairs in `evals/zoning_qa.xml`. See `backlog/tasks/T5-ollama-llm-testing.md`.

- **Parent repo cross-reference** (~15 min) — A human with access to the parent
  `Plan_for_Chicago_2030` repo should add a link/reference to this MCP server in
  the parent README.

