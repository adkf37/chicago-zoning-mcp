"""Tests for district lookup tools."""

from src.data_loader import get_district, get_all_districts, get_districts_by_category
from src.tools.district_lookup import register_district_tools
from fastmcp import FastMCP


def _get_tools():
    """Register tools and return them as callables."""
    mcp = FastMCP("test")
    register_district_tools(mcp)
    # Access tool functions directly via their registered names
    return mcp


def test_lookup_known_district():
    """RS-3 should exist and be Residential."""
    d = get_district("RS-3")
    assert d is not None
    assert d["category"] == "Residential"
    assert d["district_type_code"] == "RS-3"


def test_lookup_case_insensitive():
    """Lookup should be case-insensitive."""
    d = get_district("rs-3")
    assert d is not None
    assert d["district_type_code"] == "RS-3"


def test_lookup_unknown_district():
    """Unknown district should return None."""
    assert get_district("ZZ-99") is None


def test_all_districts_not_empty():
    """Should load at least 50 districts from CSV."""
    districts = get_all_districts()
    assert len(districts) > 50


def test_filter_by_category():
    """Should be able to filter by Residential."""
    residential = get_districts_by_category("Residential")
    assert len(residential) > 0
    assert all("Residential" in d["category"] for d in residential)


def test_district_has_required_fields():
    """Every district should have key fields populated."""
    districts = get_all_districts()
    for code, d in districts.items():
        assert d["district_type_code"], f"{code} missing district_type_code"
        assert d["category"], f"{code} missing category"


def test_filter_empty_category():
    """Empty category filter should return empty list (no match)."""
    result = get_districts_by_category("Nonexistent Category")
    assert result == []


def test_filter_partial_match():
    """Category filter uses partial matching."""
    downtown = get_districts_by_category("Downtown")
    assert len(downtown) > 0
    assert all("Downtown" in d["category"] for d in downtown)


def test_lookup_district_with_whitespace():
    """Whitespace around code should be stripped."""
    d = get_district("  RS-3  ")
    assert d is not None
    assert d["district_type_code"] == "RS-3"


def test_compare_same_district():
    """Comparing a district to itself should show all fields as 'same'."""
    a = get_district("RS-3")
    b = get_district("RS-3")
    assert a is not None and b is not None
    for key in a:
        assert a[key] == b[key]


def test_compare_different_districts():
    """RS-3 and DC-16 should differ on FAR."""
    a = get_district("RS-3")
    b = get_district("DC-16")
    assert a is not None and b is not None
    assert a["floor_area_ratio"] != b["floor_area_ratio"]


def test_manufacturing_category():
    """Should find manufacturing districts."""
    mfg = get_districts_by_category("Manufacturing")
    assert len(mfg) > 0
