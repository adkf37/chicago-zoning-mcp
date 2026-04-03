# STATUS — chicago-zoning-mcp

| Field | Value |
|---|---|
| Phase | coder |
| Last Updated | 2026-04-03 |
| Squad Template | data_pipeline |
| Priority | low |
| Blocking | Title 17 download (requires human action — see `.squad/sprint.md` T3-01) |
| GitHub Repo | https://github.com/adkf37/chicago-zoning-mcp |

## Current Objective

Sprint 1 Tier 1 complete — all 69 offline automated tests pass. Code quality pass
complete — all ruff lint warnings in `src/` and `tests/` resolved (21 issues fixed).
Remaining work is manual verification (MCP Inspector, Ollama testing, fresh-clone check)
and one human-gated step (Title 17 text download). See `.squad/sprint.md` for the full
execution plan.

## Recent Activity

- 2026-04-03: Code quality pass — fixed 21 ruff lint issues in `src/` and `tests/` (import
  ordering, line length, unused imports/variables); all 69 offline tests still pass
- 2026-04-02: Sprint Tier 1 executed — `pytest tests/ -m "not network"` → 69 passed, 5 deselected
- 2026-04-02: `.gitignore` created (was missing; prevented `__pycache__` from being ignored)
- 2026-04-02: Squad review complete — backlog gaps filled, sprint plan created
- 2026-04-01: Squad initialized — team roster, routing rules, and agent charters created
- 2026-04-01: Project activated by Maestro — GitHub repo created, agent task dispatched to Copilot

## Artifacts

| Artifact | Location | Status |
|---|---|---|
| STATUS.md | `./STATUS.md` | updated |
| FEEDBACK.md | `./FEEDBACK.md` | created |
| Backlog README | `backlog/README.md` | created |
| Data sources doc | `backlog/data_sources.md` | created |
| `.gitignore` | `.gitignore` | created (was missing from repo) |
| Phase 1 — Scaffold | `backlog/phase-01-scaffold-and-data.md` | complete — inputs/outputs added |
| Phase 2 — District Lookup | `backlog/phase-02-district-lookup-tools.md` | complete — inputs/outputs added |
| Phase 3 — Dev Calculator | `backlog/phase-03-development-calculator.md` | complete |
| Phase 4 — Geospatial | `backlog/phase-04-geospatial-tools.md` | complete |
| Phase 5 — Code Search | `backlog/phase-05-code-text-search.md` | code complete; blocked on human Title 17 download |
| Phase 6 — Integration | `backlog/phase-06-integration-and-eval.md` | code complete; manual Ollama testing pending |
| Phase 7 — Docs | `backlog/phase-07-documentation.md` | complete; manual fresh-clone check pending |
| Squad team roster | `.squad/team.md` | created |
| Squad routing rules | `.squad/routing.md` | created |
| Squad decisions log | `.squad/decisions.md` | created |
| Sprint plan | `.squad/sprint.md` | created |
| Agent charters | `.squad/agents/*/charter.md` | created |
| Agent histories | `.squad/agents/*/history.md` | created |

## Needs Human Input

- **Title 17 download** — A human must manually copy-paste Title 17 chapters from
  American Legal Publishing into `data/title_17/raw/`. See `backlog/phase-05-code-text-search.md`
  for step-by-step instructions. Estimated effort: ~2 hours. Until done, `search_zoning_code`
  and `get_zoning_section` return a helpful error — all other tools work normally.
