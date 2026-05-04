# STATUS — chicago-zoning-mcp

| Field | Value |
|---|---|
| Phase | Build |
| Last Updated | 2026-05-03 (build pass 7) |
| Squad Template | data_pipeline |
| Priority | low |
| Blocking | None for automated work — see "Needs Human Input" below for manual follow-ups |
| GitHub Repo | https://github.com/adkf37/chicago-zoning-mcp |

## Current Objective

**Build phase — eval suite expanded to 420 questions; 557 tests passing.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **557 passed, 5 deselected** ✅
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-03 (this pass): Eval suite expanded to 420 questions (Q401–Q420); 557 tests passing:
  - **Eval suite extended to Q401–Q420** — Added 20 new questions to `evals/zoning_qa.xml`
    covering B/C/M/DR/DX district series gaps, front-yard/rear-yard setbacks, and comparisons:
    - Q401–Q403: B1-2 FAR (2.2), B1-3 height (45 ft), C1-2 FAR (2.2).
    - Q404–Q405: M1-3 FAR (3.0), M2-2 height (45 ft).
    - Q406–Q408: DR-5 FAR (5.0), DR-7 height (80 ft), DR-3 lot area per unit (500 sq ft).
    - Q409–Q410: DX-5 FAR (5.0), DC-12 FAR (12.0).
    - Q411–Q412: Development envelopes — RS-1×5000=2500 sqft, B1-3×10000=30000 sqft.
    - Q413–Q414: Comparison pairs — RS-1/RS-2 (RS-2 higher), DR-3/DR-5 (DR-5 higher).
    - Q415–Q417: Front/rear yard setbacks — RS-1 front (20 ft), RS-2 rear (30 ft),
      DR-3 front (15 ft).
    - Q418–Q420: RM-4.5 FAR (1.5), RM-5.5 height (55 ft), RM-5.5 lot area per unit (400 sq ft).
  - **20 new offline eval tests** — `tests/test_evals.py` Q401–Q420, all offline.
  - **Impact**: Test count: 537 → 557; eval suite: 400 → 420 questions.

- 2026-05-03 (previous pass): Eval suite expanded to 400 questions (Q381–Q400); 537 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 360 questions (Q341–Q360); 497 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 340 questions (Q321–Q340); 477 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 320 questions (Q301–Q320); 457 tests passing.
- 2026-05-03 (previous pass): Fixed inaccurate side setback data per FEEDBACK.md; 419 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 280 questions (Q261–Q280); 419 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 260 questions (Q241–Q260); 399 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 240 questions (Q221–Q240); 379 tests passing.
- 2026-05-02 (previous pass): Eval suite expanded to 200 questions; 339 tests passing.
- 2026-05-02 (previous pass): Eval suite expanded to 180 questions; frontend redesigned.
- 2026-05-02 (previous pass): Eval suite expanded to 160 questions; 299 tests passing.
- 2026-05-02 (previous pass): Eval suite expanded to 140 questions; front-end redesigned.
- 2026-05-02 (previous pass): Eval suite expanded to 120 questions; 259 tests passing.

## Next Recommended Step

**Validate phase.** Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to
measure live eval pass-rate against the full 400-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is ≥90% on 400 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 420 questions (Q1–Q420) |
| Eval tests | `tests/test_evals.py` | 557 tests passing |
| Frontend | `web/templates/index.html` | redesigned — capabilities cards, larger hero |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 400-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.

