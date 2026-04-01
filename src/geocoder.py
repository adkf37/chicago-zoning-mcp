"""Address geocoding for Chicago parcels."""

import asyncio
import time

import httpx

# Nominatim (OpenStreetMap) — free, no API key, 1 req/sec rate limit
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Chicago bounding box (approx)
CHICAGO_BOUNDS = {
    "min_lat": 41.644,
    "max_lat": 42.023,
    "min_lng": -87.940,
    "max_lng": -87.524,
}

# Rate limiting: track last request time (1 req/sec for Nominatim)
_last_request_time: float = 0.0
_RATE_LIMIT_SECONDS = 1.1  # Slightly over 1s to be safe


async def _enforce_rate_limit() -> None:
    """Wait if needed to respect Nominatim's 1 req/sec rate limit."""
    global _last_request_time
    now = time.monotonic()
    elapsed = now - _last_request_time
    if elapsed < _RATE_LIMIT_SECONDS:
        await asyncio.sleep(_RATE_LIMIT_SECONDS - elapsed)
    _last_request_time = time.monotonic()


def is_in_chicago(lat: float, lng: float) -> bool:
    """Check if coordinates are within Chicago's approximate bounding box."""
    return (
        CHICAGO_BOUNDS["min_lat"] <= lat <= CHICAGO_BOUNDS["max_lat"]
        and CHICAGO_BOUNDS["min_lng"] <= lng <= CHICAGO_BOUNDS["max_lng"]
    )


async def geocode_address(address: str) -> tuple[float, float] | None:
    """Geocode a Chicago address to (lat, lng).

    Uses Nominatim with Chicago, IL bias. Returns None if not found.
    """
    # Append Chicago, IL if not already present
    if "chicago" not in address.lower():
        address = f"{address}, Chicago, IL"

    await _enforce_rate_limit()

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            NOMINATIM_URL,
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

    if not results:
        return None

    lat = float(results[0]["lat"])
    lng = float(results[0]["lon"])

    # Verify result is actually in Chicago
    if not is_in_chicago(lat, lng):
        return None

    return lat, lng
