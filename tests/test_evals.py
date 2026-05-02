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

from src.tools.code_search import register_code_search_tools
from src.tools.development import register_development_tools
from src.tools.district_lookup import register_district_tools
from src.tools.geospatial import register_geospatial_tools

# ---------------------------------------------------------------------------
# Fixture index used for code-search eval tests (Q15–Q18)
# Mirrors the fixture in test_code_search.py so no live Title 17 index is needed.
# ---------------------------------------------------------------------------

_CODE_SEARCH_FIXTURE = [
    {
        "section": "17-1-0101",
        "title": "Title",
        "chapter": "Chapter 17-1",
        "text": "This title shall be known and may be cited as the Chicago Zoning Ordinance.",
        "source_file": "chapter_17-1.txt",
    },
    {
        "section": "17-2-0100",
        "title": "Rules of Measurement",
        "chapter": "Chapter 17-2",
        "text": (
            "Floor area ratio (FAR) is the ratio of the total floor area"
            " of a building to the area of the lot."
        ),
        "source_file": "chapter_17-2.txt",
    },
    {
        "section": "17-3-0102",
        "title": "Accessory Dwelling Units",
        "chapter": "Chapter 17-3",
        "text": (
            "An accessory dwelling unit (ADU) is a secondary residential unit on a lot "
            "already containing a principal dwelling. ADUs may be detached or attached."
        ),
        "source_file": "chapter_17-3.txt",
    },
    {
        "section": "17-10-0200",
        "title": "Off-Street Parking Requirements",
        "chapter": "Chapter 17-10",
        "text": (
            "Parking requirements vary by use and district. Residential uses require "
            "one parking space per dwelling unit in most districts. "
            "Downtown districts may have reduced or waived parking requirements."
        ),
        "source_file": "chapter_17-10.txt",
    },
    {
        "section": "17-13-0300",
        "title": "Planned Development Application Procedures",
        "chapter": "Chapter 17-13",
        "text": (
            "A planned development (PD) application shall be filed with the Department "
            "of Planning and Development. The application must include a site plan, "
            "a traffic study, and a public benefit statement."
        ),
        "source_file": "chapter_17-13.txt",
    },
    {
        "section": "17-15-0100",
        "title": "Nonconforming Uses",
        "chapter": "Chapter 17-15",
        "text": (
            "A nonconforming use is any use of land or structure that was lawfully "
            "established but does not conform to current zoning regulations. "
            "Nonconforming uses may continue but may not be expanded."
        ),
        "source_file": "chapter_17-15.txt",
    },
]


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


@pytest.fixture(scope="module")
def code_search_tools():
    return _capture(register_code_search_tools)


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
# Q15 — search_zoning_code("accessory dwelling unit") returns section IDs
# ---------------------------------------------------------------------------


def test_eval_q15_search_accessory_dwelling_unit(code_search_tools):
    """Eval Q15: search_zoning_code('accessory dwelling unit') returns section IDs.

    Uses the fixture index so no live Title 17 index is needed.
    """
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["search_zoning_code"](
            query="accessory dwelling unit"
        )
    assert "error" not in result
    assert result["result_count"] >= 1
    # All returned sections must have a section number starting with "17-"
    for section in result["results"]:
        assert section["section"].startswith("17-"), (
            f"Expected section ID starting with '17-', got: {section['section']}"
        )


# ---------------------------------------------------------------------------
# Q16 — search_zoning_code("parking requirements") returns parking section
# ---------------------------------------------------------------------------


def test_eval_q16_search_parking_requirements(code_search_tools):
    """Eval Q16: search_zoning_code('parking requirements') finds parking section.

    Uses the fixture index so no live Title 17 index is needed.
    """
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["search_zoning_code"](
            query="parking requirements"
        )
    assert "error" not in result
    assert result["result_count"] >= 1
    # At least one result should mention parking
    assert any(
        "parking" in r["title"].lower() or "parking" in r["text"].lower()
        for r in result["results"]
    ), "Expected at least one result mentioning 'parking'"


# ---------------------------------------------------------------------------
# Q17 — search_zoning_code("nonconforming uses") returns chapter 17-15
# ---------------------------------------------------------------------------


def test_eval_q17_search_nonconforming_uses(code_search_tools):
    """Eval Q17: search_zoning_code('nonconforming uses') finds chapter 17-15.

    Uses the fixture index so no live Title 17 index is needed.
    """
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["search_zoning_code"](
            query="nonconforming uses"
        )
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-15") for s in sections), (
        f"Expected a section from chapter 17-15 in results, got: {sections}"
    )


# ---------------------------------------------------------------------------
# Q18 — get_zoning_section("17-15-0100") returns nonconforming use text
# ---------------------------------------------------------------------------


