"""Load and cache zoning reference data."""

import csv
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
ZONING_CODES_CSV = DATA_DIR / "zoning_codes.csv"
TITLE_17_INDEX = DATA_DIR / "title_17" / "sections.json"

# Category mapping: zone_type code → human-readable category
ZONE_TYPE_CATEGORIES = {
    1: "Business/Shopping",
    2: "Commercial",
    3: "Manufacturing/Industrial",
    4: "Residential",
    5: "Planned Development",
    7: "Downtown Mixed-Use",
    8: "Downtown Core",
    9: "Downtown Residential",
    10: "Downtown Service",
    12: "Parks and Open Space",
    13: "Transportation",
}


@lru_cache(maxsize=1)
def load_zoning_districts() -> dict[str, dict]:
    """Load zoning_codes.csv into a dict keyed by district_type_code.

    Returns:
        {"RS-3": {"district_type_code": "RS-3", "zone_type": 4, "category": "Residential", ...}, ...}
    """  # noqa: E501
    districts = {}
    with open(ZONING_CODES_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["district_type_code"].strip()
            zone_type = int(row["zone_type"]) if row.get("zone_type") else None
            districts[code] = {
                "district_type_code": code,
                "zone_type": zone_type,
                "category": ZONE_TYPE_CATEGORIES.get(zone_type, "Other"),
                "district_title": row.get("district_title", ""),
                "old_description": row.get("old_description", ""),
                "plain_description": row.get("juan_description", ""),
                "zoning_code_section": row.get("zoning_code_section", ""),
                "floor_area_ratio": row.get("floor_area_ratio", ""),
                "maximum_building_height": row.get("maximum_building_height", ""),
                "lot_area_per_unit": row.get("lot_area_per_unit", ""),
                "front_yard_setback": row.get("front_yard_setback", ""),
                "side_setback": row.get("side_setback", ""),
                "rear_yard_setback": row.get("rear_yard_setback", ""),
                "rear_yard_open_space": row.get("rear_yard_open_space", ""),
                "on_site_open_space": row.get("on_site_open_space", ""),
                "minimum_lot_area": row.get("minimum_lot_area", ""),
            }
    return districts


def get_district(code: str) -> dict | None:
    """Look up a single district by code (case-insensitive)."""
    districts = load_zoning_districts()
    return districts.get(code.upper().strip())


def get_all_districts() -> dict[str, dict]:
    """Return all districts."""
    return load_zoning_districts()


def get_districts_by_category(category: str) -> list[dict]:
    """Return all districts matching a category (case-insensitive partial match)."""
    districts = load_zoning_districts()
    category_lower = category.lower()
    return [
        d for d in districts.values()
        if category_lower in d["category"].lower()
    ]
