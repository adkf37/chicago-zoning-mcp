"""Zoning district lookup tools."""

from fastmcp import FastMCP

from src.data_loader import get_all_districts, get_district, get_districts_by_category


def _parse_far(far_str: str) -> float | None:
    """Return the FAR as a float, or None if it is non-numeric."""
    try:
        return float(far_str)
    except (ValueError, TypeError):
        return None


def _parse_lot_per_unit(raw: str) -> float | None:
    """Return sq-ft per dwelling unit as a float, or None if non-numeric."""
    try:
        numeric = raw.split("/")[0].split("sq")[0].replace(",", "").strip()
        val = float(numeric)
        return val if val > 0 else None
    except (ValueError, TypeError, IndexError):
        return None


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

    @mcp.tool()
    def find_districts_meeting_criteria(
        min_far: float = 0.0,
        max_far: float = 0.0,
        min_dwelling_units: int = 0,
        lot_area_sqft: float = 0.0,
        category: str = "",
    ) -> dict:
        """Find Chicago zoning districts that satisfy one or more development criteria.

        Use this tool for questions like:
        - "Which districts allow at least 6 units on a 7,500 sq ft lot?"
        - "What residential districts have a FAR of 2 or more?"
        - "Which manufacturing districts have FAR between 1 and 3?"

        Parameters (all are optional; omit or set to 0 to skip that filter):
        - min_far: only include districts with FAR >= this value (e.g. 2.0)
        - max_far: only include districts with FAR <= this value (e.g. 5.0)
        - min_dwelling_units: only include districts where a lot of lot_area_sqft
          could fit at least this many dwelling units. Requires lot_area_sqft > 0.
        - lot_area_sqft: lot size used for the unit-count filter (e.g. 7500).
          Required when min_dwelling_units > 0; ignored otherwise.
        - category: optional category to limit results (same values as list_district_types).

        Returns: matching_count, applied_filters summary, and a list of matching
        districts sorted by FAR (highest first), each with code, category, title,
        FAR, max_dwelling_units (on the given lot, when lot_area_sqft > 0), and
        plain_description.
        """
        errors = []
        if min_dwelling_units > 0 and lot_area_sqft <= 0:
            errors.append(
                "lot_area_sqft must be greater than 0 when min_dwelling_units is set."
            )
        if min_far < 0 or max_far < 0:
            errors.append("min_far and max_far must be >= 0.")
        if min_far > 0 and max_far > 0 and min_far > max_far:
            errors.append("min_far cannot be greater than max_far.")
        if errors:
            return {"error": " ".join(errors)}

        candidates = (
            get_districts_by_category(category)
            if category
            else list(get_all_districts().values())
        )

        results = []
        for d in candidates:
            far = _parse_far(d.get("floor_area_ratio", ""))

            # FAR filters — skip non-numeric FARs when a FAR filter is active
            if min_far > 0 or max_far > 0:
                if far is None:
                    continue
                if min_far > 0 and far < min_far:
                    continue
                if max_far > 0 and far > max_far:
                    continue

            # Dwelling-unit filter
            max_units: int | str = "N/A"
            if lot_area_sqft > 0:
                lpu = _parse_lot_per_unit(d.get("lot_area_per_unit", ""))
                if lpu is not None:
                    max_units = max(int(lot_area_sqft // lpu), 1)
                else:
                    max_units = "N/A (see lot_area_per_unit)"

            if min_dwelling_units > 0:
                if not isinstance(max_units, int) or max_units < min_dwelling_units:
                    continue

            entry: dict = {
                "district_type_code": d["district_type_code"],
                "category": d["category"],
                "district_title": d["district_title"],
                "floor_area_ratio": d["floor_area_ratio"],
                "plain_description": d["plain_description"],
            }
            if lot_area_sqft > 0:
                entry["max_dwelling_units"] = max_units
            results.append((far if far is not None else -1.0, entry))

        # Sort by FAR descending (numeric first, then non-numeric already excluded)
        results.sort(key=lambda x: -x[0])
        matches = [e for _, e in results]

        applied: dict = {}
        if min_far > 0:
            applied["min_far"] = min_far
        if max_far > 0:
            applied["max_far"] = max_far
        if min_dwelling_units > 0:
            applied["min_dwelling_units"] = min_dwelling_units
        if lot_area_sqft > 0:
            applied["lot_area_sqft"] = lot_area_sqft
        if category:
            applied["category"] = category

        return {
            "matching_count": len(matches),
            "applied_filters": applied,
            "districts": matches,
        }

