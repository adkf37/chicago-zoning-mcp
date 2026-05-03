# STATUS — chicago-zoning-mcp

| Field | Value |
|---|---|
| Phase | Build |
| Last Updated | 2026-05-03 (build pass 5) |
| Squad Template | data_pipeline |
| Priority | low |
| Blocking | None for automated work — see "Needs Human Input" below for manual follow-ups |
| GitHub Repo | https://github.com/adkf37/chicago-zoning-mcp |

## Current Objective

**Build phase — eval suite expanded to 380 questions; 517 tests passing.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **517 passed, 5 deselected** ✅
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-03 (this pass): Eval suite expanded to 380 questions (Q361–Q380); 517 tests passing:
  - **Eval suite extended to Q361–Q380** — Added 20 new questions to `evals/zoning_qa.xml`
    filling coverage gaps in under-tested districts and attribute types:
    - C1-2 height (38 ft), B1-5 lot area per unit (200 sq ft), C2-2 lot area per unit (700 sq ft)
    - B2-3 FAR (3.0), B2-5 envelope (1000→5000), C3-5 lot area per unit (200 sq ft)
    - B1-1.5 envelope (2000→3000), B1-2 envelope (5000→11000)
    - B2-2 lot area per unit (700 sq ft), B3-3 lot area per unit (500 sq ft)
    - C3-1 envelope (5000→5000), C3-2 lot area per unit (700 sq ft)
    - M2-1 envelope (3000→3000), M2-2 vs M3-3 comparison (M3-3 higher)
    - DX-5 envelope (2000→10000), DR-3 lot area per unit (500 sq ft)
    - POS-1 vs POS-2 comparison (POS-1 higher FAR), RS-1 front yard setback (20 ft)
    - B1-3 vs B1-5 comparison (B1-5 higher FAR), B2-3 lot area per unit (500 sq ft)
  - **20 new offline eval tests** — `tests/test_evals.py` Q361–Q380, all offline.
  - **Impact**: Test count: 497 → 517; eval suite: 360 → 380 questions.
  - **Coverage rationale**: Districts C1-2, B1-5, C2-2, B2-3, B2-5, C3-5, B1-1.5, B1-2, B2-2,
    B3-3, C3-1, C3-2, M2-1, M2-2, M3-3, DX-5, DR-3, POS-1, POS-2 each had 3–6 questions
    (below average). The new questions fill missing attribute types (lot area per unit, envelope,
    comparison, height, setback) for each of these districts, bringing them closer to average
    coverage depth.

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
measure live eval pass-rate against the full 380-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is ≥90% on 380 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 380 questions (Q1–Q380) |
| Eval tests | `tests/test_evals.py` | 517 tests passing |
| Frontend | `web/templates/index.html` | redesigned — capabilities cards, larger hero |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 380-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.
