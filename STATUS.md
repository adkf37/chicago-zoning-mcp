# STATUS — chicago-zoning-mcp

| Field | Value |
|---|---|
| Phase | Closeout |
| Last Updated | 2026-05-04 (closeout sign-off) |
| Squad Template | data_pipeline |
| Priority | low |
| Blocking | Human follow-up required for Title 17 ingestion, MCP Inspector/Ollama checks, Docker verification, and parent repo cross-reference |
| GitHub Repo | https://github.com/adkf37/chicago-zoning-mcp |

## Current Objective

**Closeout reviewed against the sprint Definition of Done — automated checks still pass, the eval harness is well-formed XML, and the repo is handoff-ready except for manual / external verification that keeps the loop human-blocked.**

Validated in this pass:
- `pytest tests/ -m "not network"` → **598 passed, 5 deselected** ✅
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools are registered via `await mcp.list_tools()` ✅
- `get_district("RS-3")` → `floor_area_ratio` 0.9, `maximum_building_height` text present ✅
- `calculate_development_envelope("RS-3", 5000)` → **4500.0 sqft** ✅
- `data/zoning_codes.csv` currently contains **67** district records ✅
- `evals/zoning_qa.xml` is valid XML with **460** questions ✅
- README / handoff docs refreshed to match the current repo state ✅

Still blocked for final completion:
- `pytest tests/ -m network` → **5 failed** in sandbox (live geocoding / Chicago Data Portal access unavailable)
- Title 17 download + ingestion still require manual human work
- MCP Inspector verification is still pending
- Ollama end-to-end validation is still pending (`ollama` not installed in this environment)
- Docker Compose deployment and parent repo cross-reference still need human confirmation

## Next Action

Human Blocked

## Recent Activity

- 2026-05-04 (closeout sign-off): Re-validated the final handoff state against the sprint Definition of Done.
  - `python -m ruff check src/ tests/ web/` → 0 errors.
  - `python -m pytest tests/ -m "not network" --tb=short` → 598 passed, 5 deselected.
  - `python -m pytest tests/ -m network --tb=short` → 5 failed in sandbox (live geocoder / Chicago Data Portal).
  - Programmatic checks reconfirmed 8 registered tools, 67 district records, valid `eval_suite` XML,
    and 460 eval questions.
  - Refreshed closeout artifacts and corrected the README handoff link for the parent project.

- 2026-05-04 (closeout refresh): Repaired the eval harness and re-ran closeout validation.
  - Escaped the malformed `&lt;` token in `evals/zoning_qa.xml`, restored Q73 as a real eval entry,
    and added `tests/test_eval_xml.py` so future closeout passes verify the file parses as XML.
  - `python -m ruff check src/ tests/ web/` → 0 errors.
  - `python -m pytest tests/ -m "not network" --tb=short` → 598 passed, 5 deselected.
  - `python -m pytest tests/ -m network --tb=short` → 5 failed in sandbox (live geocoder / Chicago Data Portal).
  - Programmatic checks confirmed 8 registered tools, 67 district records, valid `eval_suite` XML,
    and 460 eval questions.

- 2026-05-04 (this closeout pass): Re-ran the current validation and refreshed handoff artifacts.
  - `python -m ruff check src/ tests/ web/` → 0 errors.
  - `python -m pytest tests/ -m "not network" --tb=short` → 597 passed, 5 deselected.
  - `python -m pytest tests/ -m network --tb=short` → 5 failed in sandbox (live geocoder / Chicago Data Portal).
  - Initial programmatic checks found 8 registered tools and 67 district records, but the eval XML
    parse step exposed a malformed `<` token and a commented-out Q73 that were repaired in the
    follow-up closeout refresh above.
  - Added `.squad/review_report.md` and updated closeout notes to reflect a human-blocked finish rather than a completed handoff.

- 2026-05-04 (previous build pass): Realigned 74 failing tests to manually corrected `data/zoning_codes.csv`.
  - Feedback ID: 2025-05-04-Aaron — Aaron manually updated the CSV; tests were still asserting old values.
  - Fixed 73 assertions in `tests/test_evals.py`, 1 in `tests/test_integration.py`.
  - Fixed XML parse error in `evals/zoning_qa.xml` (Q73 `#SKIP#` replaced with proper XML comment).
  - Corrected all `<notes>` in eval XML that referenced outdated FAR values.
  - Key data changes accommodated: B/C/M heights now text descriptions; M1-1/M2-1 FAR 1.0→1.2;
    T/PMD category→Other; POS FAR/setbacks now formula-based text; lot_area format with commas.
  - No new test questions added per FEEDBACK.md instruction.

- 2026-05-04 (previous pass): Expanded eval suite from 440 → 460 questions (Q441–Q460).
  - Test count: 577 → 597 passed.

- 2026-05-04 (previous pass): Expanded eval suite from 420 → 440 questions (Q421–Q440).
  - Test count: 557 → 577 passed.

## Next Recommended Step

**Human follow-up required.** Complete the blocked manual checks in this order:
1. Run MCP Inspector verification from `backlog/tasks/T4-mcp-inspector-verification.md`.
2. Install Ollama and run `backlog/tasks/T5-ollama-llm-testing.md`.
3. Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` against the 460-question harness.
4. Verify `docker compose up` on a human-controlled machine and add the parent repo cross-reference.

## Artifacts

| Artifact | Location | Status |
|---|---|---|
| STATUS.md | `./STATUS.md` | updated |
| FEEDBACK.md | `./FEEDBACK.md` | created |
| Backlog README | `backlog/README.md` | created |
| Data sources doc | `backlog/data_sources.md` | created |
| `.gitignore` | `.gitignore` | created |
| Phase 5 — Code Search | `backlog/phase-05-code-text-search.md` | complete — 1,888 sections indexed (0 empty) |
| Phase 6 — Integration | `backlog/phase-06-integration-and-eval.md` | code complete; live eval pending |
| Phase 7 — Docs | `backlog/phase-07-documentation.md` | complete |
| Squad team roster | `.squad/team.md` | created |
| Squad routing rules | `.squad/routing.md` | created |
| Squad decisions log | `.squad/decisions.md` | updated |
| Closeout review report | `.squad/review_report.md` | updated |
| Sprint plan | `.squad/sprint.md` | created |
| Eval suite | `evals/zoning_qa.xml` | valid XML with 460 questions (Q1–Q460) |
| Tests | `tests/` | 598 passed, 5 deselected |
| Frontend | `web/templates/index.html` | enhanced — 4 capability cards, "How it Works" strip, expanded suggestions |

## Needs Human Input

- **Title 17 download + ingest** (~2 hrs) — Complete `backlog/tasks/T3-01-download-title-17-BLOCKED.md`,
  then run `python scripts/ingest_title_17.py` and `python scripts/ingest_title_17.py --validate`.

- **Live geospatial verification** (~15 min) — Re-run `python -m pytest tests/ -m network --tb=short`
  from an environment that can reach Nominatim and the Chicago Data Portal.

- **MCP Inspector verification** (~30 min) — Complete `backlog/tasks/T4-mcp-inspector-verification.md`
  and confirm all 8 tools are callable in the UI.

- **Ollama / LLM validation** (~1 hr) — Install Ollama, then complete
  `backlog/tasks/T5-ollama-llm-testing.md` and `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`.

- **Docker + parent repo handoff** (~30 min) — Verify `docker compose up` manually and add the
  requested cross-reference from the parent repo README (`T6-03`).
