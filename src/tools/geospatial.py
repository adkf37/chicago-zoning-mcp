"""Geospatial zoning tools — parcel lookup and map links."""

import httpx
from fastmcp import FastMCP

from src.data_loader import get_district
from src.geocoder import geocode_address, is_in_chicago

# Chicago Data Portal — Zoning Districts GeoJSON (Socrata)
ZONING_SOCRATA_URL = "https://data.cityofchicago.org/resource/dj47-wfun.geojson"

# Trim the Socrata payload — we only need a few attributes, not the full geometry.
_SOCRATA_SELECT_FIELDS = "zone_class,zone_type,edit_date,objectid,case_number"

# Reuse one async client (connection pool + keep-alive). FastMCP runs a single
# event loop per server process, so module-level reuse is safe and noticeably
# faster than spinning a new client per call.
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=5.0),
            headers={"User-Agent": "chicago-zoning-mcp/0.1"},
        )
    return _http_client


# Small in-process cache for repeated point-in-polygon lookups. Coordinates are
# rounded to ~1 m (5 decimal places) so near-identical follow-ups (typical when
# an LLM retries) hit the cache.
_parcel_cache: dict[tuple[float, float], dict] = {}
_PARCEL_CACHE_MAX = 256


def _cache_key(lat: float, lng: float) -> tuple[float, float]:
    return (round(lat, 5), round(lng, 5))


def register_geospatial_tools(mcp: FastMCP):
    """Register geospatial tools with the MCP server."""

    @mcp.tool()
    async def get_parcel_zoning(
        address: str = "",
        latitude: float = 0.0,
        longitude: float = 0.0,
    ) -> dict:
        """Look up the zoning district for a specific Chicago location.

        Use this tool when you have a street address or coordinates and need to find
        the zoning district code. This tool performs live network calls (Nominatim
        geocoding and Chicago Data Portal Socrata API) — it requires internet access.

        This is typically the FIRST step in multi-step questions like:
        "What can I build at [address]?" — call this tool first to get the district
        code, then call calculate_development_envelope with the result.

        Provide EITHER an address (e.g. "1060 W Addison St", "233 S Wacker Dr") OR
        latitude/longitude coordinates. If both are provided, coordinates take
        priority.

        Returns: zone_class (the district code), coordinates, socrata_properties
        (raw API data), and district_details (full district record from our CSV).
        """
        # Resolve coordinates
        if address and (latitude == 0.0 and longitude == 0.0):
            coords = await geocode_address(address)
            if coords is None:
                return {
                    "error": f"Could not geocode address: {address}",
                    "hint": (
                        "Make sure this is a valid Chicago address. "
                        "Addresses outside Chicago are not supported."
                    ),
                }
            lat, lng = coords
            if not is_in_chicago(lat, lng):
                return {
                    "error": "Address geocoded to a location outside Chicago city limits.",
                    "address": address,
                    "coordinates": {"lat": lat, "lng": lng},
                    "hint": (
                        "Only Chicago addresses are supported. "
                        "Chicago coordinates are roughly lat 41.64-42.02, lng -87.94 to -87.52."
                    ),
                }
        elif latitude != 0.0 and longitude != 0.0:
            lat, lng = latitude, longitude
            # Validate coordinates are in Chicago
            if not is_in_chicago(lat, lng):
                return {
                    "error": "Coordinates are outside Chicago city limits.",
                    "coordinates": {"lat": lat, "lng": lng},
                    "hint": (
                        "Chicago coordinates are roughly lat 41.64-42.02, lng -87.94 to -87.52."
                    ),
                }
        else:
            return {"error": "Provide either an address or latitude/longitude."}

        # Query Socrata for zoning district at this point
        soql_where = f"intersects(the_geom, 'POINT({lng} {lat})')"

        cache_key = _cache_key(lat, lng)
        cached = _parcel_cache.get(cache_key)
        if cached is not None:
            return {**cached, "address": address or None}

        try:
            client = _get_http_client()
            resp = await client.get(
                ZONING_SOCRATA_URL,
                params={
                    "$where": soql_where,
                    "$select": _SOCRATA_SELECT_FIELDS,
                    "$limit": 5,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException:
            return {
                "error": "Request to Chicago Data Portal timed out. Try again shortly.",
                "coordinates": {"lat": lat, "lng": lng},
            }
        except httpx.HTTPStatusError as e:
            return {
                "error": f"Chicago Data Portal returned an error: {e.response.status_code}",
                "coordinates": {"lat": lat, "lng": lng},
            }
        except httpx.HTTPError:
            return {
                "error": "Could not connect to Chicago Data Portal. Check your network connection.",
                "coordinates": {"lat": lat, "lng": lng},
                "hint": (
                    "Try again shortly, or use get_zoning_map_url to look up the"
                    " location manually."
                ),
            }

        features = data.get("features", [])
        if not features:
            return {
                "error": "No zoning district found at this location.",
                "coordinates": {"lat": lat, "lng": lng},
                "hint": (
                    "Location may be outside Chicago city limits, in a waterway, "
                    "or in an unmapped area."
                ),
            }

        # Extract district code from first matching feature
        props = features[0].get("properties", {})
        district_code = props.get("zone_class", "")

        # Enrich with our reference data
        district_info = get_district(district_code)

        result = {
            "coordinates": {"lat": lat, "lng": lng},
            "address": address or None,
            "zone_class": district_code,
            "socrata_properties": props,
            "district_details": district_info,
        }

        # Cache successful lookups (without the per-call address)
        if len(_parcel_cache) >= _PARCEL_CACHE_MAX:
            _parcel_cache.pop(next(iter(_parcel_cache)))
        _parcel_cache[cache_key] = {k: v for k, v in result.items() if k != "address"}

        return result

    @mcp.tool()
    def get_zoning_map_url(
        latitude: float = 41.8781,
        longitude: float = -87.6298,
        zoom: int = 17,
    ) -> dict:
        """Get a URL to the Chicago zoning map centered on a location.

        Use this tool when the user asks for a link to the official Chicago zoning
        map, or when get_parcel_zoning fails and you want to give the user a
        fallback way to look up the zoning themselves visually.

        This tool does NOT look up the district code — it only returns a URL.
        For district code lookup, use get_parcel_zoning.

        Defaults to downtown Chicago (City Hall area). Zoom levels:
        - 20 / 17 — individual parcels (default 17)
        - 13 — neighborhood scale
        - 11 — full city view
        """
        # Clamp zoom to reasonable range
        zoom = max(10, min(zoom, 20))

        url = (
            f"https://gisapps.chicago.gov/ZoningMapWeb/"
            f"?loc={latitude},{longitude}&zoom={zoom}"
        )
        return {
            "url": url,
            "coordinates": {"lat": latitude, "lng": longitude},
            "zoom": zoom,
            "note": "Opens in the official Chicago Zoning Map viewer.",
        }