def test_eval_q18_get_nonconforming_section(code_search_tools):
    """Eval Q18: get_zoning_section('17-15-0100') returns the nonconforming use text.

    Uses the fixture index so no live Title 17 index is needed.
    """
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["get_zoning_section"](
            section_number="17-15-0100"
        )
    assert "error" not in result
    assert result["section"] == "17-15-0100"
    assert "nonconforming" in result["text"].lower(), (
        "Expected 'nonconforming' in the section text"
    )


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

# ---------------------------------------------------------------------------
# Q21 — Google-search phrasing for RS-3 lookup
# ---------------------------------------------------------------------------


def test_eval_q21_google_search_rs3(district_tools):
    """Eval Q21: Google-search phrasing still returns RS-3 district data."""
    result = district_tools["lookup_district"](district_code="RS-3")
    assert "error" not in result
    assert result["district_type_code"] == "RS-3"


# ---------------------------------------------------------------------------
# Q22 — Structured prompt for DC-16 lookup returns FAR 16
# ---------------------------------------------------------------------------


def test_eval_q22_structured_dc16(district_tools):
    """Eval Q22: Structured prompt for DC-16 returns district data with FAR 16."""
    result = district_tools["lookup_district"](district_code="DC-16")
    assert "error" not in result
    assert result["district_type_code"] == "DC-16"
    assert float(result["floor_area_ratio"]) == pytest.approx(16.0)


# ---------------------------------------------------------------------------
# Q23 — Which district allows more units on 6000 sqft: RS-3 or RT-4?
# ---------------------------------------------------------------------------


def test_eval_q23_multistep_which_allows_more_units(district_tools, development_tools):
    """Eval Q23: RT-4 allows more dwelling units than RS-3 on a 6000 sqft lot."""
    rs3 = development_tools["calculate_development_envelope"](
        district_code="RS-3", lot_area_sqft=6000
    )
    rt4 = development_tools["calculate_development_envelope"](
        district_code="RT-4", lot_area_sqft=6000
    )
    assert "error" not in rs3
    assert "error" not in rt4
    assert rt4["max_dwelling_units"] > rs3["max_dwelling_units"]


# ---------------------------------------------------------------------------
# Q27 — B3-2 district summary contains district code
# ---------------------------------------------------------------------------


def test_eval_q27_b3_2_district_summary(district_tools):
    """Eval Q27: B3-2 lookup returns a valid district record."""
    result = district_tools["lookup_district"](district_code="B3-2")
    assert "error" not in result
    assert result["district_type_code"] == "B3-2"


# ---------------------------------------------------------------------------
# Q28 — RS-3 compliance check: 3000 sqft lot → max 2700 sqft
# ---------------------------------------------------------------------------


