# Backlog — chicago-zoning-mcp

## Project Goal

Build a locally-running MCP server that answers natural-language questions about
Chicago's zoning code with structured, accurate answers. The server exposes 8 tools
to LLM clients (Claude Desktop, Continue.dev, Ollama) covering district lookup,
development calculations, geospatial parcel queries, and full-text zoning code search.

## Success Criteria

1. **All 8 MCP tools are registered and callable** via `python -m src.server`
2. **District lookup is accurate** — `lookup_district("RS-3")` returns correct FAR, height,
   setbacks, and description from `data/zoning_codes.csv`
3. **Development calculator is accurate** — `calculate_development_envelope("RS-3", 5000)`
   returns 4,500 sqft max floor area
4. **Geospatial lookup works live** — `get_parcel_zoning(address="233 S Wacker Dr")` returns
   a valid Chicago district code via Socrata API
5. **Code search works** — `search_zoning_code("accessory dwelling unit")` returns relevant
   Title 17 sections (requires manual Title 17 ingestion step)
6. **All automated tests pass** — `pytest tests/ -m "not network"` green, no regressions
7. **Docker Compose deploys cleanly** — `docker compose up` starts both Ollama and the MCP server
8. **Documentation is complete** — README has setup instructions and 3+ example Q&A conversations

## Non-Goals

- No vector embeddings or semantic search
- No database (SQLite, Postgres, etc.) — only CSV + JSON files
- No user authentication
- No persistent state between MCP calls
- No support for addresses outside Chicago

## Phases

| Phase | Title | Status |
|-------|-------|--------|
| 01 | Project Scaffold & Data Foundation | Complete |
| 02 | Core Zoning Lookup Tools | Complete (scaffolded) |
| 03 | Development Envelope Calculator | Complete |
| 04 | Geospatial Tools | Complete |
| 05 | Zoning Code Text Search | Partially complete — blocked on manual Title 17 download |
| 06 | Integration, Testing & Evaluation | Complete |
| 07 | Documentation & Packaging | Complete |

See individual phase files (`phase-0N-*.md`) for task-level detail.

## Repository Structure

```
chicago-zoning-mcp/
├── src/
│   ├── server.py           — FastMCP entry point; registers all tools
│   ├── data_loader.py      — CSV loading with lru_cache
│   ├── geocoder.py         — Nominatim geocoding client
│   └── tools/
│       ├── district_lookup.py  — lookup_district, compare_districts, list_district_types
│       ├── development.py      — calculate_development_envelope
│       ├── geospatial.py       — get_parcel_zoning, get_zoning_map_url
│       └── code_search.py      — search_zoning_code, get_zoning_section
├── tests/                  — pytest test suite (unit + integration)
├── scripts/                — one-time data ingestion scripts
├── data/
│   ├── zoning_codes.csv    — 67 district rules (FAR, height, setbacks)
│   └── title_17/           — generated; gitignored
│       ├── raw/            — manually downloaded chapter text
│       └── sections.json   — built by ingest_title_17.py
├── evals/
│   └── zoning_qa.xml       — 460 Q&A pairs for LLM evaluation
├── Dockerfile
└── docker-compose.yml
```
