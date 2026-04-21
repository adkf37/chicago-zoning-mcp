"""Development envelope calculation tools."""

from fastmcp import FastMCP

from src.data_loader import get_district


def register_development_tools(mcp: FastMCP):
    """Register development calculation tools with the MCP server."""

    @mcp.tool()
    def calculate_development_envelope(
        district_code: str,
        lot_area_sqft: float,
    ) -> dict:
        """Calculate the maximum development envelope for a lot in a given zoning district.

        Given a district code and lot size in square feet, returns:
        - Maximum buildable floor area (from FAR)
        - Estimated max dwelling units (from lot area per unit)
        - Maximum building height
        - Key setback requirements

        This is an estimate — actual limits depend on lot shape, overlays,
        planned developments, and other factors.
        """
        if lot_area_sqft <= 0:
            return {
                "error": "lot_area_sqft must be a positive number.",
                "lot_area_sqft": lot_area_sqft,
            }

        district = get_district(district_code)
        if district is None:
            return {"error": f"District '{district_code}' not found."}

        result = {
            "district_code": district_code.upper(),
            "lot_area_sqft": lot_area_sqft,
            "district_title": district["district_title"],
        }

        # Max floor area from FAR
        far_str = district.get("floor_area_ratio", "")
        try:
            far = float(far_str)
            result["floor_area_ratio"] = far
            result["max_floor_area_sqft"] = round(lot_area_sqft * far, 1)
        except (ValueError, TypeError):
            result["floor_area_ratio"] = far_str
            result["max_floor_area_sqft"] = "Cannot calculate — FAR is not a simple number"

        # Max dwelling units from lot area per unit
        lot_per_unit_str = district.get("lot_area_per_unit", "")
        try:
            # Parse first number from strings like "2,500 sq ft/dwelling unit, ..."
            numeric = lot_per_unit_str.split("/")[0].split("sq")[0]
            numeric = numeric.replace(",", "").strip()
            lot_per_unit = float(numeric)
            if lot_per_unit <= 0:
                raise ValueError("lot_area_per_unit must be positive")
            max_units = int(lot_area_sqft // lot_per_unit)
            result["lot_area_per_dwelling_unit_sqft"] = lot_per_unit
            result["max_dwelling_units"] = max(max_units, 1)
        except (ValueError, TypeError, IndexError):
            result["lot_area_per_dwelling_unit"] = lot_per_unit_str
            result["max_dwelling_units"] = "Cannot calculate — see lot_area_per_dwelling_unit"

        # Height and setbacks (pass through as-is, they're often text)
        result["maximum_building_height"] = district.get("maximum_building_height", "")
        result["front_yard_setback"] = district.get("front_yard_setback", "")
        result["side_setback"] = district.get("side_setback", "")
        result["rear_yard_setback"] = district.get("rear_yard_setback", "")

        result["disclaimer"] = (
            "This is an estimate based on base zoning regulations. "
            "Actual limits may differ due to lot shape, overlays, planned "
            "development designations, bonus provisions, and other factors. "
            "Consult the Chicago Department of Buildings for official determinations."
        )

        return result