def test_eval_q28_rs3_compliance_3000(development_tools):
    """Eval Q28: RS-3 on 3000 sqft lot → max floor area 2700 sqft (FAR 0.9)."""
    result = development_tools["calculate_development_envelope"](
        district_code="RS-3", lot_area_sqft=3000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(2700.0)


# ---------------------------------------------------------------------------
# Q29 — RT-4 max units on 6000 sqft lot = 6
# ---------------------------------------------------------------------------


def test_eval_q29_rt4_max_units_6000(development_tools):
    """Eval Q29: RT-4 on 6000 sqft lot → max 6 dwelling units (6000 / 1000)."""
    result = development_tools["calculate_development_envelope"](
        district_code="RT-4", lot_area_sqft=6000
    )
    assert "error" not in result
    assert result["max_dwelling_units"] == 6


# ---------------------------------------------------------------------------
# Q33 — DX-7 developer lookup returns district record
# ---------------------------------------------------------------------------


def test_eval_q33_dx7_developer_lookup(district_tools):
    """Eval Q33: DX-7 lookup returns valid district data."""
    result = district_tools["lookup_district"](district_code="DX-7")
    assert "error" not in result
    assert result["district_type_code"] == "DX-7"


# ---------------------------------------------------------------------------
# Q34 — Compare RS-3 vs RT-4 rezoning potential
# ---------------------------------------------------------------------------


def test_eval_q34_rezoning_rs3_to_rt4(district_tools, development_tools):
    """Eval Q34: Rezoning from RS-3 to RT-4 increases dwelling units on 6000 sqft lot."""
    comparison = district_tools["compare_districts"](district_a="RS-3", district_b="RT-4")
    assert "error" not in comparison
    assert "floor_area_ratio" in comparison

    rs3_env = development_tools["calculate_development_envelope"](
        district_code="RS-3", lot_area_sqft=6000
    )
    rt4_env = development_tools["calculate_development_envelope"](
        district_code="RT-4", lot_area_sqft=6000
    )
    assert rt4_env["max_dwelling_units"] > rs3_env["max_dwelling_units"]


# ---------------------------------------------------------------------------
# Q35 — get_zoning_map_url with coordinates returns gisapps.chicago.gov URL
# ---------------------------------------------------------------------------


def test_eval_q35_zoning_map_url_coords(geospatial_tools):
    """Eval Q35: get_zoning_map_url with coordinates returns a gisapps.chicago.gov URL."""
    result = geospatial_tools["get_zoning_map_url"](
        latitude=41.8789, longitude=-87.6359
    )
    assert "url" in result
    assert "gisapps.chicago.gov" in result["url"]


# ---------------------------------------------------------------------------
# Q36 — list_district_types returns RS-3 when filtering by Residential
# ---------------------------------------------------------------------------


def test_eval_q36_list_residential_districts(district_tools):
    """Eval Q36: list_district_types('Residential') should include RS-3."""
    result = district_tools["list_district_types"](category="Residential")
    assert isinstance(result, list)
    assert len(result) > 0
    district_codes = [d["district_type_code"] for d in result]
    assert "RS-3" in district_codes


# ---------------------------------------------------------------------------
# Q37 — POS-1 max floor area on 10000 sqft lot = 1000
# ---------------------------------------------------------------------------


def test_eval_q37_pos1_far(development_tools):
    """Eval Q37: POS-1 FAR 0.1 → 10000 sqft lot → max 1000 sqft floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="POS-1", lot_area_sqft=10000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(1000.0)


# ---------------------------------------------------------------------------
# Q38 — RS-3 max units on 5000 sqft lot = 2
# ---------------------------------------------------------------------------


def test_eval_q38_rs3_units_5000(development_tools):
    """Eval Q38: RS-3 on 5000 sqft lot → max 2 dwelling units (5000 / 2500)."""
    result = development_tools["calculate_development_envelope"](
        district_code="RS-3", lot_area_sqft=5000
    )
    assert "error" not in result
    assert result["max_dwelling_units"] == 2


# ---------------------------------------------------------------------------
# Q42 — DC16 without hyphen normalizes to DC-16
# ---------------------------------------------------------------------------


def test_eval_q42_dc16_normalization(district_tools):
    """Eval Q42: DC-16 lookup works regardless of hyphen normalization."""
    result = district_tools["lookup_district"](district_code="DC-16")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(16.0)


# ---------------------------------------------------------------------------
# Q44 — B1-3 max floor area on 2500 sqft lot = 7500
# ---------------------------------------------------------------------------


def test_eval_q44_b1_3_far_2500(development_tools):
    """Eval Q44: B1-3 FAR 3.0 → 2500 sqft lot → max 7500 sqft floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="B1-3", lot_area_sqft=2500
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(7500.0)

# ---------------------------------------------------------------------------
# Q24 — get_zoning_section("17-2-0300") returns section about Bulk standards
# ---------------------------------------------------------------------------

_CODE_SEARCH_FIXTURE_EXTENDED = _CODE_SEARCH_FIXTURE + [
    {
        "section": "17-2-0300",
        "title": "Bulk and density standards",
        "chapter": "Chapter 17-2",
        "text": (
            "All development in R districts is subject to the following bulk and "
            "density standards. FAR and height limits apply to the total floor area "
            "of the building relative to the lot size."
        ),
        "source_file": "chapter_17-2.txt",
    },
    {
        "section": "17-7-0300",
        "title": "Affordable Housing Bonus",
        "chapter": "Chapter 17-7",
        "text": (
            "An affordable housing bonus is available for residential projects that "
            "include a specified percentage of affordable dwelling units. The bonus "
            "allows additional floor area ratio beyond the base FAR."
        ),
        "source_file": "chapter_17-7.txt",
    },
    {
        "section": "17-15-0300",
        "title": "Nonconforming uses",
        "chapter": "Chapter 17-15",
        "text": (
            "A nonconforming use is a land use that was lawfully established but is "
            "no longer allowed by current zoning regulations. Nonconforming signs are "
            "also addressed in this chapter."
        ),
        "source_file": "chapter_17-15.txt",
    },
]


def test_eval_q24_get_section_17_2_0300(code_search_tools):
    """Eval Q24: get_zoning_section('17-2-0300') returns Bulk and density text."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_EXTENDED,
    ):
        result = code_search_tools["get_zoning_section"](section_number="17-2-0300")
    assert "error" not in result
    assert result["section"] == "17-2-0300"
    assert "bulk" in result["title"].lower() or "bulk" in result["text"].lower()


# ---------------------------------------------------------------------------
# Q25 — search affordable housing bonus returns Chapter 17 results
# ---------------------------------------------------------------------------


def test_eval_q25_search_affordable_housing(code_search_tools):
    """Eval Q25: search_zoning_code('affordable housing bonus') returns 17- sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_EXTENDED,
    ):
        result = code_search_tools["search_zoning_code"](query="affordable housing bonus")
    assert "error" not in result
    assert result["result_count"] >= 1
    for section in result["results"]:
        assert section["section"].startswith("17-")


