# STATUS — chicago-zoning-mcp

| Field | Value |
|---|---|
| Phase | Build |
| Last Updated | 2026-05-02 |
| Squad Template | data_pipeline |
| Priority | low |
| Blocking | None for automated work — see "Needs Human Input" below for manual follow-ups |
| GitHub Repo | https://github.com/adkf37/chicago-zoning-mcp |

## Current Objective

**Build phase — expanding test coverage, routing reliability, and eval question breadth (per FEEDBACK.md).**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **184 passed, 5 deselected** ✅
- `ruff check src/ tests/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-02 (this pass): Expanded routing keywords, eval suite, and test coverage:
  - **Routing improvement**: Extended `_looks_like_code_search` in `web/gemini_client.py`
    with keywords `variance`, `special use`, `landscaping`, `landscape`, `overlay`,
    `certificate of occupancy`, `use approval`, `rezoning process`, and `application process`.
    Questions like "What is the variance process?" or "Find landscaping requirements"
    now correctly route to `search_zoning_code` even without a Title 17 index keyword trigger.
  - **Eval suite**: Added Q56–Q65 to `evals/zoning_qa.xml` (65 total), covering:
    - Q56: RS-3 front yard setback (lookup_district)
    - Q57: Variance application process (search_zoning_code)
    - Q58: Landscaping requirements (search_zoning_code)
    - Q59: RS-2 lot area per dwelling unit (lookup_district)
    - Q60: RS-3 vs RT-4 lot area per unit comparison (compare_districts)
    - Q61: B3-2 floor area on 20,000 sqft lot (calculate_development_envelope → 44,000 sqft)
    - Q62: Special use permit requirements (search_zoning_code)
    - Q63: M1-1 Manufacturing/Industrial category (lookup_district)
    - Q64: DX-7 vs DX-12 FAR comparison (compare_districts)
    - Q65: RS-2 maximum building height 30 ft (lookup_district)
  - **Routing tests**: Added 5 new routing tests (Q56/Q57/Q58/Q61/Q64) covering setback,
    variance, landscaping, large-lot B3-2 envelope, and DX district comparison. Total: 34 routing tests.
  - **Eval tests**: Added 10 new eval tests (Q56–Q65). Test count grew from **169 → 184**.
  - **Code search fixture**: Added `_CODE_SEARCH_FIXTURE_V2` to `tests/test_evals.py` with
    variance (17-13-0200), landscaping (17-11-0200), and special use (17-13-0600) sections.

- 2026-05-02 (previous pass): Expanded test coverage, improved ingestion, redesigned front-end:
  - **Ingestion**: `parse_sections_from_text` now post-processes empty parent sections by
    aggregating child subsection text (e.g. 17-2-0104-A through -E into 17-2-0104). Reduced
    empty-text sections from **368 → 188** in the rebuilt `sections.json` index. Added 2 new
    parser tests (`test_parser_populates_empty_parent_from_children`,
    `test_parser_does_not_overwrite_parent_text_when_already_set`).
  - **Index rebuilt**: `python scripts/ingest_title_17.py` run — 1,888 sections, 188 remaining
    empty (reserved/table-only sections), 0 duplicates.
  - **Eval tests**: Added Q26, Q30, Q31, Q32, Q41, Q43, Q45–Q55 to `tests/test_evals.py`.
    Test count grew from 47 → **57 eval tests**. Q45/Q46 mock geocoder + Socrata without
    network. Q51–Q55 cover homeowner ADU, district comparisons, development envelopes.
  - **Routing tests**: Added 6 new routing tests (Q45/Q46 address chain, Q47 list all,
    Q51 homeowner RS-3, Q53 height comparison, Q55 RT-4 floor area). Total: 29 routing tests.
  - **Address routing fix**: Extended `_extract_address` in `web/gemini_client.py` to also
    trigger when the question contains "build" or "built" keywords, enabling "What can I build
    at 5555 N Sheridan Rd?" to chain `get_parcel_zoning → calculate_development_envelope`.
  - **Q&A harness**: Added Q45–Q55 to `evals/zoning_qa.xml` (address-specific, code-text, and
    multi-step scenarios covering homeowner and developer audiences).
  - **Front-end**: Full redesign of `web/templates/index.html` — replaced Tailwind CDN with
    purpose-built CSS using DM Serif Display + Libre Franklin fonts (same as Plan_for_Chicago_2030),
    navy/cream/Chicago-red palette, stats bar (1,888 sections / 8 tools / 59 districts / Live),
    improved chat bubbles, tool badge styling, and 6 suggestion chips.
  - **Tests**: Total 169 passing (was 144).

- 2026-04-30: Web deployment phase started — adding `web/` (Flask+Gemini) layer + GitHub Actions CI/CD for Cloud Run. Title 17 confirmed already ingested locally. Ollama testing superseded by Gemini approach.
- 2026-04-30: Web layer complete — `web/app.py`, `web/gemini_client.py`, `web/tool_bridge.py`, `web/templates/index.html`, `.github/workflows/deploy-cloud-run.yml`, updated `Dockerfile` and `pyproject.toml`.
- 2026-04-22: Closeout complete — all automated acceptance criteria verified.

## Next Recommended Step

**Validate phase.** Run `python scripts/ingest_title_17.py --validate` after optionally adding
`data/title_17/raw/chapter_17-1.txt` (the only missing chapter). Then execute `eval_live_web.py`
against the deployed Cloud Run URL to measure live eval pass-rate against the full 65-question harness.

## Artifacts

| Artifact | Location | Status |
|---|---|---|
| STATUS.md | `./STATUS.md` | updated |
| FEEDBACK.md | `./FEEDBACK.md` | created |
| Backlog README | `backlog/README.md` | created |
| Data sources doc | `backlog/data_sources.md` | created |
| `.gitignore` | `.gitignore` | created |
| Phase 5 — Code Search | `backlog/phase-05-code-text-search.md` | complete — 1,888 sections indexed |
| Phase 6 — Integration | `backlog/phase-06-integration-and-eval.md` | code complete; live eval pending |
| Phase 7 — Docs | `backlog/phase-07-documentation.md` | complete |
| Squad team roster | `.squad/team.md` | created |
| Squad routing rules | `.squad/routing.md` | created |
| Squad decisions log | `.squad/decisions.md` | updated |
| Sprint plan | `.squad/sprint.md` | created |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 65-question harness. The last known score was 14/20 (70%)
  on 20 questions; the full 65-question target is 100%.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.

