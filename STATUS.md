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

**Build phase — eval suite expanded to 100 questions; routing improved; 232 tests passing.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **232 passed, 5 deselected** ✅ (up from 209)
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-02 (this pass): Eval suite expanded to 100 questions; routing improved:
  - **Eval suite expanded to 100 questions** — Added Q81–Q100 to `evals/zoning_qa.xml`
    covering 20 new scenarios across previously untested districts:
    RM-4.5, RM-6.5, B1-5, C2-3, M2-2, M2-1/M2-3, DX-3, DR-3, DS-5, POS-1, C3-2,
    B2-5, M2-3, DR-5, DS-3/DS-5, plus routing edge cases for commercial/downtown
    district listing.
  - **23 new tests** — 20 eval tests (Q81–Q100) + 3 routing tests. Total: **232 passing** (was 209).
  - **Routing improved** — Added `_looks_like_list_districts_question()` in `gemini_client.py`
    to handle "What are the commercial zoning districts?" and "Show me all residential
    districts" patterns that previously fell through to no tool call. Covers:
    - `"district" + ("list" | "types" | "all")` — existing logic preserved
    - `"what are" + "zoning districts"` — new pattern for natural-language listing
    - `"show me" / "give me" + "districts"` — new pattern

- 2026-05-02 (previous pass): Ingestion word-boundary fix applied; sections.json regenerated.

- 2026-05-02 (previous pass): Eval suite expanded to 80 questions, routing improved, front-end redesigned.

- 2026-04-30: Web deployment phase started — adding `web/` (Flask+Gemini) layer.
- 2026-04-22: Closeout complete — all automated acceptance criteria verified.

## Next Recommended Step

**Validate phase.** Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to
measure live eval pass-rate against the full 100-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is 100% on 100 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 100 questions (Q1–Q100) |
| Eval tests | `tests/test_evals.py` | 232 tests passing |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 100-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.


## Recent Activity

- 2026-05-02 (this pass): Ingestion word-boundary fix:
  - **Root cause identified**: 372+ sections in `sections.json` had text starting
    mid-word (e.g. "t 2 bicycle spaces..." instead of "at least 2 bicycle spaces...").
    The parser cut single-line headers at exactly character 80, potentially splitting
    a word.
  - **Fix applied** to `scripts/ingest_title_17.py` `else` branch: use
    `rfind(" ", 0, 80)` to find last word boundary before position 80 for the title,
    and store the COMPLETE `raw_title` as body text for long (>80 char) single-line
    sections, ensuring full searchability.
  - **`sections.json` regenerated**: 1,888 sections, 0 empty — quality improved.
  - All 209 tests still pass after regeneration.

- 2026-05-02 (previous pass): Eval suite expanded to 80 questions, routing improved, front-end redesigned.
  - **Eval suite expanded to 80 questions** — Added Q66–Q80 to `evals/zoning_qa.xml` covering:
    - New district types: RS-1, RM-6, DR-7, M1-1/M1-3, POS-2, RT-3.5, RM-5.5, DS-3, B2-3, C1-5, DX-5
    - New calculations: RM-6 (FAR 4.4), POS-2 (FAR 0.05), RT-3.5 units, RM-5.5, B2-3, C1-5
    - New comparisons: M1-1 vs M1-3, DX-5 vs DX-12
    - New code searches: setback requirements, inclusionary zoning
    - New list query: manufacturing district types
  - **Routing keywords extended** — Added `inclusionary`, `setback`, `height limit`,
    `building height`, `density bonus`, `floor area` to `_looks_like_code_search`
    for better no-district code search coverage.
  - **22 new tests** — 15 eval tests (Q66–Q80) + 7 routing tests. Total: **209 passing** (was 187).
  - **Front-end redesign** — Overhauled `web/templates/index.html`:
    - Added a top navigation bar with links to Chicago DPD, Official Zoning Map, and Title 17
    - Upgraded hero section with eyebrow text, large italic headline, subtitle, and red accent glow
    - Categorized suggestion chips into three groups: Address Lookup, District Rules, Zoning Code
    - Added a professional footer with attribution and resource links
    - Uses the same visual language as Plan_for_Chicago_2030 (DM Serif + Libre Franklin,
      navy/red/cream color scheme, radial gradient accent)

- 2026-05-02 (previous pass): Ingestion pipeline improvements — **0 empty sections** (was 188):
  - **`\xa0` normalization**, numeric child aggregation, title-as-text fallback.
  - Index rebuilt: 1,888 sections, 0 empty, 0 duplicates.
  - Tests: 187 passing.

- 2026-05-02 (earlier pass): Routing keywords, eval Q56–Q65, 184 tests.

- 2026-04-30: Web deployment phase started — adding `web/` (Flask+Gemini) layer.
- 2026-04-22: Closeout complete — all automated acceptance criteria verified.

## Next Recommended Step

**Validate phase.** Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to
measure live eval pass-rate against the full 80-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is 100% on 80 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 80 questions (Q1–Q80) |
| Eval tests | `tests/test_evals.py` | 209 tests passing |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 80-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.