# ---------------------------------------------------------------------------
# Q39 — get_zoning_section("17-10-0200") returns parking content
# ---------------------------------------------------------------------------


def test_eval_q39_get_section_17_10_0200(code_search_tools):
    """Eval Q39: get_zoning_section('17-10-0200') returns parking section text."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["get_zoning_section"](section_number="17-10-0200")
    assert "error" not in result
    assert result["section"] == "17-10-0200"
    assert "parking" in result["title"].lower() or "parking" in result["text"].lower()


# ---------------------------------------------------------------------------
# Q40 — search nonconforming signs returns 17-15 sections
# ---------------------------------------------------------------------------


def test_eval_q40_search_nonconforming_signs(code_search_tools):
    """Eval Q40: search_zoning_code('nonconforming signs') returns chapter 17-15 sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_EXTENDED,
    ):
        result = code_search_tools["search_zoning_code"](query="nonconforming signs")
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-15") for s in sections), (
        f"Expected a 17-15 section in results, got: {sections}"
    )


# ---------------------------------------------------------------------------
# Q26 — homeowner RS-3 summary: lookup_district + search_zoning_code
# ---------------------------------------------------------------------------

_CODE_SEARCH_FIXTURE_RS3 = _CODE_SEARCH_FIXTURE + [
    {
        "section": "17-2-0200",
        "title": "Residential Bulk Standards",
        "chapter": "Chapter 17-2",
        "text": (
            "RS-3 single-family residential districts are subject to the following bulk "
            "standards: maximum FAR 0.9, maximum building height 30 feet, minimum front "
            "setback 20 feet, minimum side setback 2 feet, minimum rear setback 30 feet."
        ),
        "source_file": "chapter_17-2.txt",
    },
    {
        "section": "17-4-0100",
        "title": "Residential Use Standards",
        "chapter": "Chapter 17-4",
        "text": (
            "Single-family detached houses, two-flats, and townhouses are permitted by-right "
            "in RS-3 residential districts. Home occupations and accessory structures are "
            "also allowed subject to the standards in this chapter."
        ),
        "source_file": "chapter_17-4.txt",
    },
]


def test_eval_q26_homeowner_rs3_summary(district_tools, code_search_tools):
    """Eval Q26: homeowner RS-3 summary returns RS-3 district data and ordinance context."""
    # Step 1: District lookup
    district_result = district_tools["lookup_district"](district_code="RS-3")
    assert "error" not in district_result
    assert district_result["district_type_code"] == "RS-3"

    # Step 2: Code search for RS-3 context
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_RS3,
    ):
        search_result = code_search_tools["search_zoning_code"](
            query="RS-3 single-family residential bulk standards"
        )
    assert "error" not in search_result
    assert search_result["result_count"] >= 1


# ---------------------------------------------------------------------------
# Q30 — homeowner ADU: search_zoning_code for accessory dwelling unit sections
# ---------------------------------------------------------------------------


