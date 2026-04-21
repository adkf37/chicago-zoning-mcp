"""Zoning district lookup tools."""

from fastmcp import FastMCP

from src.data_loader import get_all_districts, get_district, get_districts_by_category


def register_district_tools(mcp: FastMCP):
    """Register district lookup tools with the MCP server."""

    @mcp.tool()
    def lookup_district(district_code: str) -> dict:
        """Look up a Chicago zoning district by its code (e.g. RS-3, B2-5, DX-12).

        Use this tool when you already know the zoning district code and want its
        rules. This tool does NOT accept street addresses — use get_parcel_zoning
        first to find the district code for an address.

        Returns: FAR (floor_area_ratio), maximum_building_height, lot_area_per_unit,
        front/side/rear setbacks, minimum_lot_area, plain_description, category,
        and district_title.

        Common codes: RS-3 (single-family), RT-4 (two-flat/townhouse),
        RM-5 (multi-family), B3-2 (community shopping), DC-16 (downtown core),
        DX-7 (downtown mixed-use), M1-1 (light manufacturing).
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

        Use this tool when you know two district codes and want to understand the
        differences between them (e.g. after a rezoning, or to explain what a
        district change means for development potential).

        Both district_a and district_b must be valid district codes (e.g. "RS-3",
        "RT-4"). Use lookup_district or list_district_types to discover valid codes.

        Returns per-field comparison with "same" boolean for each field, plus a
        top-level "_differences" list naming every field whose value differs between
        the two districts. An empty "_differences" list means the districts are
        identical.

        Useful for questions like:
        - "What changes if my lot gets rezoned from RS-3 to RT-4?"
        - "Which has a higher FAR, B1-1 or B3-3?"
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

        Use this tool to discover valid district codes, browse districts by
        type, or answer "What residential districts exist in Chicago?" style
        questions. Returns a summary view (code, category, title, FAR, description)
        — for full details on a specific district, call lookup_district.

        Valid category values (case-insensitive, partial match):
        - "Residential" — RS, RT, RM districts
        - "Commercial" — C1, C2, C3 districts
        - "Business/Shopping" — B1, B2, B3 districts
        - "Manufacturing/Industrial" — M1, M2, M3 districts
        - "Downtown Mixed-Use" — DX districts
        - "Downtown Core" — DC districts
        - "Downtown Residential" — DR districts
        - "Downtown Service" — DS districts
        - "Planned Development" — PD districts
        - "Parks and Open Space" — POS districts
        - "Transportation" — T districts

        Leave category empty to return all districts.
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
