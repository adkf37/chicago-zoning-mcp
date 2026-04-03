"""Automated offline eval harness — validates Q&A pairs from evals/zoning_qa.xml.

Tests the tool functions directly against expected answers for all non-network,
non-index-required questions. Questions that require live Nominatim/Socrata
or the Title 17 index are skipped here and marked ``@pytest.mark.network``
(or explicitly excluded).

Eval question IDs correspond to entries in evals/zoning_qa.xml.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import FastMCP

from src.tools.development import register_development_tools
from src.tools.district_lookup import register_district_tools
from src.tools.geospatial import register_geospatial_tools


def _capture(register_fn) -> dict:
    """Register tools into a fresh FastMCP and return tool functions by name."""
    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*args, **kwargs):
        dec = original(*args, **kwargs)

        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)

        return wrap

    mcp_t.tool = capture
    register_fn(mcp_t)
    return tools


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def district_tools():
    return _capture(register_district_tools)


@pytest.fixture(scope="module")
def development_tools():
    return _capture(register_development_tools)


@pytest.fixture(scope="module")
def geospatial_tools():
    return _capture(register_geospatial_tools)


# ---------------------------------------------------------------------------
# Q1 — RS-3 floor area ratio
# ---------------------------------------------------------------------------


def test_eval_q1_rs3_far(district_tools):
    """Eval Q1: RS-3 FAR should be 0.9."""
    result = district_tools["lookup_district"](district_code="RS-3")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# Q2 — DC-16 floor area ratio
# ---------------------------------------------------------------------------


def test_eval_q2_dc16_far(district_tools):
    """Eval Q2: DC-16 FAR should be 16."""
    result = district_tools["lookup_district"](district_code="DC-16")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(16.0)


# ---------------------------------------------------------------------------
# Q3 — RT-4 category
# ---------------------------------------------------------------------------


def test_eval_q3_rt4_category(district_tools):
    """Eval Q3: RT-4 should be in the Residential category."""
    result = district_tools["lookup_district"](district_code="RT-4")
    assert "error" not in result
    assert "Residential" in result["category"]


# ---------------------------------------------------------------------------
# Q4 — RS-3 lot area per dwelling unit contains 2500
# ---------------------------------------------------------------------------


def test_eval_q4_rs3_lot_area_per_unit(district_tools):
    """Eval Q4: RS-3 lot_area_per_unit should reference 2500 sqft per unit."""
    result = district_tools["lookup_district"](district_code="RS-3")
    assert "error" not in result
    # The raw field is "2500 sq ft/dwelling unit" — verify 2500 is present
    lot_area = result.get("lot_area_per_unit", "")
    assert "2500" in lot_area.replace(",", "")


# ---------------------------------------------------------------------------
# Q5 — DC-16 is a valid district code
# ---------------------------------------------------------------------------


def test_eval_q5_dc16_valid(district_tools):
    """Eval Q5: DC-16 should be a valid district (no error)."""
    result = district_tools["lookup_district"](district_code="DC-16")
    assert "error" not in result
    assert result["district_type_code"] == "DC-16"


# ---------------------------------------------------------------------------
# Q6 — RT-4 has higher FAR than RS-3
# ---------------------------------------------------------------------------


def test_eval_q6_rt4_higher_far_than_rs3(district_tools):
    """Eval Q6: compare_districts — RT-4 should have higher FAR than RS-3."""
    result = district_tools["compare_districts"](district_a="RS-3", district_b="RT-4")
    assert "error" not in result
    rs3_far = float(result["floor_area_ratio"]["RS-3"])
    rt4_far = float(result["floor_area_ratio"]["RT-4"])
    assert rt4_far > rs3_far, f"Expected RT-4 FAR ({rt4_far}) > RS-3 FAR ({rs3_far})"


# ---------------------------------------------------------------------------
# Q7 — B1-1 and B1-3 have different FAR
# ---------------------------------------------------------------------------


def test_eval_q7_b1_far_differs(district_tools):
    """Eval Q7: compare_districts — B1-1 and B1-3 should differ in floor_area_ratio."""
    result = district_tools["compare_districts"](district_a="B1-1", district_b="B1-3")
    assert "error" not in result
    assert "floor_area_ratio" in result["_differences"], (
        "Expected floor_area_ratio to appear in _differences for B1-1 vs B1-3"
    )
    b11_far = float(result["floor_area_ratio"]["B1-1"])
    b13_far = float(result["floor_area_ratio"]["B1-3"])
    assert b13_far > b11_far


# ---------------------------------------------------------------------------
# Q8 — 5000 sqft RS-3 → 4500 sqft max floor area
# ---------------------------------------------------------------------------


def test_eval_q8_rs3_5000_envelope(development_tools):
    """Eval Q8: 5000 sqft RS-3 lot → 4500 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="RS-3", lot_area_sqft=5000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(4500.0)


