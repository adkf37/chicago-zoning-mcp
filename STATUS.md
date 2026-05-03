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

**Build phase — eval suite expanded to 200 questions; 339 tests passing.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **339 passed, 5 deselected** ✅ (up from 319)
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-02 (this pass): Eval suite expanded to 200 questions (Q181–Q200); 339 tests passing:
  - **Eval suite expanded to Q181–Q200** — Added 20 new questions to `evals/zoning_qa.xml`
    covering: POS-1 FAR (0.1), RM-6.5 FAR (6.6), RM-6 vs RM-6.5 comparison, B2-1 category,
    DX-3 FAR (3.0), C2-5 FAR (5.0), RS-1 lot area per unit (6500 sqft), RM-6.5 envelope
    (5000 sqft → 33,000 sqft), POS-1 height (30 ft), RS-1 vs RS-2 comparison, B3-1 category,
    C3-1 FAR (1.0), RM-4.5 height (38 ft), DX-5 lot area per unit (200 sqft), rezoning
    code search, affordable housing code search, B1-3 envelope (5000 sqft → 15,000 sqft),
    DX-5 height (65 ft), 4521 N Clark St address lookup (mocked), RM-6 units on 5800 sqft.
  - **20 new eval tests** — `tests/test_evals.py` Q181–Q200 verify district lookups for
    previously untested codes (POS-1, RM-6.5, B2-1, DX-3, C2-5, B3-1, C3-1), development
    envelopes, comparison rankings, code search topics (rezoning, affordable housing),
    and a second mocked address lookup (4521 N Clark St → B3-2).
  - **Impact**: Test count: 319 → 339; eval suite: 180 → 200 questions.

- 2026-05-02 (previous pass): Eval suite expanded to 180 questions; frontend redesigned:
  - **Eval suite expanded to Q161–Q180** — Added 20 new questions to `evals/zoning_qa.xml`
    covering: B1-1.5, M3-3, DX-16, DC-12 districts; multi-step address lookup (Willis Tower
    → DC-16, mocked); green roof/sustainability code search; certificate of zoning compliance
    search; new comparison pairs (B1-1 vs B1-1.5, DS-3 vs DS-5, RM-5 vs RM-6, B1-1.5 vs B1-2).
  - **20 new eval tests** — `tests/test_evals.py` Q161–Q180 verify FAR values, development
    envelopes, address routing (mocked), and zoning-code-text searches with new fixture sections.
  - **Frontend redesigned** — `web/templates/index.html` upgraded: larger hero headline
    (`clamp(2.4rem)`), bigger stats numbers (`clamp(1.4rem)`), subtle crosshatch background
    grid, new 3-column "Capabilities" evidence cards (replacing how-it-works section),
    color tokens aligned to Plan_for_Chicago_2030 palette.
  - **Impact**: Test count: 299 → 319; eval suite: 160 → 180 questions.

- 2026-05-02 (previous pass): Eval suite expanded to 160 questions; 299 tests passing; full district coverage achieved.

- 2026-05-02 (previous pass): Eval suite expanded to 140 questions; front-end redesigned; routing improved.

- 2026-05-02 (previous pass): Eval suite expanded to 120 questions; 259 tests passing.

## Next Recommended Step

**Validate phase.** Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to
measure live eval pass-rate against the full 200-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is ≥90% on 200 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 200 questions (Q1–Q200) |
| Eval tests | `tests/test_evals.py` | 339 tests passing |
| Frontend | `web/templates/index.html` | redesigned — capabilities cards, larger hero |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 180-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.
