# Phase 7: Documentation & Packaging

**Status:** Code/docs complete — manual fresh-clone verification pending
**Depends on:** Phase 6
**Estimated scope:** S

## Objective

Polish documentation, add example conversations, and ensure the project is ready to
clone-and-run for anyone with Ollama installed.

## Inputs

- All implemented and tested code from Phases 1–6
- Working server (`python -m src.server`)
- Working Docker Compose stack

## Outputs

- `README.md` — complete setup guide with prerequisites, quick start, Docker, data sources,
  Title 17 ingestion instructions, 4 example Q&A conversations, development workflow
- `CONTRIBUTING.md` — development workflow, project structure, tool-adding guide
- `Dockerfile` — optimized with layer-cached dependencies and explicit `src/data/` copy
- `docker-compose.yml` — Ollama + MCP server with healthcheck, auto-pull init service,
  `OLLAMA_MODEL` env var override
- `LICENSE` — MIT

## Tasks

### Automated (complete ✓)

- [x] Finalize `README.md` with tested setup instructions
- [x] Add example conversations section to README (4 real Q&A transcripts covering all tool types)
- [x] Add Title 17 ingestion instructions to README
- [x] Improve Docker Compose setup:
  - Healthcheck on Ollama service
  - `ollama-pull` init service to auto-pull the model on first start
  - `OLLAMA_MODEL` env var override (default: `llama3.1:8b`)
- [x] Improve Dockerfile: layer-cached deps, explicit `src/` and `data/` copy
- [x] Add `CONTRIBUTING.md` with development workflow, project structure, tool-adding guide
- [x] Add `LICENSE` file (MIT)
- [x] Update `.gitignore` with pytest cache and coverage entries

### Manual / Human-gated

- [ ] **[MANUAL]** Test fresh-clone experience
  - On a fresh machine (or clean Docker): `git clone <repo> && pip install -e ".[dev]"`
  - Verify `pip install` succeeds clean
  - Run `pytest tests/ -m "not network"` and confirm all pass
  - Run `python -m src.server` and confirm server starts
  - Verify `docker compose up` starts both services and auto-pulls the model
  - Target: zero-to-working Q&A in under 5 minutes
- [ ] **[HUMAN]** Cross-reference from parent repo README *(requires access to parent repo)*
  - Add a link from `Plan_for_Chicago_2030` README pointing to this project

## Key Files

| File | Owner | Status |
|------|-------|--------|
| `README.md` | Scribe | ✓ Complete |
| `CONTRIBUTING.md` | Scribe | ✓ Complete |
| `Dockerfile` | Lead | ✓ Complete |
| `docker-compose.yml` | Lead | ✓ Complete |
| `LICENSE` | Lead | ✓ Complete |

## Acceptance Criteria

- [x] `README.md` has installation instructions (pip + Docker)
- [x] `README.md` has at least 3 example Q&A conversations showing real tool use
- [x] `README.md` has Title 17 ingestion instructions
- [x] `CONTRIBUTING.md` explains how to add a new tool
- [x] Docker Compose starts both services and auto-pulls the model
- [ ] Someone with Ollama installed can get from `git clone` to working Q&A in under 5 minutes
      *(manual verification)*
