"""Integration tests — verify all tools are registered and work end-to-end.

These tests exercise the full server + tool stack with real CSV data,
using mocks only for external network calls (Socrata, Nominatim).
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP

from src.server import mcp

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_tool_names(server: FastMCP) -> set[str]:
    """Return the set of tool names registered on a FastMCP server."""
    # FastMCP exposes _tool_manager or similar; use the public list_tools helper.
    # The underlying tool manager dict is at server._tool_manager._tools
    try:
        return set(server._tool_manager._tools.keys())
    except AttributeError:
        # Fallback: introspect via the MCP protocol list
        import asyncio
        tools = asyncio.get_event_loop().run_until_complete(server.list_tools())
        return {t.name for t in tools}


def _register_and_capture(register_fn) -> dict:
    """Create a fresh FastMCP instance, register tools via register_fn, and return
    a dict mapping tool function names to their callables.

    Used by tests that need to call a tool function directly without going through
    the MCP protocol layer.
    """
    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*a, **kw):
        dec = original(*a, **kw)
        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)
        return wrap

    mcp_t.tool = capture
    register_fn(mcp_t)
    return tools


# ---------------------------------------------------------------------------
# Tool registration smoke tests
# ---------------------------------------------------------------------------


EXPECTED_TOOLS = {
    "lookup_district",
    "compare_districts",
    "list_district_types",
    "calculate_development_envelope",
    "get_parcel_zoning",
    "get_zoning_map_url",
    "search_zoning_code",
    "get_zoning_section",
}


def test_all_tools_registered():
    """All 8 expected tools must be registered on the server."""
    registered = _get_tool_names(mcp)
    missing = EXPECTED_TOOLS - registered
    assert not missing, f"Missing tools: {missing}"


def test_no_unexpected_tools():
    """No tools should be registered beyond the expected set (prevents accidental exposure)."""
    registered = _get_tool_names(mcp)
    extra = registered - EXPECTED_TOOLS
    assert not extra, f"Unexpected tools registered: {extra}"


# ---------------------------------------------------------------------------
# District lookup — uses real CSV data, no mocks needed
# ---------------------------------------------------------------------------


def test_lookup_rs3_end_to_end():
    """Full stack: lookup_district('RS-3') should return FAR and category."""
    from src.tools.district_lookup import register_district_tools

    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*a, **kw):
        dec = original(*a, **kw)
        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)
        return wrap

    mcp_t.tool = capture
    register_district_tools(mcp_t)

    result = tools["lookup_district"](district_code="RS-3")
    assert "error" not in result
    assert result["floor_area_ratio"] == "0.9"
    assert result["category"] == "Residential"


def test_lookup_unknown_district_returns_error():
    """lookup_district for a nonexistent code should return an error, not raise."""
    from src.tools.district_lookup import register_district_tools

    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*a, **kw):
        dec = original(*a, **kw)
        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)
        return wrap

    mcp_t.tool = capture
    register_district_tools(mcp_t)

    result = tools["lookup_district"](district_code="ZZ-99")
    assert "error" in result


def test_compare_districts_rs3_rt4():
    """compare_districts should show RT-4 has higher FAR than RS-3."""
    from src.tools.district_lookup import register_district_tools

    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*a, **kw):
        dec = original(*a, **kw)
        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)
        return wrap

    mcp_t.tool = capture
    register_district_tools(mcp_t)

    result = tools["compare_districts"](district_a="RS-3", district_b="RT-4")
    assert "error" not in result
    rs3_far = float(result["floor_area_ratio"]["RS-3"])
    rt4_far = float(result["floor_area_ratio"]["RT-4"])
    assert rt4_far > rs3_far


def test_list_district_types_tool():
    """list_district_types returns all districts unfiltered, and a subset when filtered."""
    from src.tools.district_lookup import register_district_tools

    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*a, **kw):
        dec = original(*a, **kw)
        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)
        return wrap

    mcp_t.tool = capture
    register_district_tools(mcp_t)

    # No filter → returns all districts
    all_districts = tools["list_district_types"]()
    assert len(all_districts) > 50

    # Filtered by Residential
    residential = tools["list_district_types"](category="Residential")
    assert len(residential) > 0
    assert all("Residential" in d["category"] for d in residential)
    assert len(residential) < len(all_districts)

    # Summary view: must include required fields, must NOT include all details
    r = residential[0]
    for field in ("district_type_code", "category", "district_title", "floor_area_ratio",
                  "plain_description"):
        assert field in r, f"Missing summary field: {field}"


# ---------------------------------------------------------------------------
# Development calculator — uses real CSV data
# ---------------------------------------------------------------------------


def test_development_envelope_rs3_5000sqft():
    """RS-3, 5000 sqft lot → 4500 sqft max floor area."""
    from src.tools.development import register_development_tools

    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*a, **kw):
        dec = original(*a, **kw)
        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)
        return wrap

    mcp_t.tool = capture
    register_development_tools(mcp_t)

    result = tools["calculate_development_envelope"](district_code="RS-3", lot_area_sqft=5000)
    assert "error" not in result
    assert result["max_floor_area_sqft"] == 4500.0


def test_development_envelope_bad_district():
    """Bad district code should return error, not raise."""
    from src.tools.development import register_development_tools

    tools = _register_and_capture(register_development_tools)
    result = tools["calculate_development_envelope"](district_code="ZZ-99", lot_area_sqft=5000)
    assert "error" in result


def test_development_envelope_pd_nonnumeric_far():
    """PD district has non-numeric FAR — tool should return partial result, not crash."""
    from src.tools.development import register_development_tools

    tools = _register_and_capture(register_development_tools)
    result = tools["calculate_development_envelope"](district_code="PD", lot_area_sqft=5000)
    assert "error" not in result
    # FAR is not a number, so max_floor_area_sqft should be a string explanation
    assert isinstance(result["max_floor_area_sqft"], str)
    assert "Cannot calculate" in result["max_floor_area_sqft"]
    # Disclaimer must still be present even when FAR is non-numeric
    assert "disclaimer" in result


def test_development_envelope_commercial_no_units():
    """Commercial district with no lot_area_per_unit (B1-1) should return partial result."""
    from src.tools.development import register_development_tools

    tools = _register_and_capture(register_development_tools)
    result = tools["calculate_development_envelope"](district_code="B1-1", lot_area_sqft=5000)
    assert "error" not in result
    # Floor area should be numeric: B1-1 FAR = 1.0, so 5000 sqft * 1.0 = 5000.0
    assert result["max_floor_area_sqft"] == pytest.approx(5000.0)
    # Dwelling units cannot be computed for pure commercial districts
    assert isinstance(result["max_dwelling_units"], str)
    assert "Cannot calculate" in result["max_dwelling_units"]
    assert "disclaimer" in result


# ---------------------------------------------------------------------------
# Multi-step / chaining: geocode → district → envelope
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chain_parcel_zoning_then_envelope():
    """Tool chaining: get zone from address, then compute envelope."""
    from src.tools.development import register_development_tools
    from src.tools.geospatial import register_geospatial_tools

    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*a, **kw):
        dec = original(*a, **kw)
        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)
        return wrap

    mcp_t.tool = capture
    register_geospatial_tools(mcp_t)
    register_development_tools(mcp_t)

    mock_socrata = {
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

        mock_geo.return_value = (41.97, -87.66)
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_socrata
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        # Step 1: get zoning district
        zone_result = await tools["get_parcel_zoning"](address="4521 N Clark St")
        assert zone_result["zone_class"] == "RS-3"

        # Step 2: calculate envelope using that district
        district_code = zone_result["zone_class"]
        envelope = tools["calculate_development_envelope"](
            district_code=district_code, lot_area_sqft=3000
        )
        assert "error" not in envelope
        assert envelope["max_floor_area_sqft"] == 2700.0  # 3000 * 0.9


# ---------------------------------------------------------------------------
# Error handling robustness
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parcel_zoning_network_down():
    """When Socrata is unreachable, get_parcel_zoning returns a user-friendly error."""
    import httpx

    from src.tools.geospatial import register_geospatial_tools

    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*a, **kw):
        dec = original(*a, **kw)
        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)
        return wrap

    mcp_t.tool = capture
    register_geospatial_tools(mcp_t)

    with patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo, \
         patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls:

        mock_geo.return_value = (41.88, -87.63)
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("connection timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await tools["get_parcel_zoning"](address="123 N Michigan Ave")
        assert "error" in result
        # Should not expose a raw stack trace — error must be a string
        assert isinstance(result["error"], str)


def test_search_zoning_code_no_index_helpful_error():
    """search_zoning_code hits a missing index and returns actionable hint."""
    from src.tools.code_search import register_code_search_tools

    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*a, **kw):
        dec = original(*a, **kw)
        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)
        return wrap

    mcp_t.tool = capture
    register_code_search_tools(mcp_t)

    with patch("src.tools.code_search.load_section_index", return_value=[]):
        result = tools["search_zoning_code"](query="parking")
    assert "error" in result
    assert "ingest_title_17" in result.get("hint", "")


def test_get_zoning_section_tool_with_fixture():
    """get_zoning_section returns full section text when the index is populated."""
    from src.tools.code_search import register_code_search_tools

    fixture = [
        {
            "section": "17-3-0102",
            "title": "Accessory Dwelling Units",
            "chapter": "Chapter 17-3",
            "text": "An ADU is a secondary residential unit.",
            "source_file": "chapter_17-3.txt",
        }
    ]

    tools = _register_and_capture(register_code_search_tools)
    with patch("src.tools.code_search.load_section_index", return_value=fixture):
        result = tools["get_zoning_section"](section_number="17-3-0102")
    assert "error" not in result
    assert result["section"] == "17-3-0102"
    assert "text" in result
    assert "title" in result


def test_get_zoning_map_url_tool():
    """get_zoning_map_url returns a valid Chicago zoning map URL."""
    from src.tools.geospatial import register_geospatial_tools

    tools = _register_and_capture(register_geospatial_tools)

    # Default call (downtown Chicago)
    result = tools["get_zoning_map_url"]()
    assert "url" in result
    assert result["url"].startswith("https://gisapps.chicago.gov/")
    assert result["zoom"] == 17

    # Custom coordinates
    result = tools["get_zoning_map_url"](latitude=41.95, longitude=-87.65, zoom=13)
    assert "41.95" in result["url"]
    assert "-87.65" in result["url"]
    assert result["zoom"] == 13


def test_compare_districts_differences_key():
    """compare_districts result includes a _differences list of changed field names."""
    from src.tools.district_lookup import register_district_tools

    tools = _register_and_capture(register_district_tools)
    result = tools["compare_districts"](district_a="RS-3", district_b="RT-4")
    assert "_differences" in result
    # RS-3 and RT-4 differ on at least FAR and district title
    assert isinstance(result["_differences"], list)
    assert "floor_area_ratio" in result["_differences"]


def test_compare_same_district_no_differences():
    """Comparing a district to itself should have no _differences."""
    from src.tools.district_lookup import register_district_tools

    tools = _register_and_capture(register_district_tools)
    result = tools["compare_districts"](district_a="RS-3", district_b="RS-3")
    assert "_differences" in result
    assert result["_differences"] == []


def test_compare_districts_first_invalid():
    """compare_districts returns error dict when the first district code is invalid."""
    from src.tools.district_lookup import register_district_tools

    tools = _register_and_capture(register_district_tools)
    result = tools["compare_districts"](district_a="ZZ-99", district_b="RS-3")
    assert "error" in result
    assert "ZZ-99" in result["error"]


def test_compare_districts_second_invalid():
    """compare_districts returns error dict when the second district code is invalid."""
    from src.tools.district_lookup import register_district_tools

    tools = _register_and_capture(register_district_tools)
    result = tools["compare_districts"](district_a="RS-3", district_b="ZZ-99")
    assert "error" in result
    assert "ZZ-99" in result["error"]


def test_compare_districts_both_invalid():
    """compare_districts returns a combined error when both district codes are invalid."""
    from src.tools.district_lookup import register_district_tools

    tools = _register_and_capture(register_district_tools)
    result = tools["compare_districts"](district_a="INVALID", district_b="ALSO_INVALID")
    assert "error" in result
    # Both missing codes should be mentioned in the combined error message
    assert "INVALID" in result["error"]
    assert "ALSO_INVALID" in result["error"]


# ---------------------------------------------------------------------------
# Performance: critical path tools must respond quickly
# ---------------------------------------------------------------------------


def test_lookup_district_performance():
    """lookup_district should complete in under 100ms (in-memory CSV)."""
    from src.tools.district_lookup import register_district_tools

    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*a, **kw):
        dec = original(*a, **kw)
        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)
        return wrap

    mcp_t.tool = capture
    register_district_tools(mcp_t)

    start = time.perf_counter()
    for _ in range(20):
        tools["lookup_district"](district_code="RS-3")
    elapsed_ms = (time.perf_counter() - start) * 1000
    avg_ms = elapsed_ms / 20
    assert avg_ms < 100, f"lookup_district averaged {avg_ms:.1f}ms — too slow"


def test_development_envelope_performance():
    """calculate_development_envelope should complete in under 100ms."""
    from src.tools.development import register_development_tools

    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*a, **kw):
        dec = original(*a, **kw)
        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)
        return wrap

    mcp_t.tool = capture
    register_development_tools(mcp_t)

    start = time.perf_counter()
    for _ in range(20):
        tools["calculate_development_envelope"](district_code="B2-3", lot_area_sqft=5000)
    elapsed_ms = (time.perf_counter() - start) * 1000
    avg_ms = elapsed_ms / 20
    assert avg_ms < 100, f"calculate_development_envelope averaged {avg_ms:.1f}ms — too slow"