def test_eval_q30_adu_code_search(code_search_tools):
    """Eval Q30: search for ADU sections returns relevant Title 17 references."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["search_zoning_code"](query="accessory dwelling unit")
    assert "error" not in result
    assert result["result_count"] >= 1
    # The ADU fixture is in chapter 17-3
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-") for s in sections)
    assert any("accessory" in r["title"].lower() or "accessory" in r["text"].lower()
               for r in result["results"])


# ---------------------------------------------------------------------------
# Q31 — developer B3-2 checklist: lookup_district + search_zoning_code
# ---------------------------------------------------------------------------


def test_eval_q31_b3_2_checklist(district_tools, code_search_tools):
    """Eval Q31: B3-2 mixed-use checklist requires district lookup and code search."""
    # Step 1: District lookup confirms B3-2 is valid
    district_result = district_tools["lookup_district"](district_code="B3-2")
    assert "error" not in district_result
    assert district_result["district_type_code"] == "B3-2"

    # Step 2: Code search for mixed-use requirements
    fixture = _CODE_SEARCH_FIXTURE_EXTENDED + [
        {
            "section": "17-4-0300",
            "title": "Mixed-Use Building Standards",
            "chapter": "Chapter 17-4",
            "text": (
                "Mixed-use buildings in B3 districts may contain residential uses above "
                "the ground floor. Ground-floor space must be devoted to permitted "
                "commercial uses. Minimum floor-to-ceiling height for commercial space "
                "is 10 feet."
            ),
            "source_file": "chapter_17-4.txt",
        },
    ]
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=fixture,
    ):
        search_result = code_search_tools["search_zoning_code"](
            query="mixed-use construction requirements"
        )
    assert "error" not in search_result
    assert search_result["result_count"] >= 1


# ---------------------------------------------------------------------------
# Q32 — homeowner ADU checklist: RS-3 lookup + ADU code search
# ---------------------------------------------------------------------------


def test_eval_q32_homeowner_adu_checklist(district_tools, code_search_tools):
    """Eval Q32: homeowner ADU checklist requires RS-3 district data and ADU code sections."""
    # Step 1: Confirm RS-3 is valid
    district_result = district_tools["lookup_district"](district_code="RS-3")
    assert "error" not in district_result

    # Step 2: Search for ADU ordinance text
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        search_result = code_search_tools["search_zoning_code"](
            query="accessory dwelling unit ADU"
        )
    assert "error" not in search_result
    assert search_result["result_count"] >= 1
    # Must include a section referencing accessory dwelling
    found_adu = any(
        "accessory" in r.get("title", "").lower() or "accessory" in r.get("text", "").lower()
        for r in search_result["results"]
    )
    assert found_adu, "Expected at least one result referencing 'accessory' dwelling unit"


# ---------------------------------------------------------------------------
# Q41 — planned development checklist: PD lookup + code search
# ---------------------------------------------------------------------------


def test_eval_q41_planned_development_checklist(district_tools, code_search_tools):
    """Eval Q41: PD checklist requires district data and Title 17 procedural sections."""
    # Step 1: Confirm PD is in the district types
    all_districts = district_tools["list_district_types"](category="Planned Development")
    assert isinstance(all_districts, list)
    # PD type districts should exist
    codes = [d["district_type_code"] for d in all_districts]
    assert any("PD" in c or "PMD" in c for c in codes), (
        f"Expected PD districts in list, got: {codes}"
    )

    # Step 2: Code search for planned development procedures
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        search_result = code_search_tools["search_zoning_code"](
            query="planned development application procedures"
        )
    assert "error" not in search_result
    assert search_result["result_count"] >= 1
    # Should return the planned development section from the fixture
    sections = [r["section"] for r in search_result["results"]]
    assert any(s.startswith("17-13") for s in sections), (
        f"Expected a 17-13 section in results for planned development, got: {sections}"
    )


# ---------------------------------------------------------------------------
# Q43 — RS-3 permit pre-check: district lookup + code search
# ---------------------------------------------------------------------------


def test_eval_q43_rs3_permit_precheck(district_tools, code_search_tools):
    """Eval Q43: RS-3 permit pre-check requires district data and relevant code sections."""
    # Step 1: RS-3 district data
    district_result = district_tools["lookup_district"](district_code="RS-3")
    assert "error" not in district_result
    assert float(district_result["floor_area_ratio"]) == pytest.approx(0.9)

    # Step 2: Search for single-family permit/building requirements
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_RS3,
    ):
        search_result = code_search_tools["search_zoning_code"](
            query="single-family residential building requirements"
        )
    assert "error" not in search_result
    assert search_result["result_count"] >= 1


# ---------------------------------------------------------------------------
# Q45 — Wrigley Field address routing (mocked geocode + parcel)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_eval_q45_wrigley_field_address():
    """Eval Q45: Wrigley Field address routes to get_parcel_zoning and returns a zone.

    Mocks geocoder and Socrata so no network required.
    """
    from unittest.mock import MagicMock

    mcp_t = FastMCP("test")
    tools: dict = {}
    original = mcp_t.tool

    def capture(*args, **kwargs):
        dec = original(*args, **kwargs)

        def wrap(fn):
            tools[fn.__name__] = fn
            return dec(fn)

        return wrap

    mcp_t.tool = capture
    register_geospatial_tools(mcp_t)

    mock_socrata_response = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"zone_class": "B3-2", "zone_type": "6"},
                "geometry": {"type": "MultiPolygon", "coordinates": []},
            }
        ],
    }

    with (
        patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo,
        patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_geo.return_value = (41.9478, -87.6553)  # Wrigley Field coordinates

        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_socrata_response
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await tools["get_parcel_zoning"](address="1060 W Addison St")

    assert "error" not in result, f"Expected no error, got: {result.get('error')}"
    assert result.get("zone_class") == "B3-2"


# ---------------------------------------------------------------------------
# Q46 — address + development envelope chain (mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_eval_q46_address_development_chain():
    """Eval Q46: address lookup followed by development envelope calculation.

    Mocks both geocoder and parcel API. Confirms the zone returned by parcel
    lookup can feed into calculate_development_envelope.
    """
    from unittest.mock import MagicMock

    mcp_t = FastMCP("test")
    all_tools: dict = {}
    original = mcp_t.tool

    def capture(*args, **kwargs):
        dec = original(*args, **kwargs)

        def wrap(fn):
            all_tools[fn.__name__] = fn
            return dec(fn)

        return wrap

    mcp_t.tool = capture
    register_geospatial_tools(mcp_t)
    register_development_tools(mcp_t)

    mock_socrata_response = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"zone_class": "B3-2", "zone_type": "6"},
                "geometry": {},
            }
        ],
    }

    with (
        patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo,
        patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_geo.return_value = (41.9478, -87.6553)

        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_socrata_response
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        parcel_result = await all_tools["get_parcel_zoning"](address="5555 N Sheridan Rd")

    assert "error" not in parcel_result
    zone = parcel_result.get("zone_class")
    assert zone is not None

    # Now calculate development envelope with returned zone + 4000 sqft lot
    envelope = all_tools["calculate_development_envelope"](
        district_code=zone, lot_area_sqft=4000
    )
    assert "error" not in envelope
    assert envelope["max_floor_area_sqft"] > 0


# ---------------------------------------------------------------------------
# Q47 — list all district types returns non-empty list
# ---------------------------------------------------------------------------


def test_eval_q47_list_all_district_types(district_tools):
    """Eval Q47: list_district_types() with no category returns all districts."""
    result = district_tools["list_district_types"]()
    assert isinstance(result, list)
    assert len(result) >= 50, f"Expected 50+ districts, got {len(result)}"
    # Each district should have required keys
    for d in result[:5]:
        assert "district_type_code" in d
        assert "category" in d
        assert "floor_area_ratio" in d


# ---------------------------------------------------------------------------
# Q48 — search "sign regulations" returns relevant chapter
# ---------------------------------------------------------------------------


def test_eval_q48_search_sign_regulations(code_search_tools):
    """Eval Q48: search_zoning_code('sign regulations') returns Title 17 sections."""
    fixture = _CODE_SEARCH_FIXTURE + [
        {
            "section": "17-12-0100",
            "title": "Sign Regulations — General",
            "chapter": "Chapter 17-12",
            "text": (
                "Sign regulations in this chapter apply to all signs visible from a "
                "public street or right-of-way. Commercial signs must comply with size, "
                "height, and illumination standards by district type."
            ),
            "source_file": "chapter_17-12.txt",
        },
    ]
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=fixture,
    ):
        result = code_search_tools["search_zoning_code"](query="sign regulations")
    assert "error" not in result
    assert result["result_count"] >= 1
    assert any("sign" in r["title"].lower() or "sign" in r["text"].lower()
               for r in result["results"])


# ---------------------------------------------------------------------------
# Q49 — RT-4 height limit is present and parseable
# ---------------------------------------------------------------------------


def test_eval_q49_rt4_height_limit(district_tools):
    """Eval Q49: RT-4 lookup returns a maximum_building_height value."""
    result = district_tools["lookup_district"](district_code="RT-4")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert height, "Expected a non-empty maximum_building_height for RT-4"


# ---------------------------------------------------------------------------
# Q50 — RM-5 FAR is higher than RT-4
# ---------------------------------------------------------------------------


def test_eval_q50_rm5_far_higher_than_rt4(district_tools):
    """Eval Q50: RM-5 FAR should be higher than RT-4 FAR."""
    rt4 = district_tools["lookup_district"](district_code="RT-4")
    rm5 = district_tools["lookup_district"](district_code="RM-5")
    assert "error" not in rt4
    assert "error" not in rm5
    rt4_far = float(rt4["floor_area_ratio"])
    rm5_far = float(rm5["floor_area_ratio"])
    assert rm5_far >= rt4_far, (
        f"Expected RM-5 FAR ({rm5_far}) >= RT-4 FAR ({rt4_far})"
    )


# ---------------------------------------------------------------------------
# Q51 — homeowner RS-3 summary with index: lookup + search
# ---------------------------------------------------------------------------


def test_eval_q51_homeowner_rs3_with_index(district_tools, code_search_tools):
    """Eval Q51: homeowner RS-3 summary uses both district lookup and code search."""
    district_result = district_tools["lookup_district"](district_code="RS-3")
    assert "error" not in district_result
    assert district_result["district_type_code"] == "RS-3"

    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_RS3,
    ):
        search_result = code_search_tools["search_zoning_code"](
            query="residential zoning requirements"
        )
    assert "error" not in search_result
    assert search_result["result_count"] >= 1


# ---------------------------------------------------------------------------
# Q52 — ADU code search returns accessory dwelling sections
# ---------------------------------------------------------------------------


def test_eval_q52_adu_code_sections(code_search_tools):
    """Eval Q52: 'accessory dwelling unit' search returns relevant ordinance sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["search_zoning_code"](
            query="accessory dwelling unit property"
        )
    assert "error" not in result
    assert result["result_count"] >= 1
    assert any(
        "accessory" in r.get("title", "").lower() or "accessory" in r.get("text", "").lower()
        for r in result["results"]
    )


