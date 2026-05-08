# Chicago Zoning Assistant

A Chicago zoning tool with two modes: a **web chat app** powered by Gemini and a **local MCP server** for Claude Desktop, Continue.dev, and other MCP-compatible clients. Exposes **10 tools** for district lookups, development calculations, address-based parcel queries, and full-text search of Title 17 (Chicago Zoning Ordinance).

**67** district records · **1,888** indexed Title 17 sections · **175** tests

## What it does

Ask questions like:
- *"What's the zoning at 1521 N Bell Ave?"*
- *"What does RS-3 zoning mean?"*
- *"Compare RS-3 and RT-4 districts side by side"*
- *"How many units can I build on a 5,000 sq ft RS-3 lot?"*
- *"What uses are permitted in B2-1?"*
- *"What does the zoning code say about parking requirements?"*
- *"Which residential districts allow at least 4 units on a 6,000 sq ft lot?"*
- *"What does section 17-15-0100 say?"*

No RAG pipeline, no vector database. Structured data gets structured lookups; zoning code text gets section-indexed keyword search. The web app maintains **conversation context** across turns, so follow-up questions like *"parking requirements there"* automatically apply to the address you asked about earlier.

## Architecture

```
                  ┌─────────────────────────────┐
                  │   Web Chat (Flask + Gemini)  │  browser → localhost:8080
                  │                              │  or Cloud Run
                  │  Tool routing + session ctx  │
                  └──────────────┬──────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
  ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐
  │ District     │    │ Geospatial      │    │ Code Search     │
  │ Lookup Tools │    │ Tools           │    │ Tools           │
  │              │    │                 │    │                 │
  │ zoning_      │    │ Chicago Socrata │    │ Title 17        │
  │ codes.csv    │    │ API (live)      │    │ section index   │
  └──────────────┘    └─────────────────┘    └─────────────────┘

  ┌──────────────────────────────────────────────────────────┐
  │   FastMCP Server (stdio)                                 │  Claude Desktop,
  │   Same 10 tools exposed over MCP protocol               │  Continue.dev, etc.
  └──────────────────────────────────────────────────────────┘
```

## Tools

| Tool | Description |
|------|-------------|
| `lookup_district` | Look up a district by code (e.g. RS-3). Returns FAR, height limits, setbacks, description. |
| `compare_districts` | Side-by-side comparison of two zoning districts with a differences summary. |
| `list_district_types` | List all 67 districts, optionally filtered by category (Residential, Commercial, etc). |
| `calculate_development_envelope` | Given a district code and lot size, return max floor area, unit count, height, and setbacks. |
| `get_parcel_zoning` | Live lookup of the zoning district for a Chicago street address or lat/lng coordinates. |
| `get_zoning_map_url` | Get a link to the Chicago Zoning Map viewer centered on a location. |
| `search_zoning_code` | Full-text keyword search across 1,888 sections of Title 17 (Chicago Zoning Ordinance). |
| `get_zoning_section` | Retrieve a specific Title 17 section by number (e.g. `17-15-0100`). |
| `find_districts_meeting_criteria` | Find districts that meet FAR, unit-count, or category criteria. |
| `get_use_table` | Return the permitted-use table for a district (Permitted / Special Use / Not Allowed). |

## Quick Start — Web App

The web app is the easiest way to use the assistant. It requires a Google Gemini API key (free tier available).

```bash
git clone <repo-url>
cd chicago-zoning-mcp

# Install web dependencies
pip install -e ".[web]"

# Set your Gemini API key
export GOOGLE_API_KEY=your_key_here   # Windows: $env:GOOGLE_API_KEY="..."

# Start the server
flask --app web.app run --port 8080
```

Then open [http://localhost:8080](http://localhost:8080).

### Getting a Gemini API key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a key (free tier supports Gemini 2.5 Flash)
3. Set `GOOGLE_API_KEY` in your environment

### Changing the model

```bash
export GEMINI_MODEL=gemini-2.5-pro   # default: gemini-2.5-flash
```

## Quick Start — MCP Server (Claude Desktop / Continue.dev)

The MCP server uses a local Ollama model and requires no API key.

```bash
pip install -e ".[dev]"
ollama pull llama3.1:8b   # minimum; llama3.1:70b recommended
python -m src.server
```

### Connect to Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "chicago-zoning": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/chicago-zoning-mcp"
    }
  }
}
```

### Connect to Continue.dev (VS Code)

Add to your Continue config:

```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "transport": {
          "type": "stdio",
          "command": "python",
          "args": ["-m", "src.server"],
          "cwd": "/path/to/chicago-zoning-mcp"
        }
      }
    ]
  }
}
```

## Docker

The Dockerfile builds a production web app image (gunicorn on `$PORT`). The `docker-compose.yml` runs the MCP stdio server with a sidecar Ollama instance.

```bash
# Web app (production)
docker build -t chicago-zoning .
docker run -p 8080:8080 -e GOOGLE_API_KEY=your_key chicago-zoning

