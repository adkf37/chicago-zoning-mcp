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

**Build phase — eval suite expanded to 160 questions; 299 tests passing; full district coverage achieved.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **299 passed, 5 deselected** ✅ (up from 279)
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-02 (this pass): Eval suite expanded to 160 questions; full district coverage:
  - **Eval suite expanded to Q141–Q160** — Added 20 new questions to `evals/zoning_qa.xml`
    covering every previously-untested district: RS-1, RS-2, RT-3.5, RM-4.5, RM-5, RM-5.5,
    B1-5, B2-5, B3-1, C1-3, C2-3, M1-1, M2-1, M2-2, M2-3, DR-3, DR-5, POS-2, and two
    new comparison questions (RM-5 vs RM-5.5, M2-2 vs M2-3).
  - **20 new eval tests** — `tests/test_evals.py` Q141–Q160 verify FAR values, height limits,
    lot-area-per-unit strings, development envelope calculations, category names, and
    comparison rankings for all remaining uncovered districts.
  - **Full district coverage** — Every district code in `data/zoning_codes.csv` now has at
    least one eval question (except T and PMD, which have variable/undefined FAR values).
  - **Impact**: Test count: 279 → 299; eval suite: 140 → 160 questions.

- 2026-05-02 (previous pass): Eval suite expanded to 140 questions; front-end redesigned; routing improved.

- 2026-05-02 (previous pass): Eval suite expanded to 120 questions; 259 tests passing.

## Next Recommended Step

**Validate phase.** Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to
measure live eval pass-rate against the full 160-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is ≥90% on 160 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 160 questions (Q1–Q160) |
| Eval tests | `tests/test_evals.py` | 299 tests passing |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 160-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.
