# Contributing to Chicago Zoning MCP

## Development Setup

```bash
git clone <repo-url>
cd chicago-zoning-mcp
pip install -e ".[dev]"
```

## Running Tests

```bash
# Unit tests only (fast, no network required)
pytest tests/ -m "not network"

# Live API integration tests (requires internet access)
pytest tests/ -m network

# Full suite
pytest tests/
```

Tests are organized by phase:

| File | Coverage |
|------|----------|
| `tests/test_district_lookup.py` | `lookup_district`, `compare_districts`, `list_district_types` |
| `tests/test_development.py` | `calculate_development_envelope` |
| `tests/test_geospatial.py` | `get_parcel_zoning`, `get_zoning_map_url`, geocoder |
| `tests/test_code_search.py` | `search_zoning_code`, `get_zoning_section`, ingest script |
| `tests/test_integration.py` | all tools registered, tool chaining, error handling, performance |

## Project Structure

```
src/
  server.py           # FastMCP entry point — registers all tool groups
  data_loader.py      # CSV → dict with lru_cache; shared by all tools
  geocoder.py         # Nominatim geocoding with rate limiting
  tools/
    district_lookup.py  # lookup_district, compare_districts, list_district_types
    development.py      # calculate_development_envelope
    geospatial.py       # get_parcel_zoning, get_zoning_map_url
    code_search.py      # search_zoning_code, get_zoning_section
scripts/
  ingest_title_17.py  # One-time Title 17 ingestion (run manually)
data/
  zoning_codes.csv    # ~80 Chicago zoning district records
  title_17/
    raw/              # Raw .txt chapter files (gitignored, add manually)
    sections.json     # Built index (gitignored, built by ingest script)
evals/
  zoning_qa.xml       # 20 Q&A pairs for LLM response evaluation
```

## Adding a New Tool

1. Add the tool function inside the relevant `register_*_tools()` function in `src/tools/`.
2. The `@mcp.tool()` decorator automatically registers it with the MCP server.
3. Add it to `EXPECTED_TOOLS` in `tests/test_integration.py`.
4. Write unit tests covering at least: happy path, missing/bad input, and any error branch.

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting:

```bash
ruff check src/ tests/ scripts/
ruff format src/ tests/ scripts/
```

## Title 17 Data

The zoning code text is not checked in (it's on American Legal Publishing's website). To populate it:

```bash
# After manually saving chapter text files to data/title_17/raw/
python scripts/ingest_title_17.py
python scripts/ingest_title_17.py --validate
```

See the README for full instructions.
