# STATUS — chicago-zoning-mcp

| Field | Value |
|---|---|
| Phase | Build |
| Last Updated | 2026-05-03 (build pass 6) |
| Squad Template | data_pipeline |
| Priority | low |
| Blocking | None for automated work — see "Needs Human Input" below for manual follow-ups |
| GitHub Repo | https://github.com/adkf37/chicago-zoning-mcp |

## Current Objective

**Build phase — eval suite expanded to 400 questions; 537 tests passing.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **537 passed, 5 deselected** ✅
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-03 (this pass): Eval suite expanded to 400 questions (Q381–Q400); 537 tests passing:
  - **Eval suite extended to Q381–Q400** — Added 20 new questions to `evals/zoning_qa.xml`
    addressing FEEDBACK request for zoning code text questions and broader attribute coverage:
    - Q381–Q386: Fixture-based code-search questions (planned development, floor area ratio,
      special use permit) — `search_zoning_code` and `get_zoning_section` tests using the
      in-memory fixture index; no live Title 17 index required.
    - Q387–Q389: Minimum lot area per dwelling unit for RS-3 (2500), RM-5 (500), RT-4 (1000).
    - Q390–Q392: Setback attributes — RM-6 rear yard (30 ft), POS-1 side (15 ft),
      POS-2 rear yard (25 ft).
    - Q393–Q396: Development envelope calculations — DS-5×3000=15000, DX-7×3000=21000,
      C2-5×2000=10000, RM-5×4000=8000.
    - Q397: DS-3 height (50 ft).
    - Q398–Q399: Comparison pairs RM-5/RM-5.5 (RM-5.5 higher), C2-3/C2-5 (C2-5 higher).
    - Q400: DX-7 lot area per dwelling unit (145 sq ft).
  - **20 new offline eval tests** — `tests/test_evals.py` Q381–Q400, all offline.
  - **Impact**: Test count: 517 → 537; eval suite: 380 → 400 questions.
  - **Coverage rationale**: Addresses FEEDBACK request for more zoning code text questions
    (6 fixture-based code search tests); fills minimum lot area per unit gaps (RS-3, RM-5,
    RT-4 previously untested for this attribute); adds setback coverage for POS and RM-6;
    adds envelope/comparison coverage for DS-5, DX-7, C2-5, RM-5, RM-5/RM-5.5, C2-3/C2-5.

- 2026-05-03 (previous pass): Eval suite expanded to 380 questions (Q361–Q380); 517 tests passing.
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
| Eval suite | `evals/zoning_qa.xml` | 400 questions (Q1–Q400) |
| Eval tests | `tests/test_evals.py` | 537 tests passing |
| Frontend | `web/templates/index.html` | redesigned — capabilities cards, larger hero |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 400-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.

