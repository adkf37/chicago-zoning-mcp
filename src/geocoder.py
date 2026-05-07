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

# In-process cache for repeated geocoding lookups. Repeat queries (very common
# during multi-turn LLM conversations) are returned instantly and skip the
# 1.1 s rate-limit wait entirely.
_geocode_cache: dict[str, tuple[float, float] | None] = {}
_GEOCODE_CACHE_MAX = 512


def _normalize_address(address: str) -> str:
    return " ".join(address.lower().split())


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

    cache_key = _normalize_address(address)
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    await _enforce_rate_limit()

    try:
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
    except httpx.HTTPError:
        return None

    if not results:
        _store_geocode(cache_key, None)
        return None

    lat = float(results[0]["lat"])
    lng = float(results[0]["lon"])

    # Verify result is actually in Chicago
    if not is_in_chicago(lat, lng):
        _store_geocode(cache_key, None)
        return None

    _store_geocode(cache_key, (lat, lng))
    return lat, lng


def _store_geocode(key: str, value: tuple[float, float] | None) -> None:
    if len(_geocode_cache) >= _GEOCODE_CACHE_MAX:
        _geocode_cache.pop(next(iter(_geocode_cache)))
    _geocode_cache[key] = value
