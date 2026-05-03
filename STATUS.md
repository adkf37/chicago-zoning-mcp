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

**Build phase — side setback data corrected; 419 tests passing.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **419 passed, 5 deselected** ✅
- `ruff check src/ tests/ web/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-03 (this pass): Fixed inaccurate side setback data per FEEDBACK.md; 419 tests passing:
  - **Corrected `data/zoning_codes.csv` side setbacks** for all R and DR districts per the
    actual zoning code (Sec. 17-2-0309 and 17-4-0406-B). Previous values were simplified
    fixed-foot numbers (e.g. "Combined 8 ft"); correct values are percentage-of-lot-width
    formulas. Key corrections:
    - RS-1: "Combined 15 ft…" → "30% of lot width (combined); each side min 5 ft or 10% of lot width"
    - RS-2: "Combined 10 ft, min 3 ft…" → "30% of lot width (combined); each side min 4 ft or 10%"
    - RS-3: "Combined 8 ft, min 2 ft…" → "20% of lot width (combined); each side min 2 ft or 8%"
    - RT-3.5/RT-4: "Combined 5 ft, min 2 ft…" → "20% of lot width (combined); each side min 2 ft or 8%, max 5 ft"
    - RM-4.5/RM-5/RM-5.5: same percentage formula as RT-3.5/RT-4
    - RM-6/RM-6.5: none for ≤50% lot coverage; ≥50% → 10% of lot width or 10% of building height, max 20 ft
    - DR-3/DR-5/DR-7/DR-10: "Combined 5 ft…" → "None (no minimum side setback in DR district per Sec. 17-4-0406-B)"
  - **Fixed `evals/zoning_qa.xml` Q255** — updated answer_contains from "8" to "20" and
    corrected notes to match the actual rule (20% of lot width, not a fixed 8 ft).
  - **Fixed `tests/test_evals.py` Q255** — assertion now checks for "20" (percentage-based
    formula) rather than "8" (old wrong fixed value).

- 2026-05-03 (previous pass): Eval suite expanded to 280 questions (Q261–Q280); 419 tests passing.
  - **Eval suite extended to Q261–Q280** — Added 20 new questions to `evals/zoning_qa.xml`
    covering the least-tested districts and attributes: C1-1 FAR (1.0), C1-5 FAR (5.0),
    C2-1 FAR (1.0), C2-2 FAR (2.2), B1-5 FAR (5.0), B2-5 FAR (5.0), C2-3 height (50 ft),
    C3-1 FAR (1.0), C3-2 FAR (2.2), RM-5.5 FAR (2.5), B1-1.5 FAR (1.5), DX-3 FAR (3.0),
    DC-12 FAR (12.0), DR-7 FAR (7.0), DR-10 FAR (10.0), M1-3 FAR (3.0), M2-3 FAR (3.0),
    M3-3 FAR (3.0), C2-1 vs C2-3 comparison (C2-3 higher FAR), RM-5.5 envelope
    (3000 → 7500 sqft).
  - **20 new eval tests** — `tests/test_evals.py` Q261–Q280 cover: 7 previously least-tested
    districts (C1-1, C1-5, C2-1, C2-2, C3-1, C3-2, M3-3) with standalone FAR tests; 6
    additional district FAR tests (B1-5, B2-5, RM-5.5, B1-1.5, M1-3, M2-3); 4 downtown
    district FAR tests (DX-3, DC-12, DR-7, DR-10); 1 new height test (C2-3); 1 new comparison
    pair (C2-1 vs C2-3); 1 new envelope calculation (RM-5.5 × 3000).
  - **Impact**: Test count: 399 → 419; eval suite: 260 → 280 questions.

- 2026-05-03 (previous pass): Eval suite expanded to 260 questions (Q241–Q260); 399 tests passing.
- 2026-05-03 (previous pass): Eval suite expanded to 240 questions (Q221–Q240); 379 tests passing.
- 2026-05-02 (previous pass): Eval suite expanded to 200 questions; 339 tests passing.
- 2026-05-02 (previous pass): Eval suite expanded to 180 questions; frontend redesigned.
- 2026-05-02 (previous pass): Eval suite expanded to 160 questions; 299 tests passing.
- 2026-05-02 (previous pass): Eval suite expanded to 140 questions; front-end redesigned.
- 2026-05-02 (previous pass): Eval suite expanded to 120 questions; 259 tests passing.

## Next Recommended Step

**Validate phase.** Run `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>` to
measure live eval pass-rate against the full 280-question harness. Prior live eval score
was 14/20 (70%) on 20 questions; the new target is ≥90% on 280 questions.

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
| Eval suite | `evals/zoning_qa.xml` | 280 questions (Q1–Q280) |
| Eval tests | `tests/test_evals.py` | 419 tests passing |
| Frontend | `web/templates/index.html` | redesigned — capabilities cards, larger hero |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 280-question harness.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.
