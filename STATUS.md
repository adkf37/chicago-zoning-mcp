# STATUS — chicago-zoning-mcp

| Field | Value |
|---|---|
| Phase | Build |
| Last Updated | 2026-05-04 (build pass 9) |
| Squad Template | data_pipeline |
| Priority | low |
| Blocking | None for automated work — see "Needs Human Input" below for manual follow-ups |
| GitHub Repo | https://github.com/adkf37/chicago-zoning-mcp |

## Current Objective

**Build phase — eval suite expanded to 440 questions; 577 tests passing; frontend enhanced.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **577 passed, 5 deselected** ✅
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-04 (this pass): Expanded eval suite from 420 → 440 questions (Q421–Q440).
  - Added coverage for undertested districts: M1-2, M2-3, M3-3, DX-12, DX-16, DC-16, DR-10,
    DS-3, DS-5, POS-1, POS-2, C3-2, B3-5, C2-3.
  - Added cross-series comparison questions (DX-12 vs DX-16, DC-12 vs DC-16).
  - Added development envelope calculations for C3-2 and M1-2.
  - Added 20 new offline test functions in `tests/test_evals.py` (Q421–Q440).
  - Test count: 557 → 577 passed.
  - Frontend: added 4th capability card (Address Zoning), added "How it Works" strip,
    updated capabilities grid to 4 columns, expanded suggestion chips.

- 2026-05-04 (previous pass): Corrected inaccurate `data/zoning_codes.csv` values sourced from
  secondcityzoning.org. Key corrections:
  - RS-1 lot area: 6500 → 6250 sq ft; RT-3.5 lot_area_per_unit: 1650 → 1250 sq ft.
  - RM-4.5 FAR: 1.5 → 1.7; RM-5/RM-5.5/RM-6/RM-6.5 lot_area_per_unit corrected.
  - B/C -1 districts: FAR 1.0 → 1.2; height updated to 38 ft formula; residential density added.
  - B/C -2 districts: lot_area_per_unit 700 → 1000; height updated to varies formula.
  - B/C -3 districts: lot_area_per_unit 500 → 400; height updated to varies formula.
  - DR/DX/DS tall-building districts: heights set to None (PD required).
  - Updated 420 eval questions in evals/zoning_qa.xml and 80 test assertions in test_evals.py.
  - Integration test updated to use M1-1 (no residential) instead of B1-1.

- 2026-05-03 (previous pass): Eval suite expanded to 400 questions (Q381–Q400); 537 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 360 questions (Q341–Q360); 497 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 340 questions (Q321–Q340); 477 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 320 questions (Q301–Q320); 457 tests passing.
- 2026-05-03 (previous pass): Fixed inaccurate side setback data per FEEDBACK.md; 419 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 280 questions (Q261–Q280); 419 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 260 questions (Q241–Q260); 399 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 240 questions (Q221–Q240); 379 tests passing.
- 2026-05-02 (previous pass): Eval suite expanded to 200 questions; 339 tests passing.

## Next Recommended Step

**Validate phase.** Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to
measure live eval pass-rate against the full 440-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is ≥90% on 440 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 440 questions (Q1–Q440) |
| Eval tests | `tests/test_evals.py` | 577 tests passing |
| Frontend | `web/templates/index.html` | enhanced — 4 capability cards, "How it Works" strip, expanded suggestions |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 440-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.
