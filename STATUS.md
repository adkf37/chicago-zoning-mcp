<!-- maestro:temporary-human-block=nyc-budget-ab -->
# STATUS â€” chicago-zoning-mcp

| Field | Value |
|---|---|
| Phase | Closeout |
| Last Updated | 2026-05-04 (closeout reviewed) |
| Squad Template | data_pipeline |
| Priority | low |
| Blocking | Human follow-up required for Title 17 ingestion, MCP Inspector/Ollama checks, Docker verification, and parent repo cross-reference |
| Next Action | Human Blocked |
| GitHub Repo | https://github.com/adkf37/chicago-zoning-mcp |


## Maestro Temporary Pause

- 2026-06-03: Temporarily human-blocked by Maestro so the NYC budget A/B experiment can run without queue starvation. Remove `<!-- maestro:temporary-human-block=nyc-budget-ab -->` and restore the previous Next Action to resume.

## Current Objective

**Closeout reviewed in the current sandbox â€” the documented setup works from a fresh clone, automated checks still pass, the eval harness is well-formed XML, and the repo is handoff-ready except for manual / external verification that keeps the loop human-blocked.**

Validated in this pass:
- `pytest tests/ -m "not network"` â†’ **598 passed, 5 deselected** âœ…
- `ruff check src/ tests/ web/` â†’ **0 errors** âœ…
- All 8 MCP tools are registered via `await mcp.list_tools()` âœ…
- `get_district("RS-3")` â†’ `floor_area_ratio` 0.9, `maximum_building_height` text present âœ…
- `calculate_development_envelope("RS-3", 5000)` â†’ **4500.0 sqft** âœ…
- `data/zoning_codes.csv` currently contains **67** district records âœ…
- `evals/zoning_qa.xml` is valid XML with **460** questions âœ…
- README / handoff docs refreshed to match the current repo state âœ…

Still blocked for final completion:
- `pytest tests/ -m network` â†’ **5 failed** in sandbox (live geocoding / Chicago Data Portal access unavailable)
- Title 17 download + ingestion still require manual human work
- MCP Inspector verification is still pending
- Ollama end-to-end validation is still pending (`ollama` not installed in this environment)
- Docker Compose deployment and parent repo cross-reference still need human confirmation

## Next Action

Human Blocked

## Recent Activity

- 2026-05-04 (closeout final review): Re-ran the documented closeout evidence in the current sandbox and confirmed the decision stays human-blocked.
  - `python -m pip install -e ".[dev,web]"` completed successfully.
  - `python -m ruff check src/ tests/ web/` â†’ 0 errors.
  - `python -m pytest tests/ -m "not network" --tb=short` â†’ 598 passed, 5 deselected.
  - `python -m pytest tests/ -m network --tb=short` â†’ 5 failed in sandbox (live geocoding / Chicago Data Portal).
  - Programmatic checks reconfirmed 8 registered tools, RS-3 FAR 0.9, a 4500.0 sqft RS-3 envelope on a 5,000 sqft lot,
    67 district records, and 460 eval questions.
  - Refreshed closeout artifacts only; `Next Action` remains `Human Blocked` because all remaining gates are manual or external.

- 2026-05-04 (final closeout revalidation): Confirmed the handoff state from a fresh clone environment.
  - `pip install -e ".[dev,web]"` completed successfully in the sandbox.
  - `python -m ruff check src/ tests/ web/` â†’ 0 errors.
  - `python -m pytest tests/ -m "not network" --tb=short` â†’ 598 passed, 5 deselected.
  - `python -m pytest tests/ -m network --tb=short` â†’ 5 failed in sandbox (live geocoder / Chicago Data Portal).
  - Programmatic checks reconfirmed 8 registered tools, RS-3 FAR 0.9, a 4500.0 sqft RS-3 envelope on a 5,000 sqft lot,
    67 district records, and 460 eval questions.
  - Refreshed closeout artifacts; `Next Action` remains `Human Blocked` because the remaining gates are manual or external.

- 2026-05-04 (closeout sign-off): Re-validated the final handoff state against the sprint Definition of Done.
  - `python -m ruff check src/ tests/ web/` â†’ 0 errors.
  - `python -m pytest tests/ -m "not network" --tb=short` â†’ 598 passed, 5 deselected.
  - `python -m pytest tests/ -m network --tb=short` â†’ 5 failed in sandbox (live geocoder / Chicago Data Portal).
  - Programmatic checks reconfirmed 8 registered tools, 67 district records, valid `eval_suite` XML,
    and 460 eval questions.
  - Refreshed closeout artifacts and corrected the README handoff link for the parent project.

