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

**Build phase — eval suite expanded to 260 questions; 399 tests passing.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **399 passed, 5 deselected** ✅ (up from 379)
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-03 (this pass): Eval suite expanded to 260 questions (Q241–Q260); 399 tests passing:
  - **Eval suite expanded to Q241–Q260** — Added 20 new questions to `evals/zoning_qa.xml`
    covering: RS-2 FAR (0.65), RS-2 front yard setback (15 ft), RS-2 rear yard setback (30 ft),
    RM-5 FAR (2.0), B1-1 FAR (1.0), DS-3 FAR (3.0), POS-1 FAR (0.1), RT-3.5 lot area per unit
    (1650 sqft), RS-2 envelope (6000 → 3900 sqft), RM-5 envelope (8000 → 16000 sqft), DS-3
    envelope (4000 → 12000 sqft), B3-3 vs B3-5 comparison (B3-5 higher FAR), C1-2 vs C1-3
    comparison (C1-3 higher FAR), M1-1 vs M1-2 comparison (M1-2 higher FAR), RS-3 side yard
    setback (combined 8 ft), RS-1 minimum lot area (6500 sqft), 3 new code search queries
    (FAR measurement, secondary dwelling unit, planned development site plan), and mocked Wrigley
    Field address lookup (1060 W Addison → B3-1).
  - **20 new eval tests** — `tests/test_evals.py` Q241–Q260 cover: previously untested standalone
    FAR values (RS-2, RM-5, B1-1, DS-3, POS-1), RS-2 setbacks (front and rear), RT-3.5 lot area
    per unit, 3 development envelope calculations, 3 new comparison pairs (B3-3/B3-5, C1-2/C1-3,
    M1-1/M1-2), first-ever side setback test (RS-3), first-ever minimum lot area test (RS-1),
    3 new code search fixture queries, and a mocked Wrigley Field address lookup.
  - **Impact**: Test count: 379 → 399; eval suite: 240 → 260 questions.

- 2026-05-03 (previous pass): Eval suite expanded to 240 questions (Q221–Q240); 379 tests passing.
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
