# Phase 1: Project Scaffold & Data Foundation

**Status:** Complete
**Depends on:** None
**Estimated scope:** S

## Objective

Stand up the project structure, dependency management, and data loading layer so that all
subsequent phases have a working foundation to build on.

## Inputs

- `data/zoning_codes.csv` — zoning district reference data (ported from parent repo)

## Outputs

- `pyproject.toml` — project metadata with `fastmcp`, `httpx`, `pandas` dependencies;
  `[dev]` extras include `pytest`, `pytest-asyncio`, `pytest-mock`
- `src/server.py` — FastMCP entry point; imports and registers all tool groups
- `src/data_loader.py` — `load_zoning_districts()`, `get_district()`, `get_all_districts()`,
  `get_districts_by_category()` with `lru_cache`
- `Dockerfile` / `docker-compose.yml` — containerized deployment skeleton
- `.gitignore` — ignores `__pycache__`, `.venv`, `data/title_17/`, pytest/coverage artifacts

## Tasks

- [x] Initialize Python project with pyproject.toml (FastMCP, httpx, pandas)
- [x] Create directory structure: src/, src/tools/, tests/, scripts/, data/
- [x] Create FastMCP server entry point (src/server.py)
- [x] Port zoning_codes.csv from parent repo into data/
- [x] Implement data_loader.py — CSV → dict lookup with lru_cache
- [x] Create .gitignore
- [x] Create Dockerfile and docker-compose.yml
- [x] Verify: `pip install -e ".[dev]"` succeeds
- [x] Verify: `python -c "from src.data_loader import get_district; print(get_district('RS-3'))"` returns data

## Key Files

- `pyproject.toml` — project metadata and dependencies
- `src/server.py` — FastMCP entry point
- `src/data_loader.py` — zoning data loading and lookup
- `data/zoning_codes.csv` — zoning district reference data

## Acceptance Criteria

- `pip install -e .` works clean
- `get_district("RS-3")` returns a dict with FAR, height, setbacks, description
- `get_all_districts()` returns 50+ districts
- Server starts without error: `python -m src.server`
