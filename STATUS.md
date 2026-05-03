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

**Build phase — eval suite expanded to 220 questions; 359 tests passing.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **359 passed, 5 deselected** ✅ (up from 339)
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-03 (this pass): Eval suite expanded to 220 questions (Q201–Q220); 359 tests passing:
  - **Eval suite expanded to Q201–Q220** — Added 20 new questions to `evals/zoning_qa.xml`
    covering: DX-7 FAR (7.0), DX-12 FAR (12.0), DR-5 FAR (5.0), DR-7 FAR (7.0),
    B2-2 height (38 ft), C1-2 FAR (2.2), M1-2 height (45 ft), RT-3.5 FAR (1.05),
    RM-5.5 FAR (2.5), B3-3 height (50 ft), DX-7 vs DX-12 comparison, DX-7 envelope
    (3000 sqft → 21,000 sqft), DR-5 envelope (4000 sqft → 20,000 sqft), B2-2 envelope
    (6000 sqft → 13,200 sqft), M1-3 height (55 ft), C3-5 FAR (5.0), POS-2 FAR (0.05),
    RM-5.5 lot area per unit (400 sqft), sign regulations code search (17-12),
    and 121 N LaSalle St address lookup (mocked → DC-16).
  - **20 new eval tests** — `tests/test_evals.py` Q201–Q220 verify district lookups for
    previously untested codes (DX-7, DX-12, DR-5, DR-7, B2-2, C1-2, M1-2, RT-3.5,
    RM-5.5, B3-3, M1-3, C3-5, POS-2), development envelopes, a comparison ranking,
    a code search for signs (17-12 fixture), and a mocked address lookup (121 N LaSalle St → DC-16).
  - **Impact**: Test count: 339 → 359; eval suite: 200 → 220 questions.

- 2026-05-02 (previous pass): Eval suite expanded to 200 questions; 339 tests passing.
- 2026-05-02 (previous pass): Eval suite expanded to 180 questions; frontend redesigned.
- 2026-05-02 (previous pass): Eval suite expanded to 160 questions; 299 tests passing.
- 2026-05-02 (previous pass): Eval suite expanded to 140 questions; front-end redesigned.
- 2026-05-02 (previous pass): Eval suite expanded to 120 questions; 259 tests passing.

## Next Recommended Step

**Validate phase.** Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to
measure live eval pass-rate against the full 220-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is ≥90% on 220 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 220 questions (Q1–Q220) |
| Eval tests | `tests/test_evals.py` | 359 tests passing |
| Frontend | `web/templates/index.html` | redesigned — capabilities cards, larger hero |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 220-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.
