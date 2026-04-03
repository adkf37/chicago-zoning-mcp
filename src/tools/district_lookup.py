"""Zoning district lookup tools."""

from fastmcp import FastMCP

from src.data_loader import get_all_districts, get_district, get_districts_by_category


def register_district_tools(mcp: FastMCP):
    """Register district lookup tools with the MCP server."""

    @mcp.tool()
    def lookup_district(district_code: str) -> dict:
        """Look up a Chicago zoning district by its code (e.g. RS-3, B2-5, DX-12).

        Returns the district's FAR, max height, setbacks, lot requirements,
        and a plain-language description of what the district allows.
        """
        result = get_district(district_code)
        if result is None:
            return {
                "error": f"District '{district_code}' not found.",
                "hint": "Use list_district_types to see all valid district codes.",
            }
        return result

    @mcp.tool()
    def compare_districts(district_a: str, district_b: str) -> dict:
        """Compare two Chicago zoning districts side by side.

        Shows differences in FAR, height, setbacks, and allowed uses.
        Useful for understanding what changes when a parcel is rezoned.

        The response includes a ``_differences`` key with a list of field names
        whose values differ between the two districts (empty list when both are
        the same district).
        """
        a = get_district(district_a)
        b = get_district(district_b)

        errors = []
        if a is None:
            errors.append(f"District '{district_a}' not found.")
        if b is None:
            errors.append(f"District '{district_b}' not found.")
        if errors:
            return {"error": " ".join(errors)}

        comparison = {}
        for key in a:
            comparison[key] = {
                district_a.upper(): a[key],
                district_b.upper(): b[key],
                "same": a[key] == b[key],
            }

        # Top-level summary: list fields that differ for quick LLM consumption
        comparison["_differences"] = [k for k in a if a[k] != b[k]]
        return comparison

    @mcp.tool()
    def list_district_types(category: str = "") -> list[dict]:
        """List all Chicago zoning districts, optionally filtered by category.

        Categories: Residential, Commercial, Business/Shopping, Manufacturing/Industrial,
        Downtown Mixed-Use, Downtown Core, Downtown Residential, Downtown Service,
        Planned Development, Parks and Open Space, Transportation.

        If no category is given, returns all districts (summary view).
        """
        if category:
            districts = get_districts_by_category(category)
        else:
            districts = list(get_all_districts().values())

        # Return summary view (not full details) for listing
        return [
            {
                "district_type_code": d["district_type_code"],
                "category": d["category"],
                "district_title": d["district_title"],
                "floor_area_ratio": d["floor_area_ratio"],
                "plain_description": d["plain_description"],
            }
            for d in districts
        ]