# ---------------------------------------------------------------------------
# Q9 — 10000 sqft DC-16 → 160000 sqft max floor area
# ---------------------------------------------------------------------------


def test_eval_q9_dc16_10000_envelope(development_tools):
    """Eval Q9: 10000 sqft DC-16 lot → 160,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="DC-16", lot_area_sqft=10000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(160000.0)


# ---------------------------------------------------------------------------
# Q10 — 7500 sqft RS-3 → 3 max dwelling units
# ---------------------------------------------------------------------------


def test_eval_q10_rs3_7500_units(development_tools):
    """Eval Q10: 7500 sqft RS-3 lot → 3 max dwelling units (7500 / 2500)."""
    result = development_tools["calculate_development_envelope"](
        district_code="RS-3", lot_area_sqft=7500
    )
    assert "error" not in result
    assert result["max_dwelling_units"] == 3


# ---------------------------------------------------------------------------
# Q13 — address outside Chicago returns graceful error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_eval_q13_address_outside_chicago():
    """Eval Q13: address in New York City should return a graceful 'outside Chicago' error.

    requires_network=false because we mock the geocoder to return NYC coordinates.
    The tool must validate the geocoded coordinates against Chicago bounds and return
    a helpful error without querying Socrata.
    """
    mcp_t = FastMCP("test")
    tools = {}
    original = mcp_t.tool

    def capture(*args, **kwargs):
        dec = original(*args, **kwargs)

        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)

        return wrap

    mcp_t.tool = capture
    register_geospatial_tools(mcp_t)

    with patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo:
        mock_geo.return_value = (40.7128, -74.0060)  # New York City coordinates
        result = await tools["get_parcel_zoning"](address="350 5th Ave, New York, NY")

    assert "error" in result
    assert "outside" in result["error"].lower(), (
        f"Expected 'outside' in error message, got: {result['error']}"
    )


# ---------------------------------------------------------------------------
# Q14 — get_zoning_map_url returns a gisapps.chicago.gov URL
# ---------------------------------------------------------------------------


def test_eval_q14_zoning_map_url(geospatial_tools):
    """Eval Q14: get_zoning_map_url should return a gisapps.chicago.gov URL."""
    result = geospatial_tools["get_zoning_map_url"](
        latitude=41.8789, longitude=-87.6359
    )
    assert "url" in result
    assert result["url"].startswith("https://gisapps.chicago.gov/")


# ---------------------------------------------------------------------------
# Q20 — offline multi-step: compare RS-3 vs RT-4, calculate units for 6000 sqft
# ---------------------------------------------------------------------------


def test_eval_q20_multistep_rezone_units(district_tools, development_tools):
    """Eval Q20: offline multi-step — compare RS-3 and RT-4, compute unit delta.

    RS-3: 6000 / 2500 = 2 units.
    RT-4: 6000 / 1000 = 6 units.
    Delta = 4 additional units after rezoning from RS-3 to RT-4.
    """
    # Step 1: Confirm the two districts differ in lot_area_per_unit
    comparison = district_tools["compare_districts"](district_a="RS-3", district_b="RT-4")
    assert "error" not in comparison
    assert "lot_area_per_unit" in comparison["_differences"]

    # Step 2: Calculate envelope for each
    rs3_env = development_tools["calculate_development_envelope"](
        district_code="RS-3", lot_area_sqft=6000
    )
    rt4_env = development_tools["calculate_development_envelope"](
        district_code="RT-4", lot_area_sqft=6000
    )
    assert "error" not in rs3_env
    assert "error" not in rt4_env

    rs3_units = rs3_env["max_dwelling_units"]
    rt4_units = rt4_env["max_dwelling_units"]
    assert isinstance(rs3_units, int)
    assert isinstance(rt4_units, int)
    assert rt4_units > rs3_units, (
        f"Expected RT-4 ({rt4_units} units) to allow more units than RS-3 ({rs3_units} units)"
    )
    assert (rt4_units - rs3_units) == 4, (
        f"Expected 4 additional units after rezoning, got {rt4_units - rs3_units}"
    )
