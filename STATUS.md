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

**Build phase — eval suite expanded to 140 questions; 279 tests passing; front-end redesigned.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **279 passed, 5 deselected** ✅ (up from 259)
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-02 (this pass): Eval suite expanded to 140 questions; front-end redesigned; routing improved:
  - **Eval suite expanded to Q121–Q140** — Added 20 new questions to `evals/zoning_qa.xml`
    covering zoning code text searches (home occupation, sign regulations, FAR definitions),
    address-pattern questions, and previously untested districts (DX-5, B1-2, B2-2, C1-1,
    C2-1, C2-5, C3-5, M1-3, B2-3).
  - **20 new eval tests** — `tests/test_evals.py` Q121–Q140 verify code-search responses,
    district FAR values, height limits, development envelopes, and comparison rankings.
  - **Front-end redesign** — `web/templates/index.html` updated with larger hero section,
    Chicago city stars (★★★★) accent, three-step "How It Works" strip, categorized
    suggestion chips, richer stats bar, and improved footer with official resource links.
    Inspired by Plan_for_Chicago_2030 visual language (DM Serif Display, navy/cream palette).
  - **System prompt improved** — Step 8 now explicitly instructs the model to call
    `search_zoning_code` for zoning code topics (parking, ADUs, signs, variances, etc.).
  - **Routing keyword expansion** — `_looks_like_code_search` now recognizes 16 additional
    phrases: home occupation, sign permit, certificate of zoning, use matrix, permitted
    uses, conditional use, bulk regulation, green roof, sustainability, open space,
    public benefits, demolition, adaptive reuse, historic preservation, transit-oriented,
    and pedestrian street.

- 2026-05-02 (previous pass): Eval suite expanded to 120 questions; 259 tests passing.

## Next Recommended Step

**Validate phase.** Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to
measure live eval pass-rate against the full 140-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is ≥90% on 140 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 140 questions (Q1–Q140) |
| Eval tests | `tests/test_evals.py` | 279 tests passing |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 140-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.


| Field | Value |
|---|---|
| Phase | Build |
| Last Updated | 2026-05-02 |
| Squad Template | data_pipeline |
| Priority | low |
| Blocking | None for automated work — see "Needs Human Input" below for manual follow-ups |
| GitHub Repo | https://github.com/adkf37/chicago-zoning-mcp |

## Current Objective

**Build phase — eval suite expanded to 120 questions; 259 tests passing.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **259 passed, 5 deselected** ✅ (up from 234)
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-02 (this pass): Eval suite expanded to 120 questions; acre routing added:
  - **Eval suite expanded to Q101–Q120** — Added 20 new questions to `evals/zoning_qa.xml`
    covering previously untested districts: DC-12, DR-10, DX-16, M3-3, B1-1.5, C1-2,
    M1-2, B3-3, RM-6.5, C2-2, B2-1, C3-1, B3-5, and an acre-based lot area question.
  - **20 new eval tests** — `tests/test_evals.py` Q101–Q120 verify exact FAR values,
    height limits, lot-area-per-unit strings, district categories, and development
    envelope calculations for the new districts.
  - **6 new routing tests** — `tests/test_gemini_tool_routing.py` adds DC-12 lookup,
    DX-16 development envelope, DC-12 vs DC-16 comparison, downtown-service list,
    and acre-based lot routing.
  - **Acre lot-area support** — Extended `_extract_lot_area` in `web/gemini_client.py`
    to parse acre-based lot sizes (e.g. "0.5 acres") and convert to sqft
    (1 acre = 43,560 sqft), enabling development envelope routing for acre-scale lots.
  - **Impact**: Test count: 234 → 259; every district in `zoning_codes.csv` now has
    at least one eval test; routing handles acre lot-area inputs.

- 2026-05-02 (previous pass): Downtown category routing fixed; 234 tests passing.
  - Extended `_extract_district_category` with "downtown residential", "downtown service",
    and "downtown" catch-all entries.
  - 2 new tests covering downtown routing precision.

- 2026-05-02 (previous pass): Eval suite expanded to 100 questions; routing improved.

- 2026-05-02 (previous pass): Ingestion word-boundary fix applied; sections.json regenerated.

- 2026-04-30: Web deployment phase started — adding `web/` (Flask+Gemini) layer.
- 2026-04-22: Closeout complete — all automated acceptance criteria verified.

## Next Recommended Step

**Validate phase.** Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to
measure live eval pass-rate against the full 120-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is 100% on 120 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 120 questions (Q1–Q120) |
| Eval tests | `tests/test_evals.py` | 259 tests passing |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 120-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.

