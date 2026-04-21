# Chicago Zoning MCP Server

A locally-running MCP server that lets you ask natural-language questions about Chicago's zoning code and get accurate answers. Powered by [Ollama](https://ollama.com/) for local LLM inference and [FastMCP](https://github.com/jlowin/fastmcp) for the MCP protocol layer.

## What it does

Ask questions like:
- *"What does RS-3 zoning mean?"*
- *"What's the maximum FAR for a B2-3 district?"*
- *"What's the zoning at 1060 W. Addison Street?"*
- *"Compare RS-3 and RT-4 districts side by side"*
- *"How many units can I build on a 5,000 sq ft RS-3 lot?"*
- *"What does the zoning code say about accessory dwelling units?"*

The server exposes **8 MCP tools** that the LLM calls as needed — no RAG pipeline, no vector database. Structured data gets structured lookups; zoning code text gets section-indexed keyword search.

## Architecture

```
┌─────────────────────┐
│   LLM Client        │  Claude Desktop, Continue.dev, etc.
│   (MCP Host)        │
└────────┬────────────┘
         │ MCP (stdio)
┌────────▼────────────┐
│   FastMCP Server    │  This project
│                     │
│  ┌───────────────┐  │
│  │ District      │  │  zoning_codes.csv → structured lookup
│  │ Lookup Tools  │  │
│  ├───────────────┤  │
│  │ Geospatial    │  │  Chicago Socrata API → live parcel queries
│  │ Tools         │  │
│  ├───────────────┤  │
│  │ Code Search   │  │  Title 17 section index → keyword search
│  │ Tools         │  │
│  └───────────────┘  │
└────────┬────────────┘
         │
┌────────▼────────────┐
│   Ollama            │  Local LLM inference
│   (llama3.1:8b+)    │
└─────────────────────┘
```

## Tools

| Tool | Description |
|------|-------------|
| `lookup_district` | Look up a zoning district by code (e.g. RS-3). Returns FAR, height limits, setbacks, description. |
| `compare_districts` | Side-by-side comparison of two zoning districts. |
| `list_district_types` | List all zoning districts, optionally filtered by category (Residential, Commercial, etc). |
| `calculate_development_envelope` | Given a district code and lot size, calculate max buildable area, unit count, and height. |
| `get_parcel_zoning` | Look up what zoning district applies to a specific address or lat/lng coordinate. |
| `get_zoning_map_url` | Get a link to the Chicago zoning map centered on a location. |
| `search_zoning_code` | Search the text of Title 17 (Chicago Zoning Ordinance) by keyword or topic. |
| `get_zoning_section` | Retrieve the full text of a specific Title 17 section by its number (e.g. "17-15-0100"). |

## Prerequisites

- **Python 3.10+**
- **Ollama** installed and running ([install guide](https://ollama.com/download))
- A pulled model: `ollama pull llama3.1:8b` (minimum) or `ollama pull llama3.1:70b` (recommended)

## Quick Start

```bash
# Clone and install
git clone <repo-url>
cd chicago-zoning-mcp
pip install -e ".[dev]"

# Pull the LLM model
ollama pull llama3.1:8b

# Run the MCP server
python -m src.server
```

### Connect to Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

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

```bash
docker compose up
```

This starts both Ollama and the MCP server. The Ollama model is pulled automatically on first run.

## Data Sources

- **Zoning district rules**: `data/zoning_codes.csv` — FAR, height, setbacks, descriptions for all 59 Chicago zoning districts
- **Parcel zoning**: [Chicago Data Portal](https://data.cityofchicago.org/resource/dj47-wfun.geojson) — live Socrata API queries
- **Zoning code text**: Title 17 of the Chicago Municipal Code, section-indexed in `data/title_17/sections.json`

## Setting Up Title 17 Text Search

The `search_zoning_code` and `get_zoning_section` tools require a section index built from Title 17 of the Chicago Municipal Code. This is a one-time manual step:

1. Go to [American Legal Publishing](https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2647389)
2. For each chapter (17-1 through 17-17), copy the plain text and save to `data/title_17/raw/chapter_17-N.txt`
3. Build the index:

```bash
python scripts/ingest_title_17.py
```

4. Validate the result:

```bash
python scripts/ingest_title_17.py --validate
# Should print: "Index contains 500+ sections."
```

Until the index is built, the two code search tools return a helpful error pointing to this step. All other tools work without it.

## Example Conversations

These are real outputs from the MCP server when queried through an LLM client.

**District lookup:**
> *"What does RS-3 zoning mean and what can I build there?"*
>
> RS-3 is a Residential Single-Unit District — the most common zoning in Chicago's neighborhoods. On a standard lot it allows one primary dwelling unit plus an accessory dwelling unit. Key limits: FAR 0.9 (so a 5,000 sq ft lot allows up to 4,500 sq ft of floor area), maximum height around 30 ft, and a required rear yard of 28.75% of lot depth.

**Development calculator:**
> *"I'm looking at a 6,000 sq ft lot zoned RS-3. How much could I build?"*
>
> On a 6,000 sq ft RS-3 lot:
> - **Max floor area**: 5,400 sq ft (FAR 0.9 × 6,000)
> - **Max dwelling units**: 2 (one per 2,500 sq ft of lot area)
> - **Max height**: ~30 ft
> - **Setbacks**: front 20 ft, rear 28.75% of lot depth, side varies
>
> *This is an estimate — planned development designations, lot shape, and overlays can affect actual limits.*

**Geospatial lookup + calculator (tool chaining):**
> *"What's the zoning at 4521 N Clark St, and what could I build on a 3,000 sq ft lot there?"*
>
> 4521 N Clark St is zoned **B3-2** (Community Shopping District). On a 3,000 sq ft lot:
> - **Max floor area**: 6,000 sq ft (FAR 2.0)
> - Commercial and residential mixed uses permitted
> - No minimum parking requirement in this corridor
>
> *The server called `get_parcel_zoning` then `calculate_development_envelope` automatically.*

**District comparison:**
> *"If my RS-3 lot got rezoned to RT-4, how much more could I build?"*
>
> | | RS-3 | RT-4 |
> |---|---|---|
> | FAR | 0.9 | 1.2 |
> | Max units (5,000 sqft lot) | 2 | 5 |
> | Category | Residential | Residential |
>
> Rezoning from RS-3 to RT-4 would increase your allowable floor area by 33% and potentially allow up to 5 dwelling units instead of 2.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run unit tests (no network required)
pytest tests/ -m "not network"

# Run all tests including live API calls
pytest tests/ -m network          # geospatial integration tests only
pytest tests/                     # everything

# Test with MCP Inspector
npx @modelcontextprotocol/inspector python -m src.server
```

## Related Projects

- [Plan for Chicago 2030](https://github.com/your-username/Plan_for_Chicago_2030) — The parent analysis project with zoning analysis, property value modeling, and interactive maps.

## License

MIT
