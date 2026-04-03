"""Geospatial zoning tools — parcel lookup and map links."""

import httpx
from fastmcp import FastMCP

from src.data_loader import get_district
from src.geocoder import geocode_address, is_in_chicago

# Chicago Data Portal — Zoning Districts GeoJSON (Socrata)
ZONING_SOCRATA_URL = "https://data.cityofchicago.org/resource/dj47-wfun.geojson"


def register_geospatial_tools(mcp: FastMCP):
    """Register geospatial tools with the MCP server."""

    @mcp.tool()
    async def get_parcel_zoning(
        address: str = "",
        latitude: float = 0.0,
        longitude: float = 0.0,
    ) -> dict:
        """Look up the zoning district for a specific Chicago location.

        Provide EITHER an address (e.g. "1060 W Addison St") OR
        latitude/longitude coordinates. Returns the zoning district
        code and full district details.
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

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    ZONING_SOCRATA_URL,
                    params={
                        "$where": soql_where,
                        "$limit": 5,
                    },
                    timeout=15,
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

        return {
            "coordinates": {"lat": lat, "lng": lng},
            "address": address or None,
            "zone_class": district_code,
            "socrata_properties": props,
            "district_details": district_info,
        }

    @mcp.tool()
    def get_zoning_map_url(
        latitude: float = 41.8781,
        longitude: float = -87.6298,
        zoom: int = 17,
    ) -> dict:
        """Get a URL to the Chicago zoning map centered on a location.

        Defaults to downtown Chicago. Zoom 17 shows individual parcels;
        zoom 13 shows neighborhood-scale; zoom 11 shows the full city.
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
