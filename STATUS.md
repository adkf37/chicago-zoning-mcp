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

**Build phase — ingestion pipeline improvement: all 1,888 indexed sections now have text.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **187 passed, 5 deselected** ✅ (was 184)
- `ruff check src/ tests/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-02 (this pass): Ingestion pipeline improvements — **0 empty sections** (was 188):
  - **`\xa0` normalization** in `parse_sections_from_text`: the title-line extraction now
    normalizes non-breaking spaces (`\xa0`) to regular spaces before detecting the `". "`
    sentence boundary. amlegal.com sometimes uses `".\xa0"` as the separator between a
    section heading and its inline body text (e.g. `"Nonconforming Uses.\xa0..."`) which
    previously caused the body content to be lost. Fixed 1 section (17-6-0404).
  - **Numeric child aggregation** (Post-process 2): empty section-group headers ending in
    a multiple of 100 (e.g. `17-2-0100 "District descriptions"`, `17-2-0200 "Allowed uses"`)
    now get a summary of their child sections' titles appended as text. This enables
    `get_zoning_section("17-2-0100")` to return useful content. Fixed ~89 header sections.
  - **Title-as-text fallback** (Post-process 3): any section still empty after the above
    steps (e.g. single-line list items like `17-3-0502-A "have a high concentration..."` and
    reserved placeholder sections) now uses the section title as its text, making every
    section keyword-searchable. Fixed ~98 remaining sections.
  - **Index rebuilt**: `python scripts/ingest_title_17.py` — 1,888 sections, **0 empty**
    (down from 188), 0 duplicates. Validation now shows only the expected chapter 17-1 warning.
  - **Tests**: Added 3 new parser tests (`test_parser_handles_nbsp_separator`,
    `test_parser_populates_header_section_from_numeric_children`,
    `test_parser_uses_title_as_text_for_list_items`). Total: **187 passing** (was 184).

- 2026-05-02 (previous pass): Expanded routing keywords, eval suite, and test coverage:
  - **Routing improvement**: Extended `_looks_like_code_search` in `web/gemini_client.py`
    with keywords `variance`, `special use`, `landscaping`, `landscape`, `overlay`,
    `certificate of occupancy`, `use approval`, `rezoning process`, and `application process`.
  - **Eval suite**: Added Q56–Q65 to `evals/zoning_qa.xml` (65 total).
  - **Routing tests**: Added 5 new routing tests. Total: 34 routing tests.
  - **Eval tests**: Added 10 new eval tests (Q56–Q65). Test count grew from **169 → 184**.

- 2026-05-02 (earlier pass): Expanded test coverage, improved ingestion, redesigned front-end:
  - **Ingestion**: Reduced empty-text sections from **368 → 188** via letter-suffix aggregation.
  - **Front-end**: Full redesign of `web/templates/index.html`.
  - **Tests**: Total 169 passing (was 144).

- 2026-04-30: Web deployment phase started — adding `web/` (Flask+Gemini) layer + GitHub Actions CI/CD for Cloud Run.
- 2026-04-22: Closeout complete — all automated acceptance criteria verified.

## Next Recommended Step

**Validate phase.** The index is now fully populated (0 empty sections). Run
`python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to measure live eval
pass-rate against the full 65-question harness. Then optionally add
`data/title_17/raw/chapter_17-01.txt` for Chapter 17-1 (Definitions) and
re-run ingestion to complete the full 17-chapter index.

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
| Sprint plan | `.squad/sprint.md` | created |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 65-question harness. The last known score was 14/20 (70%)
  on 20 questions; the full 65-question target is 100%.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.

