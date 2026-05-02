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

**Build phase — expanding test coverage, ingestion quality, and front-end polish (per FEEDBACK.md).**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **169 passed, 5 deselected** ✅
- `ruff check src/ tests/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-02 (this pass): Expanded test coverage, improved ingestion, redesigned front-end:
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

- 2026-05-02 (previous pass): Build pass — ingestion improvements, expanded eval tests, front-end refresh.
  - **Ingestion**: Improved `parse_sections_from_text` in `scripts/ingest_title_17.py` to capture
    indented subsections and letter-suffixed sub-items (e.g. `17-15-0102-A`). The parser now uses
    `\s*` to match non-breaking space (`\xa0`) indentation from amlegal.com. Added boilerplate
    cleanup (`_clean_text`) to strip "ShareDownloadBookmarkPrint" and disclaimer text. The
    `sections.json` index grew from **130 → 1,888 sections** (16 chapters, chapters 2–17).
  - **Parser**: Also splits inline sub-item content into proper `title` + `text` fields so that
    direct lookups for any indexed section return meaningful content.
  - **SECTION_RE**: Updated in `web/gemini_client.py` to also match letter-suffixed sections
    (`17-X-XXXX-A`) so the routing layer can direct those to `get_zoning_section`.
  - **Eval tests**: Expanded `tests/test_evals.py` from 20 to 35 Q&A tests, covering Q21–Q44
    (offline: district lookup, development envelope, code search, routing).
  - **Routing tests**: Added 8 new tests to `tests/test_gemini_tool_routing.py` covering
    structured prompts, developer-style questions, rezoning comparisons, map URL, and
    letter-suffixed section routing. Total routing tests: 16.
  - **Front-end**: Refreshed `web/templates/index.html` — Chicago Municipal blue/red palette,
    Inter font, stats bar (1,888 sections, 8 tools, 200+ district codes), improved typography,
    typing indicator, and 5 suggestion chips.
  - **validate_index**: Now warns specifically about missing Chapter 17-1 (separate from the
    general missing-chapters warning) without false-positives on the test fixture.
  - All **144 offline tests pass** (up from 118 before this pass).

- 2026-04-30: Web deployment phase started — adding `web/` (Flask+Gemini) layer + GitHub Actions CI/CD for Cloud Run. Title 17 confirmed already ingested locally. Ollama testing superseded by Gemini approach.
- 2026-04-30: Web layer complete — `web/app.py`, `web/gemini_client.py`, `web/tool_bridge.py`, `web/templates/index.html`, `.github/workflows/deploy-cloud-run.yml`, updated `Dockerfile` and `pyproject.toml`.
- 2026-04-22: Closeout complete — all automated acceptance criteria verified.

## Next Recommended Step

**Validate phase.** Run `python scripts/ingest_title_17.py --validate` after optionally adding
`data/title_17/raw/chapter_17-1.txt` (the only missing chapter). Then execute `eval_live_web.py`
against the deployed Cloud Run URL to measure live eval pass-rate against the 44-question harness.

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
  to measure pass-rate against the 44-question harness. The last known score was 14/20 (70%)
  on 20 questions; the full 44-question target is 100%.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.

