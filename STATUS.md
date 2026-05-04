# STATUS — chicago-zoning-mcp

| Field | Value |
|---|---|
| Phase | Closeout |
| Last Updated | 2026-05-04 (build pass 11) |
| Squad Template | data_pipeline |
| Priority | low |
| Blocking | None for automated work — see "Needs Human Input" below for manual follow-ups |
| GitHub Repo | https://github.com/adkf37/chicago-zoning-mcp |

## Current Objective

**Closeout — eval tests realigned to corrected zoning_codes.csv; 597 tests passing.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **597 passed, 5 deselected** ✅
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Next Action

Closeout

## Recent Activity

- 2026-05-04 (this pass): Realigned 74 failing tests to manually corrected `data/zoning_codes.csv`.
  - Feedback ID: 2025-05-04-Aaron — Aaron manually updated the CSV; tests were still asserting old values.
  - Fixed 73 assertions in `tests/test_evals.py`, 1 in `tests/test_integration.py`.
  - Fixed XML parse error in `evals/zoning_qa.xml` (Q73 `#SKIP#` replaced with proper XML comment).
  - Corrected all `<notes>` in eval XML that referenced outdated FAR values.
  - Key data changes accommodated: B/C/M heights now text descriptions; M1-1/M2-1 FAR 1.0→1.2;
    T/PMD category→Other; POS FAR/setbacks now formula-based text; lot_area format with commas.
  - No new test questions added per FEEDBACK.md instruction.

- 2026-05-04 (previous pass): Expanded eval suite from 440 → 460 questions (Q441–Q460).
  - Test count: 577 → 597 passed.

- 2026-05-04 (previous pass): Expanded eval suite from 420 → 440 questions (Q421–Q440).
  - Test count: 557 → 577 passed.

## Next Recommended Step

**Closeout.** Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to
measure live eval pass-rate against the full 460-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is ≥90% on 460 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 460 questions (Q1–Q460) |
| Eval tests | `tests/test_evals.py` | 597 tests passing |
| Frontend | `web/templates/index.html` | enhanced — 4 capability cards, "How it Works" strip, expanded suggestions |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 440-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.
