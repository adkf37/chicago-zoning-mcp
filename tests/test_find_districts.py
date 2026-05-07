"""Tests for find_districts_meeting_criteria tool."""

from fastmcp import FastMCP

from src.tools.district_lookup import (
    _parse_far,
    _parse_lot_per_unit,
    register_district_tools,
)

# ---------------------------------------------------------------------------
# Helper: call the tool via the registered MCP function
# ---------------------------------------------------------------------------


def _get_tool():
    mcp = FastMCP("test")
    tools = {}
    original = mcp.tool

    def capture(*a, **kw):
        dec = original(*a, **kw)
        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)
        return wrap

    mcp.tool = capture
    register_district_tools(mcp)
    return tools["find_districts_meeting_criteria"]


find_districts_meeting_criteria = _get_tool()


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------


def test_parse_far_numeric():
    assert _parse_far("3.0") == 3.0
    assert _parse_far("0.9") == 0.9


def test_parse_far_non_numeric():
    assert _parse_far("Varies by planned development ordinance") is None
    assert _parse_far("") is None
    assert _parse_far(None) is None


def test_parse_lot_per_unit_with_commas():
    assert _parse_lot_per_unit("2,500 sq ft/dwelling unit") == 2500.0
    assert _parse_lot_per_unit("1,000 sq ft/dwelling unit, 700 sq ft/efficiency unit") == 1000.0


def test_parse_lot_per_unit_non_numeric():
    assert _parse_lot_per_unit("N/A") is None
    assert _parse_lot_per_unit("") is None


# ---------------------------------------------------------------------------
# Integration tests — real CSV data
# ---------------------------------------------------------------------------


def test_no_filters_returns_all_districts():
    result = find_districts_meeting_criteria()
    assert result["matching_count"] > 50
    assert len(result["districts"]) == result["matching_count"]


def test_min_far_filter():
    """Districts with FAR >= 10 should exist (downtown) and exclude RS-3 (FAR 0.9)."""
    result = find_districts_meeting_criteria(min_far=10.0)
    assert result["matching_count"] > 0
    codes = {d["district_type_code"] for d in result["districts"]}
    assert "RS-3" not in codes
    # All returned districts should have numeric FAR >= 10
    for d in result["districts"]:
        far = _parse_far(d["floor_area_ratio"])
        assert far is not None
        assert far >= 10.0


def test_max_far_filter():
    """Districts with FAR <= 1 should exclude high-density downtown districts."""
    result = find_districts_meeting_criteria(max_far=1.0)
    assert result["matching_count"] > 0
    codes = {d["district_type_code"] for d in result["districts"]}
    assert "DC-16" not in codes
    for d in result["districts"]:
        far = _parse_far(d["floor_area_ratio"])
        assert far is not None
        assert far <= 1.0


def test_far_range_filter():
    result = find_districts_meeting_criteria(min_far=2.0, max_far=4.0)
    assert result["matching_count"] > 0
    for d in result["districts"]:
        far = _parse_far(d["floor_area_ratio"])
        assert far is not None
        assert 2.0 <= far <= 4.0


def test_min_far_max_far_conflict_returns_error():
    result = find_districts_meeting_criteria(min_far=5.0, max_far=2.0)
    assert "error" in result


def test_min_dwelling_units_requires_lot_area():
    result = find_districts_meeting_criteria(min_dwelling_units=4)
    assert "error" in result


def test_min_dwelling_units_on_lot():
    """A 7,500 sqft lot should find districts supporting >= 4 units."""
    result = find_districts_meeting_criteria(min_dwelling_units=4, lot_area_sqft=7500.0)
    assert result["matching_count"] > 0
    for d in result["districts"]:
        units = d["max_dwelling_units"]
        assert isinstance(units, int), f"Expected int, got {units!r} for {d['district_type_code']}"
        assert units >= 4


def test_lot_area_without_unit_filter_adds_max_units():
    """When lot_area_sqft is given, max_dwelling_units should appear in results."""
    result = find_districts_meeting_criteria(lot_area_sqft=5000.0)
    assert result["matching_count"] > 0
    for d in result["districts"]:
        assert "max_dwelling_units" in d


def test_category_filter_residential():
    result = find_districts_meeting_criteria(category="Residential")
    assert result["matching_count"] > 0
    for d in result["districts"]:
        assert "Residential" in d["category"]


def test_results_sorted_by_far_descending():
    """Results should be sorted by FAR from highest to lowest."""
    result = find_districts_meeting_criteria(category="Downtown Core")
    fars = [
        _parse_far(d["floor_area_ratio"])
        for d in result["districts"]
        if _parse_far(d["floor_area_ratio"]) is not None
    ]
    assert fars == sorted(fars, reverse=True)


def test_applied_filters_recorded():
    result = find_districts_meeting_criteria(min_far=1.0, category="Residential")
    assert result["applied_filters"]["min_far"] == 1.0
    assert result["applied_filters"]["category"] == "Residential"


def test_unknown_category_returns_empty():
    result = find_districts_meeting_criteria(category="Atlantis")
    assert result["matching_count"] == 0
    assert result["districts"] == []
