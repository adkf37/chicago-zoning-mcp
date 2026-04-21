"""Tests for geospatial tools.

Unit tests use mocking to avoid network calls.
Integration tests (marked with @pytest.mark.network) hit live APIs.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastmcp import FastMCP

from src.geocoder import CHICAGO_BOUNDS, geocode_address, is_in_chicago
from src.tools.geospatial import register_geospatial_tools

# --- Unit tests for geocoder helpers ---


def test_chicago_coordinates_in_bounds():
    """Downtown Chicago should be in bounds."""
    assert is_in_chicago(41.8781, -87.6298) is True


def test_lake_michigan_out_of_bounds():
    """A point in Lake Michigan east of Chicago should be out of bounds."""
    assert is_in_chicago(41.88, -87.50) is False


def test_new_york_out_of_bounds():
    """New York coordinates should be out of bounds."""
    assert is_in_chicago(40.7128, -74.0060) is False


def test_edge_of_chicago():
    """Points right at the boundary edge should be in bounds."""
    assert is_in_chicago(CHICAGO_BOUNDS["min_lat"], CHICAGO_BOUNDS["min_lng"]) is True
    assert is_in_chicago(CHICAGO_BOUNDS["max_lat"], CHICAGO_BOUNDS["max_lng"]) is True


@pytest.mark.asyncio
async def test_geocode_address_network_error_returns_none():
    """geocode_address should return None (not raise) when Nominatim is unreachable."""
    with patch("src.geocoder.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("name resolution failed")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await geocode_address("123 N Michigan Ave")
    assert result is None


@pytest.mark.asyncio
async def test_geocode_address_timeout_returns_none():
    """geocode_address should return None (not raise) when Nominatim times out."""
    with patch("src.geocoder.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await geocode_address("1060 W Addison St")
    assert result is None


# --- Unit tests for geospatial tools (mocked) ---


def _make_mcp():
    mcp = FastMCP("test")
    register_geospatial_tools(mcp)
    return mcp


def test_get_zoning_map_url_default():
    """Default map URL should point to downtown Chicago."""
    _make_mcp()
    result = _call_sync_tool_get_zoning_map_url()
    assert "url" in result
    assert result["url"].startswith("https://gisapps.chicago.gov/")
    assert result["zoom"] == 17


def _call_sync_tool_get_zoning_map_url(lat=41.8781, lng=-87.6298, zoom=17):
    """Helper to call the sync get_zoning_map_url tool."""
    # Recreate to get the function
    mcp = FastMCP("test")
    tools = {}

    # Intercept tool registration
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    return tools["get_zoning_map_url"](latitude=lat, longitude=lng, zoom=zoom)


def test_get_zoning_map_url_custom():
    """Custom coordinates and zoom should be reflected in URL."""
    result = _call_sync_tool_get_zoning_map_url(lat=41.95, lng=-87.65, zoom=13)
    assert "41.95" in result["url"]
    assert "-87.65" in result["url"]
    assert result["zoom"] == 13


def test_get_zoning_map_url_zoom_clamped():
    """Zoom should be clamped to [10, 20]."""
    result = _call_sync_tool_get_zoning_map_url(zoom=5)
    assert result["zoom"] == 10

    result = _call_sync_tool_get_zoning_map_url(zoom=25)
    assert result["zoom"] == 20


@pytest.mark.asyncio
async def test_parcel_zoning_no_input():
    """Should return error when neither address nor coordinates provided."""
    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    result = await tools["get_parcel_zoning"]()
    assert "error" in result


@pytest.mark.asyncio
async def test_parcel_zoning_outside_chicago():
    """Coordinates outside Chicago should return error."""
    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    # New York coords
    result = await tools["get_parcel_zoning"](latitude=40.7128, longitude=-74.0060)
    assert "error" in result
    assert "outside" in result["error"].lower()


@pytest.mark.asyncio
async def test_parcel_zoning_address_outside_chicago():
    """Address that geocodes to outside Chicago should return error without querying Socrata."""
    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    # Mock geocoder returning New York City coordinates
    with patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo, \
         patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls:

        mock_geo.return_value = (40.7128, -74.0060)  # New York City coords

        result = await tools["get_parcel_zoning"](address="350 5th Ave, New York, NY")

        # Should return error before ever calling Socrata
        assert mock_client_cls.called is False, (
            "Socrata should not be queried for non-Chicago address"
        )
        assert "error" in result
        assert "outside" in result["error"].lower()


@pytest.mark.asyncio
async def test_parcel_zoning_with_mocked_geocoder():
    """With mocked geocoder and Socrata, should return district info."""
    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    mock_socrata_response = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"zone_class": "RS-3", "zone_type": "4"},
                "geometry": {"type": "MultiPolygon", "coordinates": []},
            }
        ],
    }

    with patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo, \
         patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls:

        mock_geo.return_value = (41.97, -87.66)

        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_socrata_response
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await tools["get_parcel_zoning"](address="4521 N Clark St")
        assert result["zone_class"] == "RS-3"
        assert result["district_details"] is not None
        assert result["district_details"]["category"] == "Residential"


# --- Integration tests (require network) ---


@pytest.mark.asyncio
async def test_parcel_zoning_geocoder_returns_none():
    """When geocoding fails, should return an error dict."""
    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    with patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo:
        mock_geo.return_value = None
        result = await tools["get_parcel_zoning"](address="9999 Fake St")
        assert "error" in result
        assert "geocode" in result["error"].lower()


@pytest.mark.asyncio
async def test_parcel_zoning_socrata_no_features():
    """When Socrata returns zero features, should return a 'not found' error."""
    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    empty_response = {"type": "FeatureCollection", "features": []}

    with patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo, \
         patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls:

        mock_geo.return_value = (41.88, -87.63)

        mock_resp = MagicMock()
        mock_resp.json.return_value = empty_response
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await tools["get_parcel_zoning"](address="Some Address")
        assert "error" in result


@pytest.mark.asyncio
async def test_parcel_zoning_socrata_timeout():
    """A Socrata timeout should return a user-friendly error."""
    import httpx as _httpx

    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    with patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo, \
         patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls:

        mock_geo.return_value = (41.88, -87.63)

        mock_client = AsyncMock()
        mock_client.get.side_effect = _httpx.TimeoutException("timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await tools["get_parcel_zoning"](address="Some Address")
        assert "error" in result
        assert "timed out" in result["error"].lower()


@pytest.mark.asyncio
async def test_parcel_zoning_socrata_connect_error():
    """A Socrata connection error (DNS failure, etc.) should return a user-friendly error."""
    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    with patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo, \
         patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls:

        mock_geo.return_value = (41.88, -87.63)

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Name resolution failed")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await tools["get_parcel_zoning"](address="Some Address")
        assert "error" in result
        assert isinstance(result["error"], str)
        # Should not raise; must return a structured dict
        assert "coordinates" in result


@pytest.mark.asyncio
async def test_parcel_zoning_coords_directly():
    """Coordinates can be passed directly without an address."""
    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    mock_socrata_response = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"zone_class": "DC-16", "zone_type": "8"},
                "geometry": {"type": "MultiPolygon", "coordinates": []},
            }
        ],
    }

    with patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_socrata_response
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        # Willis Tower coordinates
        result = await tools["get_parcel_zoning"](latitude=41.8789, longitude=-87.6359)
        assert result["zone_class"] == "DC-16"
        assert result["coordinates"]["lat"] == 41.8789


@pytest.mark.asyncio
async def test_parcel_zoning_coords_take_priority_over_address():
    """When both address and coordinates are provided, coordinates win (no geocoding call)."""
    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    mock_socrata_response = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"zone_class": "RS-3", "zone_type": "4"},
                "geometry": {},
            }
        ],
    }

    with patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo, \
         patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls:

        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_socrata_response
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        # Both address and coords provided — geocoder must NOT be called
        result = await tools["get_parcel_zoning"](
            address="some address that would be ignored",
            latitude=41.97,
            longitude=-87.66,
        )
        assert mock_geo.called is False, "geocode_address should not be called when coords provided"
        assert result["zone_class"] == "RS-3"
        assert result["coordinates"]["lat"] == 41.97


# --- Integration tests (require network) ---


@pytest.mark.network
@pytest.mark.asyncio
async def test_geocode_wrigley_field():
    """Integration: geocode Wrigley Field address."""
    from src.geocoder import geocode_address

    coords = await geocode_address("1060 W Addison St")
    assert coords is not None
    lat, lng = coords
    # Wrigley Field is around 41.948, -87.656
    assert 41.94 < lat < 41.96
    assert -87.67 < lng < -87.64


@pytest.mark.network
@pytest.mark.asyncio
async def test_geocode_willis_tower():
    """Integration: geocode Willis Tower address."""
    from src.geocoder import geocode_address

    coords = await geocode_address("233 S Wacker Dr")
    assert coords is not None
    lat, lng = coords
    # Willis Tower is around 41.879, -87.636
    assert 41.87 < lat < 41.89
    assert -87.65 < lng < -87.62


@pytest.mark.network
@pytest.mark.asyncio
async def test_parcel_zoning_willis_tower():
    """Integration: Willis Tower should return DC-16 zoning."""
    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    result = await tools["get_parcel_zoning"](address="233 S Wacker Dr")
    assert "error" not in result, f"Unexpected error: {result.get('error')}"
    assert result["zone_class"] == "DC-16"


@pytest.mark.network
@pytest.mark.asyncio
async def test_parcel_zoning_residential_block():
    """Integration: residential block should return an R-category district."""
    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    result = await tools["get_parcel_zoning"](address="4521 N Clark St")
    assert "error" not in result, f"Unexpected error: {result.get('error')}"
    assert result["zone_class"].startswith(("RS", "RT", "RM", "B", "C"))


@pytest.mark.network
@pytest.mark.asyncio
async def test_parcel_zoning_by_coordinates():
    """Integration: coordinate-based lookup for downtown Chicago."""
    mcp = FastMCP("test")
    tools = {}
    original_tool = mcp.tool

    def capture_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            tools[fn.__name__] = fn
            return decorator(fn)
        return wrapper

    mcp.tool = capture_tool
    register_geospatial_tools(mcp)

    # Willis Tower coordinates
    result = await tools["get_parcel_zoning"](latitude=41.8789, longitude=-87.6359)
    assert "error" not in result, f"Unexpected error: {result.get('error')}"
    assert result["zone_class"] != ""