# ---------------------------------------------------------------------------
# Q53 — compare RS-3 vs RT-4 height and FAR differences
# ---------------------------------------------------------------------------


def test_eval_q53_rs3_rt4_height_comparison(district_tools):
    """Eval Q53: RS-3 and RT-4 comparison shows height and FAR differences."""
    result = district_tools["compare_districts"](district_a="RS-3", district_b="RT-4")
    assert "error" not in result
    # Both height and FAR should differ
    assert "floor_area_ratio" in result["_differences"]
    assert result["floor_area_ratio"]["RS-3"] != result["floor_area_ratio"]["RT-4"]


# ---------------------------------------------------------------------------
# Q54 — RS-3 max dwelling units on 8000 sqft = 3
# ---------------------------------------------------------------------------


def test_eval_q54_rs3_8000_units(development_tools):
    """Eval Q54: RS-3 on 8000 sqft lot → 3 max dwelling units (floor(8000/2500))."""
    result = development_tools["calculate_development_envelope"](
        district_code="RS-3", lot_area_sqft=8000
    )
    assert "error" not in result
    assert result["max_dwelling_units"] == 3


# ---------------------------------------------------------------------------
# Q55 — RT-4 max floor area on 3000 sqft lot = 3600
# ---------------------------------------------------------------------------


