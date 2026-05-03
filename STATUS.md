# STATUS — chicago-zoning-mcp

| Field | Value |
|---|---|
| Phase | Build |
| Last Updated | 2026-05-03 |
| Squad Template | data_pipeline |
| Priority | low |
| Blocking | None for automated work — see "Needs Human Input" below for manual follow-ups |
| GitHub Repo | https://github.com/adkf37/chicago-zoning-mcp |

## Current Objective

**Build phase — eval suite expanded to 240 questions; 379 tests passing.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **379 passed, 5 deselected** ✅ (up from 359)
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-03 (this pass): Eval suite expanded to 240 questions (Q221–Q240); 379 tests passing:
  - **Eval suite expanded to Q221–Q240** — Added 20 new questions to `evals/zoning_qa.xml`
    covering: M1-1 height (30 ft), RM-6 height (70 ft), RM-6.5 height (80 ft), DR-5 height
    (65 ft), RS-1 front yard setback (20 ft), RT-4 lot area per unit (1000 sqft), B2-3 height
    (45 ft), C1-3 height (50 ft), PD FAR ("Varies"), RM-6 lot area per unit (200 sqft),
    list Downtown Service districts (DS-3, DS-5), RM-6 envelope (4000 sqft → 17,600 sqft),
    RM-6.5 envelope (3000 sqft → 19,800 sqft), DR-3 envelope (5000 sqft → 15,000 sqft),
    M2-1 vs M2-2 comparison (M2-2 higher FAR), B1-2 height (38 ft), RS-1 rear yard setback
    (50 ft), DR-3 height (45 ft), special use permit code search (17-13 fixture), and
    200 E Randolph St address lookup (mocked → DX-16).
  - **20 new eval tests** — `tests/test_evals.py` Q221–Q240 verify height limits for
    previously untested districts (M1-1, RM-6, RM-6.5, DR-5, B2-3, C1-3, B1-2, DR-3),
    setback values (RS-1 front yard and rear yard), lot area per unit (RT-4, RM-6),
    the PD "Varies" FAR edge case, Downtown Service district listing, 3 new development
    envelopes, a M2-1 vs M2-2 comparison, a special use permit code search, and a
    mocked address lookup (200 E Randolph St → DX-16).
  - **Impact**: Test count: 359 → 379; eval suite: 220 → 240 questions.

- 2026-05-03 (previous pass): Eval suite expanded to 220 questions; 359 tests passing.
- 2026-05-02 (previous pass): Eval suite expanded to 200 questions; 339 tests passing.
- 2026-05-02 (previous pass): Eval suite expanded to 180 questions; frontend redesigned.
- 2026-05-02 (previous pass): Eval suite expanded to 160 questions; 299 tests passing.
- 2026-05-02 (previous pass): Eval suite expanded to 140 questions; front-end redesigned.
- 2026-05-02 (previous pass): Eval suite expanded to 120 questions; 259 tests passing.

## Next Recommended Step

**Validate phase.** Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to
measure live eval pass-rate against the full 240-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is ≥90% on 240 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 240 questions (Q1–Q240) |
| Eval tests | `tests/test_evals.py` | 379 tests passing |
| Frontend | `web/templates/index.html` | redesigned — capabilities cards, larger hero |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 240-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.