- 2026-05-04 (closeout refresh): Repaired the eval harness and re-ran closeout validation.
  - Escaped the malformed `&lt;` token in `evals/zoning_qa.xml`, restored Q73 as a real eval entry,
    and added `tests/test_eval_xml.py` so future closeout passes verify the file parses as XML.
  - `python -m ruff check src/ tests/ web/` â†’ 0 errors.
  - `python -m pytest tests/ -m "not network" --tb=short` â†’ 598 passed, 5 deselected.
  - `python -m pytest tests/ -m network --tb=short` â†’ 5 failed in sandbox (live geocoder / Chicago Data Portal).
  - Programmatic checks confirmed 8 registered tools, 67 district records, valid `eval_suite` XML,
    and 460 eval questions.

- 2026-05-04 (this closeout pass): Re-ran the current validation and refreshed handoff artifacts.
  - `python -m ruff check src/ tests/ web/` â†’ 0 errors.
  - `python -m pytest tests/ -m "not network" --tb=short` â†’ 597 passed, 5 deselected.
  - `python -m pytest tests/ -m network --tb=short` â†’ 5 failed in sandbox (live geocoder / Chicago Data Portal).
  - Initial programmatic checks found 8 registered tools and 67 district records, but the eval XML
    parse step exposed a malformed `<` token and a commented-out Q73 that were repaired in the
    follow-up closeout refresh above.
  - Added `.squad/review_report.md` and updated closeout notes to reflect a human-blocked finish rather than a completed handoff.

- 2026-05-04 (previous build pass): Realigned 74 failing tests to manually corrected `data/zoning_codes.csv`.
  - Feedback ID: 2025-05-04-Aaron â€” Aaron manually updated the CSV; tests were still asserting old values.
  - Fixed 73 assertions in `tests/test_evals.py`, 1 in `tests/test_integration.py`.
  - Fixed XML parse error in `evals/zoning_qa.xml` (Q73 `#SKIP#` replaced with proper XML comment).
  - Corrected all `<notes>` in eval XML that referenced outdated FAR values.
  - Key data changes accommodated: B/C/M heights now text descriptions; M1-1/M2-1 FAR 1.0â†’1.2;
    T/PMD categoryâ†’Other; POS FAR/setbacks now formula-based text; lot_area format with commas.
  - No new test questions added per FEEDBACK.md instruction.

- 2026-05-04 (previous pass): Expanded eval suite from 440 â†’ 460 questions (Q441â€“Q460).
  - Test count: 577 â†’ 597 passed.

- 2026-05-04 (previous pass): Expanded eval suite from 420 â†’ 440 questions (Q421â€“Q440).
  - Test count: 557 â†’ 577 passed.

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
| Phase 5 â€” Code Search | `backlog/phase-05-code-text-search.md` | complete â€” 1,888 sections indexed (0 empty) |
| Phase 6 â€” Integration | `backlog/phase-06-integration-and-eval.md` | code complete; live eval pending |
| Phase 7 â€” Docs | `backlog/phase-07-documentation.md` | complete |
| Squad team roster | `.squad/team.md` | created |
| Squad routing rules | `.squad/routing.md` | created |
| Squad decisions log | `.squad/decisions.md` | updated |
| Closeout review report | `.squad/review_report.md` | updated |
| Sprint plan | `.squad/sprint.md` | created |
| Eval suite | `evals/zoning_qa.xml` | valid XML with 460 questions (Q1â€“Q460) |
| Tests | `tests/` | 598 passed, 5 deselected |
| Frontend | `web/templates/index.html` | enhanced â€” 4 capability cards, "How it Works" strip, expanded suggestions |

## Needs Human Input

- **Title 17 download + ingest** (~2 hrs) â€” Complete `backlog/tasks/T3-01-download-title-17-BLOCKED.md`,
  then run `python scripts/ingest_title_17.py` and `python scripts/ingest_title_17.py --validate`.

- **Live geospatial verification** (~15 min) â€” Re-run `python -m pytest tests/ -m network --tb=short`
  from an environment that can reach Nominatim and the Chicago Data Portal.

- **MCP Inspector verification** (~30 min) â€” Complete `backlog/tasks/T4-mcp-inspector-verification.md`
  and confirm all 8 tools are callable in the UI.

- **Ollama / LLM validation** (~1 hr) â€” Install Ollama, then complete
  `backlog/tasks/T5-ollama-llm-testing.md` and `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`.

- **Docker + parent repo handoff** (~30 min) â€” Verify `docker compose up` manually and add the
  requested cross-reference from the parent repo README (`T6-03`).