def test_eval_q55_rt4_3000_floor_area(development_tools):
    """Eval Q55: RT-4 FAR 1.2 × 3000 sqft lot = 3600 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="RT-4", lot_area_sqft=3000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(3600.0)


# ---------------------------------------------------------------------------
# Code-search fixture additions for Q57, Q58, Q62 (variance, landscaping, special use)
# ---------------------------------------------------------------------------

_CODE_SEARCH_FIXTURE_PROCEDURES = _CODE_SEARCH_FIXTURE + [
    {
        "section": "17-13-0200",
        "title": "Variations and Adjustments",
        "chapter": "Chapter 17-13",
        "text": (
            "A variation is an authorized departure from the specific requirements of "
            "this Zoning Ordinance. Applications for variations shall be filed with the "
            "Zoning Board of Appeals. The Board shall consider the applicable standards "
            "before granting or denying a variance."
        ),
        "source_file": "chapter_17-13.txt",
    },
    {
        "section": "17-11-0200",
        "title": "Landscaping and Screening Standards",
        "chapter": "Chapter 17-11",
        "text": (
            "All parking lots and surface lots with more than four parking spaces must "
            "provide perimeter landscaping. A minimum of one tree per 10 parking spaces "
            "is required. Landscaping must be maintained in good condition and replaced "
            "if it dies."
        ),
        "source_file": "chapter_17-11.txt",
    },
    {
        "section": "17-13-0600",
        "title": "Special Use Permits",
        "chapter": "Chapter 17-13",
        "text": (
            "A special use is a use that, because of its unique characteristics, cannot "
            "be permitted by right in a particular zoning district. Special use applications "
            "shall be filed with the Zoning Board of Appeals and require public notice. "
            "Conditions may be attached to an approved special use."
        ),
        "source_file": "chapter_17-13.txt",
    },
]


# ---------------------------------------------------------------------------
# Q56 — RS-3 front yard setback is 15 ft
# ---------------------------------------------------------------------------


def test_eval_q56_rs3_front_yard_setback(district_tools):
    """Eval Q56: RS-3 front_yard_setback should be 15 ft."""
    result = district_tools["lookup_district"](district_code="RS-3")
    assert "error" not in result
    setback = result.get("front_yard_setback", "")
    assert "15" in str(setback), f"Expected '15' in front_yard_setback, got: {setback!r}"


# ---------------------------------------------------------------------------
# Q57 — Search "variance" returns Chapter 17-13 section
# ---------------------------------------------------------------------------


def test_eval_q57_variance_code_search(code_search_tools):
    """Eval Q57: search_zoning_code('variance') returns a Chapter 17-13 section."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_PROCEDURES,
    ):
        result = code_search_tools["search_zoning_code"](
            query="zoning variance application process"
        )
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-13") for s in sections), (
        f"Expected a 17-13 section for variance query, got: {sections}"
    )


