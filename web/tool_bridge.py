"""Synchronous tool bridge — calls src/* functions directly for use by the web layer.

All 8 MCP tools are re-exposed here as plain synchronous Python functions so the
Gemini client can call them without spawning a subprocess or running an event loop.
"""

from __future__ import annotations

import time

import httpx

from src.data_loader import get_all_districts, get_district, get_districts_by_category
from src.geocoder import is_in_chicago
from src.tools.code_search import get_section_by_number, load_section_index, search_sections

# ---------------------------------------------------------------------------
# Nominatim geocoding (sync version — avoids asyncio in Flask workers)
# ---------------------------------------------------------------------------

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_SOCRATA_URL = "https://data.cityofchicago.org/resource/dj47-wfun.geojson"

_last_geocode_time: float = 0.0
_RATE_LIMIT_SECONDS = 1.1


def _sync_geocode(address: str) -> tuple[float, float] | None:
    """Synchronous geocoding via Nominatim. Rate-limited to 1 req/sec."""
    global _last_geocode_time
    elapsed = time.monotonic() - _last_geocode_time
    if elapsed < _RATE_LIMIT_SECONDS:
        time.sleep(_RATE_LIMIT_SECONDS - elapsed)
    _last_geocode_time = time.monotonic()

    if "chicago" not in address.lower():
        address = f"{address}, Chicago, IL"
    try:
        with httpx.Client() as client:
            resp = client.get(
                _NOMINATIM_URL,
                params={
                    "q": address,
                    "format": "json",
                    "limit": 1,
                    "countrycodes": "us",
                    "viewbox": "-87.94,42.02,-87.52,41.64",
                    "bounded": 1,
                },
                headers={"User-Agent": "chicago-zoning-mcp/0.1"},
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json()
    except httpx.HTTPError:
        return None

    if not results:
        return None
    lat = float(results[0]["lat"])
    lng = float(results[0]["lon"])
    return (lat, lng) if is_in_chicago(lat, lng) else None


# ---------------------------------------------------------------------------
# Tool implementations (1-to-1 with the MCP tools in src/tools/)
# ---------------------------------------------------------------------------


def lookup_district(district_code: str) -> dict:
    result = get_district(district_code)
    if result is None:
        return {
            "error": f"District '{district_code}' not found.",
            "hint": "Use list_district_types to see all valid district codes.",
        }
    return result


def compare_districts(district_a: str, district_b: str) -> dict:
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
    comparison["_differences"] = [k for k in a if a[k] != b[k]]
    return comparison


def list_district_types(category: str = "") -> list[dict]:
    if category:
        districts = get_districts_by_category(category)
    else:
        districts = list(get_all_districts().values())
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


def calculate_development_envelope(district_code: str, lot_area_sqft: float) -> dict:
    if lot_area_sqft <= 0:
        return {"error": "lot_area_sqft must be a positive number.", "lot_area_sqft": lot_area_sqft}
    district = get_district(district_code)
    if district is None:
        return {"error": f"District '{district_code}' not found."}

    result: dict = {
        "district_code": district_code.upper(),
        "lot_area_sqft": lot_area_sqft,
        "district_title": district["district_title"],
    }
    # Max floor area
    far_str = district.get("floor_area_ratio", "")
    try:
        far = float(far_str)
        result["floor_area_ratio"] = far
        result["max_floor_area_sqft"] = round(lot_area_sqft * far, 1)
    except (ValueError, TypeError):
        result["floor_area_ratio"] = far_str
        result["max_floor_area_sqft"] = "Cannot calculate — FAR is not a simple number"
    # Max dwelling units
    lot_per_unit_str = district.get("lot_area_per_unit", "")
    try:
        numeric = lot_per_unit_str.split("/")[0].split("sq")[0].replace(",", "").strip()
        lot_per_unit = float(numeric)
        if lot_per_unit <= 0:
            raise ValueError
        result["lot_area_per_dwelling_unit_sqft"] = lot_per_unit
        result["max_dwelling_units"] = max(int(lot_area_sqft // lot_per_unit), 1)
    except (ValueError, TypeError, IndexError, OverflowError):
        result["lot_area_per_dwelling_unit"] = lot_per_unit_str
        result["max_dwelling_units"] = "Cannot calculate — see lot_area_per_dwelling_unit"

    result["maximum_building_height"] = district.get("maximum_building_height", "")
    result["front_yard_setback"] = district.get("front_yard_setback", "")
    result["side_setback"] = district.get("side_setback", "")
    result["rear_yard_setback"] = district.get("rear_yard_setback", "")
    result["disclaimer"] = (
        "This is an estimate. Actual limits depend on lot shape, overlays, "
        "planned developments, and other site-specific factors."
    )
    return result


def get_parcel_zoning(
    address: str = "",
    latitude: float = 0.0,
    longitude: float = 0.0,
) -> dict:
    # Resolve coordinates
    if address and (latitude == 0.0 and longitude == 0.0):
        coords = _sync_geocode(address)
        if coords is None:
            return {
                "error": f"Could not geocode address: {address}",
                "hint": "Make sure this is a valid Chicago address.",
            }
        lat, lng = coords
        if not is_in_chicago(lat, lng):
            return {
                "error": "Address geocoded to a location outside Chicago city limits.",
                "address": address,
                "hint": "Only Chicago addresses are supported.",
            }
    elif latitude != 0.0 and longitude != 0.0:
        lat, lng = latitude, longitude
        if not is_in_chicago(lat, lng):
            return {
                "error": "Coordinates are outside Chicago city limits.",
                "coordinates": {"lat": lat, "lng": lng},
            }
    else:
        return {"error": "Provide either an address or latitude/longitude."}

    soql_where = f"intersects(the_geom, 'POINT({lng} {lat})')"
    try:
        with httpx.Client() as client:
            resp = client.get(
                _SOCRATA_URL,
                params={"$where": soql_where, "$limit": 5},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        return {
            "error": "Request to Chicago Data Portal timed out. Try again shortly.",
            "coordinates": {"lat": lat, "lng": lng},
        }
    except httpx.HTTPError:
        return {
            "error": "Could not connect to Chicago Data Portal. Check network connection.",
            "coordinates": {"lat": lat, "lng": lng},
        }

    features = data.get("features", [])
    if not features:
        return {
            "error": "No zoning district found at this location.",
            "coordinates": {"lat": lat, "lng": lng},
        }
    props = features[0].get("properties", {})
    district_code = props.get("zone_class", "")
    return {
        "coordinates": {"lat": lat, "lng": lng},
        "address": address or None,
        "zone_class": district_code,
        "socrata_properties": props,
        "district_details": get_district(district_code),
    }


def get_zoning_map_url(
    latitude: float = 41.8781,
    longitude: float = -87.6298,
    zoom: int = 17,
) -> dict:
    zoom = max(10, min(zoom, 20))
    url = f"https://gisapps.chicago.gov/ZoningMapWeb/?loc={latitude},{longitude}&zoom={zoom}"
    return {
        "url": url,
        "coordinates": {"lat": latitude, "lng": longitude},
        "zoom": zoom,
        "note": "Opens in the official Chicago Zoning Map viewer.",
    }


def search_zoning_code(query: str, max_results: int = 5) -> dict:
    results = search_sections(query, max_results=min(max_results, 10))
    if not results:
        if not load_section_index():
            return {
                "error": "Title 17 text index not yet built.",
                "hint": "Run: python scripts/ingest_title_17.py",
            }
        return {
            "results": [],
            "result_count": 0,
            "query": query,
            "message": "No matching sections found. Try different keywords.",
        }
    return {"query": query, "result_count": len(results), "results": results}


def get_zoning_section(section_number: str) -> dict:
    section = get_section_by_number(section_number)
    if section is None:
        return {
            "error": f"Section '{section_number}' not found.",
            "hint": "Use search_zoning_code to find sections by keyword.",
        }
    return section


# ---------------------------------------------------------------------------
# Registry for the Gemini client to dispatch by name
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS: dict[str, callable] = {
    "lookup_district": lookup_district,
    "compare_districts": compare_districts,
    "list_district_types": list_district_types,
    "calculate_development_envelope": calculate_development_envelope,
    "get_parcel_zoning": get_parcel_zoning,
    "get_zoning_map_url": get_zoning_map_url,
    "search_zoning_code": search_zoning_code,
    "get_zoning_section": get_zoning_section,
}
