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

**Build phase — improving ingestion depth, eval coverage, and front-end polish.**

All automatable acceptance criteria from `backlog/README.md` are satisfied:
- `pytest tests/ -m "not network"` → **144 passed, 5 deselected** ✅
- `ruff check src/ tests/` → **0 errors** ✅
- All 8 MCP tools registered and callable ✅
- `lookup_district("RS-3")` → FAR 0.9, height 30 ft ✅
- `calculate_development_envelope("RS-3", 5000)` → 4500 sqft ✅
- 59 districts in `data/zoning_codes.csv` ✅
- Documentation complete (README, CONTRIBUTING.md, phase docs, example conversations) ✅

## Recent Activity

- 2026-05-02: Build pass — ingestion improvements, expanded eval tests, front-end refresh:
  - **Ingestion**: Improved `parse_sections_from_text` in `scripts/ingest_title_17.py` to capture
    indented subsections and letter-suffixed sub-items (e.g. `17-15-0102-A`). The parser now uses
    `\s*` to match non-breaking space (`\xa0`) indentation from amlegal.com. Added boilerplate
    cleanup (`_clean_text`) to strip "ShareDownloadBookmarkPrint" and disclaimer text. The
    `sections.json` index grew from **130 → 1,888 sections** (16 chapters, chapters 2–17).
  - **Parser**: Also splits inline sub-item content into proper `title` + `text` fields so that
    direct lookups for any indexed section return meaningful content.
  - **SECTION_RE**: Updated in `web/gemini_client.py` to also match letter-suffixed sections
    (`17-X-XXXX-A`) so the routing layer can direct those to `get_zoning_section`.
  - **Eval tests**: Expanded `tests/test_evals.py` from 20 to 35 Q&A tests, covering Q21–Q44
    (offline: district lookup, development envelope, code search, routing).
  - **Routing tests**: Added 8 new tests to `tests/test_gemini_tool_routing.py` covering
    structured prompts, developer-style questions, rezoning comparisons, map URL, and
    letter-suffixed section routing. Total routing tests: 16.
  - **Front-end**: Refreshed `web/templates/index.html` — Chicago Municipal blue/red palette,
    Inter font, stats bar (1,888 sections, 8 tools, 200+ district codes), improved typography,
    typing indicator, and 5 suggestion chips.
  - **validate_index**: Now warns specifically about missing Chapter 17-1 (separate from the
    general missing-chapters warning) without false-positives on the test fixture.
  - All **144 offline tests pass** (up from 118 before this pass).

- 2026-04-30: Web deployment phase started — adding `web/` (Flask+Gemini) layer + GitHub Actions CI/CD for Cloud Run. Title 17 confirmed already ingested locally. Ollama testing superseded by Gemini approach.
- 2026-04-30: Web layer complete — `web/app.py`, `web/gemini_client.py`, `web/tool_bridge.py`, `web/templates/index.html`, `.github/workflows/deploy-cloud-run.yml`, updated `Dockerfile` and `pyproject.toml`.
- 2026-04-22: Closeout complete — all automated acceptance criteria verified.

## Next Recommended Step

**Validate phase.** Run `python scripts/ingest_title_17.py --validate` after optionally adding
`data/title_17/raw/chapter_17-1.txt` (the only missing chapter). Then execute `eval_live_web.py`
against the deployed Cloud Run URL to measure live eval pass-rate against the 44-question harness.

## Artifacts

| Artifact | Location | Status |
|---|---|---|
| STATUS.md | `./STATUS.md` | updated |
| FEEDBACK.md | `./FEEDBACK.md` | created |
| Backlog README | `backlog/README.md` | created |
| Data sources doc | `backlog/data_sources.md` | created |
| `.gitignore` | `.gitignore` | created |
| Phase 5 — Code Search | `backlog/phase-05-code-text-search.md` | complete — 1,888 sections indexed |
| Phase 6 — Integration | `backlog/phase-06-integration-and-eval.md` | code complete; live eval pending |
| Phase 7 — Docs | `backlog/phase-07-documentation.md` | complete |
| Squad team roster | `.squad/team.md` | created |
| Squad routing rules | `.squad/routing.md` | created |
| Squad decisions log | `.squad/decisions.md` | updated |
| Sprint plan | `.squad/sprint.md` | created |

## Needs Human Input

- **Chapter 17-1 download** (~15 min) — Copy-paste Chapter 17-1 (Title, Purpose, and
  Definitions) from amlegal.com into `data/title_17/raw/chapter_17-01.txt`, then run
  `python scripts/ingest_title_17.py` to rebuild the index with all 17 chapters.

- **Live eval run** (~15 min) — Execute `python scripts/eval_live_web.py --base-url <CLOUD_RUN_URL>`
  to measure pass-rate against the 44-question harness. The last known score was 14/20 (70%)
  on 20 questions; the full 44-question target is 100%.

- **MCP Inspector verification** (~30 min) — Run `npx @modelcontextprotocol/inspector python -m src.server`.