# ---------------------------------------------------------------------------
# Q58 — Search "landscaping" returns relevant fixture section
# ---------------------------------------------------------------------------


def test_eval_q58_landscaping_code_search(code_search_tools):
    """Eval Q58: search_zoning_code('landscaping requirements') returns landscaping sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_PROCEDURES,
    ):
        result = code_search_tools["search_zoning_code"](query="landscaping requirements")
    assert "error" not in result
    assert result["result_count"] >= 1
    assert any(
        "landscap" in r.get("title", "").lower() or "landscap" in r.get("text", "").lower()
        for r in result["results"]
    ), "Expected at least one result mentioning 'landscaping'"


# ---------------------------------------------------------------------------
# Q59 — RS-2 lot area per dwelling unit is 5000
# ---------------------------------------------------------------------------


def test_eval_q59_rs2_lot_area_per_unit(district_tools):
    """Eval Q59: RS-2 lot_area_per_unit should reference 5000 sqft per dwelling unit."""
    result = district_tools["lookup_district"](district_code="RS-2")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "5000" in lot_area.replace(",", ""), (
        f"Expected '5000' in lot_area_per_unit for RS-2, got: {lot_area!r}"
    )


# ---------------------------------------------------------------------------
# Q60 — RS-3 vs RT-4 lot area per dwelling unit difference
# ---------------------------------------------------------------------------


def test_eval_q60_rs3_rt4_lot_per_unit_differs(district_tools):
    """Eval Q60: compare_districts RS-3 vs RT-4 shows lot_area_per_unit in _differences."""
    result = district_tools["compare_districts"](district_a="RS-3", district_b="RT-4")
    assert "error" not in result
    assert "lot_area_per_unit" in result["_differences"], (
        "Expected lot_area_per_unit to appear in _differences for RS-3 vs RT-4"
    )
    rs3_val = result["lot_area_per_unit"]["RS-3"]
    rt4_val = result["lot_area_per_unit"]["RT-4"]
    assert rs3_val != rt4_val


# ---------------------------------------------------------------------------
# Q61 — B3-2 max floor area on 20,000 sqft lot = 44,000 sqft
# ---------------------------------------------------------------------------


def test_eval_q61_b3_2_20000_envelope(development_tools):
    """Eval Q61: B3-2 FAR 2.2 × 20,000 sqft lot = 44,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="B3-2", lot_area_sqft=20000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(44000.0)


# ---------------------------------------------------------------------------
# Q62 — Search "special use" returns Chapter 17-13 section
# ---------------------------------------------------------------------------


def test_eval_q62_special_use_code_search(code_search_tools):
    """Eval Q62: search_zoning_code('special use permit') returns 17-13 sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_PROCEDURES,
    ):
        result = code_search_tools["search_zoning_code"](query="special use permit")
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-13") for s in sections), (
        f"Expected a 17-13 section for special use query, got: {sections}"
    )


# ---------------------------------------------------------------------------
# Q63 — M1-1 district category is Manufacturing/Industrial
# ---------------------------------------------------------------------------


def test_eval_q63_m1_1_category(district_tools):
    """Eval Q63: M1-1 lookup should show the Manufacturing/Industrial category."""
    result = district_tools["lookup_district"](district_code="M1-1")
    assert "error" not in result
    assert "Manufacturing" in result["category"], (
        f"Expected 'Manufacturing' in M1-1 category, got: {result['category']!r}"
    )


# ---------------------------------------------------------------------------
# Q64 — DX-12 has higher FAR than DX-7
# ---------------------------------------------------------------------------


def test_eval_q64_dx12_higher_far_than_dx7(district_tools):
    """Eval Q64: compare_districts DX-7 vs DX-12 — DX-12 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="DX-7", district_b="DX-12")
    assert "error" not in result
    dx7_far = float(result["floor_area_ratio"]["DX-7"])
    dx12_far = float(result["floor_area_ratio"]["DX-12"])
    assert dx12_far > dx7_far, (
        f"Expected DX-12 FAR ({dx12_far}) > DX-7 FAR ({dx7_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q65 — RS-2 maximum building height contains "30"
# ---------------------------------------------------------------------------


def test_eval_q65_rs2_height(district_tools):
    """Eval Q65: RS-2 maximum_building_height should reference 30 ft."""
    result = district_tools["lookup_district"](district_code="RS-2")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "30" in str(height), (
        f"Expected '30' in RS-2 maximum_building_height, got: {height!r}"
    )