# MCP server + Ollama (local)
docker compose up
# Pulls llama3.1:8b automatically; override with OLLAMA_MODEL=llama3.1:70b
```

## Data Sources

| Source | Contents |
|--------|----------|
| `data/zoning_codes.csv` | 67 Chicago zoning districts — FAR, height limits, setbacks, descriptions |
| `data/title_17/sections.json` | 1,888 indexed sections of Title 17 (Chicago Zoning Ordinance) |
| `data/title_17/raw/` | Raw chapter text files (17-02 through 17-17) |
| [Chicago Data Portal](https://data.cityofchicago.org/resource/dj47-wfun.geojson) | Live Socrata API for parcel-level zoning lookups |

## Setting Up Title 17 Text Search

The `search_zoning_code` and `get_zoning_section` tools require a pre-built section index. The index is already committed at `data/title_17/sections.json` (1,888 sections). To rebuild it from the raw chapter files:

```bash
python scripts/ingest_title_17.py
```

To add or refresh raw chapter text, save plain-text content from [American Legal Publishing](https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2647389) to `data/title_17/raw/chapter_17-N.txt` (one file per chapter), then re-run the script.

## Example Conversations

**District lookup:**
> *"What does RS-3 zoning mean and what can I build there?"*
>
> RS-3 is a Residential Single-Unit District — the most common zoning in Chicago neighborhoods. Key limits: FAR 0.9 (a 5,000 sq ft lot allows up to 4,500 sq ft of floor area), maximum height ~30 ft, required rear yard of 28.75% of lot depth, and one primary + one accessory dwelling unit permitted.

**Development calculator:**
> *"I'm looking at a 6,000 sq ft lot zoned RS-3. How much could I build?"*
>
> On a 6,000 sq ft RS-3 lot: max floor area **5,400 sq ft** (FAR 0.9), max **2 dwelling units**, max height ~30 ft, front setback 20 ft. This is an estimate — overlays, lot shape, and planned development designations can affect actual limits.

**Address lookup + tool chaining:**
> *"What's the zoning at 4521 N Clark St, and what could I build on a 3,000 sq ft lot there?"*
>
> 4521 N Clark St is zoned **B3-2** (Community Shopping District). On a 3,000 sq ft lot: max floor area **6,000 sq ft** (FAR 2.0), mixed commercial/residential uses permitted.
> *(Automatically called `get_parcel_zoning` then `calculate_development_envelope`.)*

**Conversational follow-up:**
> *"What's the zoning at 1521 N Bell Ave?"* → RS-3
>
> *"What are the parking requirements there?"*
>
> The assistant remembers the address and looks up parking requirements specifically for RS-3 residential districts, rather than giving a generic answer.

**District comparison:**
> *"If my RS-3 lot got rezoned to RT-4, how much more could I build?"*
>
> | | RS-3 | RT-4 |
> |---|---|---|
> | FAR | 0.9 | 1.2 |
> | Max units (5,000 sqft lot) | 2 | 5 |
>
> Rezoning to RT-4 increases allowable floor area by 33% and permits up to 5 dwelling units instead of 2.

**Use table:**
> *"Can I open a restaurant in B2-1?"*
>
> Yes — eating and drinking establishments are **Permitted (P)** in B2-1. Taverns and bars require **Special Use (S)** approval.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests (offline only — skips live API calls)
pytest tests/ -m "not network" -q

# Run all tests including live API calls
pytest tests/ -q

# Inspect tools interactively with MCP Inspector
npx @modelcontextprotocol/inspector python -m src.server

# Lint
ruff check src/ web/ tests/
```

### Project layout

```
src/
  server.py          # FastMCP server entry point
  data_loader.py     # CSV district data
  geocoder.py        # Chicago bounds helpers
  tools/             # 10 MCP tool implementations
web/
  app.py             # Flask routes + session management
  gemini_client.py   # Gemini function-calling loop + tool routing
  tool_bridge.py     # Sync wrappers that connect web layer to src/tools
  templates/
    index.html       # Chat UI
scripts/
  ingest_title_17.py # Build Title 17 section index
  smoke_test.py      # Quick end-to-end sanity check
data/
  zoning_codes.csv   # 67 district records
  title_17/          # 1,888 indexed sections + raw chapter text
tests/               # 175 tests across 11 test files
```

## License

MIT
