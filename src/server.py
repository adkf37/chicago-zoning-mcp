"""Chicago Zoning MCP Server — FastMCP entry point."""

from fastmcp import FastMCP

from src.tools.district_lookup import register_district_tools
from src.tools.geospatial import register_geospatial_tools
from src.tools.development import register_development_tools
from src.tools.code_search import register_code_search_tools

mcp = FastMCP("Chicago Zoning Assistant")

# Register all tool groups
register_district_tools(mcp)
register_geospatial_tools(mcp)
register_development_tools(mcp)
register_code_search_tools(mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio")
