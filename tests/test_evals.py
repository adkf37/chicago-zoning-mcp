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


# ---------------------------------------------------------------------------
# Q66 — RS-1 FAR is 0.5
# ---------------------------------------------------------------------------


def test_eval_q66_rs1_far(district_tools):
    """Eval Q66: RS-1 FAR should be 0.5."""
    result = district_tools["lookup_district"](district_code="RS-1")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Q67 — RM-6 category is Residential
# ---------------------------------------------------------------------------


def test_eval_q67_rm6_category(district_tools):
    """Eval Q67: RM-6 should be in the Residential category."""
    result = district_tools["lookup_district"](district_code="RM-6")
    assert "error" not in result
    assert "Residential" in result["category"]


# ---------------------------------------------------------------------------
# Q68 — RM-6 max floor area on 5000 sqft = 22000 (FAR 4.4)
# ---------------------------------------------------------------------------


def test_eval_q68_rm6_5000_envelope(development_tools):
    """Eval Q68: RM-6 FAR 4.4 × 5000 sqft lot = 22,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="RM-6", lot_area_sqft=5000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(22000.0)


# ---------------------------------------------------------------------------
# Q69 — DR-7 category is Downtown Residential
# ---------------------------------------------------------------------------


def test_eval_q69_dr7_category(district_tools):
    """Eval Q69: DR-7 should be in the Downtown Residential category."""
    result = district_tools["lookup_district"](district_code="DR-7")
    assert "error" not in result
    assert "Downtown" in result["category"], (
        f"Expected 'Downtown' in DR-7 category, got: {result['category']!r}"
    )


# ---------------------------------------------------------------------------
# Q70 — M1-3 has higher FAR than M1-1
# ---------------------------------------------------------------------------


def test_eval_q70_m1_3_higher_far_than_m1_1(district_tools):
    """Eval Q70: compare_districts M1-1 vs M1-3 — M1-3 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="M1-1", district_b="M1-3")
    assert "error" not in result
    m1_1_far = float(result["floor_area_ratio"]["M1-1"])
    m1_3_far = float(result["floor_area_ratio"]["M1-3"])
    assert m1_3_far > m1_1_far, (
        f"Expected M1-3 FAR ({m1_3_far}) > M1-1 FAR ({m1_1_far})"
    )


# ---------------------------------------------------------------------------
# Q71 — POS-2 max floor area on 10000 sqft = 500 (FAR 0.05)
# ---------------------------------------------------------------------------


def test_eval_q71_pos2_10000_envelope(development_tools):
    """Eval Q71: POS-2 FAR 0.05 × 10,000 sqft lot = 500 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="POS-2", lot_area_sqft=10000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(500.0)


# ---------------------------------------------------------------------------
# Q72 — list_district_types filtering by Manufacturing returns M1-1
# ---------------------------------------------------------------------------


def test_eval_q72_list_manufacturing_districts(district_tools):
    """Eval Q72: list_district_types('Manufacturing') should include M1-1."""
    result = district_tools["list_district_types"](category="Manufacturing")
    assert isinstance(result, list)
    assert len(result) > 0
    district_codes = [d["district_type_code"] for d in result]
    assert "M1-1" in district_codes, (
        f"Expected M1-1 in manufacturing districts, got: {district_codes}"
    )


# ---------------------------------------------------------------------------
# Q73 — RT-3.5 max units on 8250 sqft = 5 (8250 / 1650)
# ---------------------------------------------------------------------------


def test_eval_q73_rt3_5_units_8250(development_tools):
    """Eval Q73: RT-3.5 on 8250 sqft lot → 5 max dwelling units (8250 / 1650)."""
    result = development_tools["calculate_development_envelope"](
        district_code="RT-3.5", lot_area_sqft=8250
    )
    assert "error" not in result
    assert result["max_dwelling_units"] == 5


# ---------------------------------------------------------------------------
# Q74 — RM-5.5 max floor area on 8000 sqft = 20000 (FAR 2.5)
# ---------------------------------------------------------------------------


def test_eval_q74_rm5_5_8000_envelope(development_tools):
    """Eval Q74: RM-5.5 FAR 2.5 × 8000 sqft lot = 20,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="RM-5.5", lot_area_sqft=8000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(20000.0)


# ---------------------------------------------------------------------------
# Q75 — search "setback requirements" returns Title 17 sections
# ---------------------------------------------------------------------------

_CODE_SEARCH_FIXTURE_SETBACKS = _CODE_SEARCH_FIXTURE + [
    {
        "section": "17-2-0400",
        "title": "Setback Requirements",
        "chapter": "Chapter 17-2",
        "text": (
            "All buildings and structures must observe minimum front, side, and rear "
            "setbacks as specified by the applicable district standards. Setbacks are "
            "measured from the lot line to the nearest wall of the structure."
        ),
        "source_file": "chapter_17-2.txt",
    },
]


def test_eval_q75_setback_requirements_code_search(code_search_tools):
    """Eval Q75: search_zoning_code('setback requirements') returns Title 17 sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_SETBACKS,
    ):
        result = code_search_tools["search_zoning_code"](
            query="building setback requirements"
        )
    assert "error" not in result
    assert result["result_count"] >= 1
    for section in result["results"]:
        assert section["section"].startswith("17-")


# ---------------------------------------------------------------------------
# Q76 — DS-3 maximum building height contains 50
# ---------------------------------------------------------------------------


def test_eval_q76_ds3_height(district_tools):
    """Eval Q76: DS-3 maximum_building_height should reference 50 ft."""
    result = district_tools["lookup_district"](district_code="DS-3")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "50" in str(height), (
        f"Expected '50' in DS-3 maximum_building_height, got: {height!r}"
    )


# ---------------------------------------------------------------------------
# Q77 — B2-3 max floor area on 5000 sqft = 15000 (FAR 3.0)
# ---------------------------------------------------------------------------


def test_eval_q77_b2_3_5000_envelope(development_tools):
    """Eval Q77: B2-3 FAR 3.0 × 5000 sqft lot = 15,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="B2-3", lot_area_sqft=5000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(15000.0)


# ---------------------------------------------------------------------------
# Q78 — C1-5 max floor area on 2000 sqft = 10000 (FAR 5.0)
# ---------------------------------------------------------------------------


def test_eval_q78_c1_5_2000_envelope(development_tools):
    """Eval Q78: C1-5 FAR 5.0 × 2000 sqft lot = 10,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="C1-5", lot_area_sqft=2000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(10000.0)


# ---------------------------------------------------------------------------
# Q79 — DX-12 has higher FAR than DX-5
# ---------------------------------------------------------------------------


def test_eval_q79_dx12_higher_far_than_dx5(district_tools):
    """Eval Q79: compare_districts DX-5 vs DX-12 — DX-12 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="DX-5", district_b="DX-12")
    assert "error" not in result
    dx5_far = float(result["floor_area_ratio"]["DX-5"])
    dx12_far = float(result["floor_area_ratio"]["DX-12"])
    assert dx12_far > dx5_far, (
        f"Expected DX-12 FAR ({dx12_far}) > DX-5 FAR ({dx5_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q80 — search "inclusionary zoning" returns Title 17 sections
# ---------------------------------------------------------------------------

_CODE_SEARCH_FIXTURE_INCLUSIONARY = _CODE_SEARCH_FIXTURE_EXTENDED + [
    {
        "section": "17-4-1000",
        "title": "Affordable Housing and Inclusionary Zoning",
        "chapter": "Chapter 17-4",
        "text": (
            "Inclusionary zoning requirements apply to residential developments that "
            "receive city financial assistance or involve a zoning map amendment. "
            "Developers must provide a specified percentage of affordable housing units "
            "or make an in-lieu payment to the Affordable Housing Opportunity Fund."
        ),
        "source_file": "chapter_17-4.txt",
    },
]


def test_eval_q80_inclusionary_zoning_code_search(code_search_tools):
    """Eval Q80: search for 'inclusionary zoning' returns Title 17 sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_INCLUSIONARY,
    ):
        result = code_search_tools["search_zoning_code"](
            query="inclusionary zoning affordable housing requirements"
        )
    assert "error" not in result
    assert result["result_count"] >= 1
    for section in result["results"]:
        assert section["section"].startswith("17-")


# ---------------------------------------------------------------------------
# Q81 — RM-4.5 FAR is 1.5
# ---------------------------------------------------------------------------


def test_eval_q81_rm4_5_far(district_tools):
    """Eval Q81: RM-4.5 FAR should be 1.5."""
    result = district_tools["lookup_district"](district_code="RM-4.5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# Q82 — RM-6.5 FAR is 6.6
# ---------------------------------------------------------------------------


def test_eval_q82_rm6_5_far(district_tools):
    """Eval Q82: RM-6.5 FAR should be 6.6."""
    result = district_tools["lookup_district"](district_code="RM-6.5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(6.6)


# ---------------------------------------------------------------------------
# Q83 — B1-5 max building height contains 65
# ---------------------------------------------------------------------------


def test_eval_q83_b1_5_height(district_tools):
    """Eval Q83: B1-5 maximum building height should reference 65 ft."""
    result = district_tools["lookup_district"](district_code="B1-5")
    assert "error" not in result
    assert "65" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q84 — C2-3 4000 sqft lot → 12000 sqft max floor area
# ---------------------------------------------------------------------------


def test_eval_q84_c2_3_4000_envelope(development_tools):
    """Eval Q84: 4000 sqft C2-3 lot → 12,000 sqft max floor area (FAR 3.0)."""
    result = development_tools["calculate_development_envelope"](
        district_code="C2-3", lot_area_sqft=4000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(12000.0)


# ---------------------------------------------------------------------------
# Q85 — M2-2 category is Manufacturing/Industrial
# ---------------------------------------------------------------------------


def test_eval_q85_m2_2_category(district_tools):
    """Eval Q85: M2-2 should be in the Manufacturing/Industrial category."""
    result = district_tools["lookup_district"](district_code="M2-2")
    assert "error" not in result
    assert "Manufacturing" in result["category"]


# ---------------------------------------------------------------------------
# Q86 — M2-3 has higher FAR than M2-1
# ---------------------------------------------------------------------------


def test_eval_q86_m2_3_higher_far_than_m2_1(district_tools):
    """Eval Q86: compare_districts M2-1 vs M2-3 — M2-3 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="M2-1", district_b="M2-3")
    assert "error" not in result
    m2_1_far = float(result["floor_area_ratio"]["M2-1"])
    m2_3_far = float(result["floor_area_ratio"]["M2-3"])
    assert m2_3_far > m2_1_far, (
        f"Expected M2-3 FAR ({m2_3_far}) > M2-1 FAR ({m2_1_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q87 — DX-3 5000 sqft lot → 10 dwelling units
# ---------------------------------------------------------------------------


def test_eval_q87_dx3_5000_units(development_tools):
    """Eval Q87: 5000 sqft DX-3 lot → 10 max dwelling units (5000 / 500)."""
    result = development_tools["calculate_development_envelope"](
        district_code="DX-3", lot_area_sqft=5000
    )
    assert "error" not in result
    assert result["max_dwelling_units"] == 10


# ---------------------------------------------------------------------------
# Q88 — DR-3 category is Downtown Residential
# ---------------------------------------------------------------------------


def test_eval_q88_dr3_category(district_tools):
    """Eval Q88: DR-3 should be in the Downtown Residential category."""
    result = district_tools["lookup_district"](district_code="DR-3")
    assert "error" not in result
    assert "Downtown" in result["category"]


# ---------------------------------------------------------------------------
# Q89 — DS-5 FAR is 5.0
# ---------------------------------------------------------------------------


def test_eval_q89_ds5_far(district_tools):
    """Eval Q89: DS-5 FAR should be 5.0."""
    result = district_tools["lookup_district"](district_code="DS-5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Q90 — POS-1 category is Parks and Open Space
# ---------------------------------------------------------------------------


def test_eval_q90_pos1_category(district_tools):
    """Eval Q90: POS-1 should be in the Parks and Open Space category."""
    result = district_tools["lookup_district"](district_code="POS-1")
    assert "error" not in result
    assert "Parks" in result["category"]


# ---------------------------------------------------------------------------
# Q91 — RM-5 has higher FAR than RM-4.5
# ---------------------------------------------------------------------------


def test_eval_q91_rm5_higher_far_than_rm4_5(district_tools):
    """Eval Q91: compare_districts RM-4.5 vs RM-5 — RM-5 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="RM-4.5", district_b="RM-5")
    assert "error" not in result
    rm4_5_far = float(result["floor_area_ratio"]["RM-4.5"])
    rm5_far = float(result["floor_area_ratio"]["RM-5"])
    assert rm5_far > rm4_5_far, (
        f"Expected RM-5 FAR ({rm5_far}) > RM-4.5 FAR ({rm4_5_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q92 — DR-10 has higher FAR than DR-3
# ---------------------------------------------------------------------------


def test_eval_q92_dr10_higher_far_than_dr3(district_tools):
    """Eval Q92: compare_districts DR-3 vs DR-10 — DR-10 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="DR-3", district_b="DR-10")
    assert "error" not in result
    dr3_far = float(result["floor_area_ratio"]["DR-3"])
    dr10_far = float(result["floor_area_ratio"]["DR-10"])
    assert dr10_far > dr3_far, (
        f"Expected DR-10 FAR ({dr10_far}) > DR-3 FAR ({dr3_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q93 — C3-2 3000 sqft lot → 6600 sqft max floor area
# ---------------------------------------------------------------------------


def test_eval_q93_c3_2_3000_envelope(development_tools):
    """Eval Q93: 3000 sqft C3-2 lot → 6,600 sqft max floor area (FAR 2.2)."""
    result = development_tools["calculate_development_envelope"](
        district_code="C3-2", lot_area_sqft=3000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(6600.0)


# ---------------------------------------------------------------------------
# Q94 — Commercial districts list includes C1-series
# ---------------------------------------------------------------------------


def test_eval_q94_commercial_districts_list(district_tools):
    """Eval Q94: list_district_types with 'Commercial' should include C1-series."""
    result = district_tools["list_district_types"](category="Commercial")
    assert isinstance(result, list), f"Expected list, got {type(result)}"
    codes = [d["district_type_code"] for d in result]
    assert any(c.startswith("C1") for c in codes), (
        f"Expected C1-series districts in Commercial list, got: {codes}"
    )


# ---------------------------------------------------------------------------
# Q95 — RM-5.5 lot area per dwelling unit contains 400
# ---------------------------------------------------------------------------


def test_eval_q95_rm5_5_lot_area_per_unit(district_tools):
    """Eval Q95: RM-5.5 lot_area_per_unit should reference 400 sqft per unit."""
    result = district_tools["lookup_district"](district_code="RM-5.5")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "400" in lot_area.replace(",", ""), (
        f"Expected 400 in lot_area_per_unit, got: {lot_area!r}"
    )


# ---------------------------------------------------------------------------
# Q96 — B2-5 max building height contains 65
# ---------------------------------------------------------------------------


def test_eval_q96_b2_5_height(district_tools):
    """Eval Q96: B2-5 maximum building height should reference 65 ft."""
    result = district_tools["lookup_district"](district_code="B2-5")
    assert "error" not in result
    assert "65" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q97 — M2-3 FAR is 3.0
# ---------------------------------------------------------------------------


def test_eval_q97_m2_3_far(district_tools):
    """Eval Q97: M2-3 FAR should be 3.0."""
    result = district_tools["lookup_district"](district_code="M2-3")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Q98 — DR-5 category is Downtown Residential
# ---------------------------------------------------------------------------


def test_eval_q98_dr5_category(district_tools):
    """Eval Q98: DR-5 should be in the Downtown Residential category."""
    result = district_tools["lookup_district"](district_code="DR-5")
    assert "error" not in result
    assert "Downtown" in result["category"]


# ---------------------------------------------------------------------------
# Q99 — DS-5 has higher FAR than DS-3
# ---------------------------------------------------------------------------


def test_eval_q99_ds5_higher_far_than_ds3(district_tools):
    """Eval Q99: compare_districts DS-3 vs DS-5 — DS-5 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="DS-3", district_b="DS-5")
    assert "error" not in result
    ds3_far = float(result["floor_area_ratio"]["DS-3"])
    ds5_far = float(result["floor_area_ratio"]["DS-5"])
    assert ds5_far > ds3_far, (
        f"Expected DS-5 FAR ({ds5_far}) > DS-3 FAR ({ds3_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q100 — list Downtown Mixed-Use districts includes DX-7
# ---------------------------------------------------------------------------


def test_eval_q100_list_downtown_districts(district_tools):
    """Eval Q100: list_district_types with 'Downtown Mixed-Use' should include DX-7."""
    result = district_tools["list_district_types"](category="Downtown Mixed-Use")
    assert isinstance(result, list), f"Expected list, got {type(result)}"
    codes = [d["district_type_code"] for d in result]
    assert "DX-7" in codes, f"Expected DX-7 in Downtown Mixed-Use list, got: {codes}"


# ---------------------------------------------------------------------------
# Q101 — DC-12 FAR is 12.0
# ---------------------------------------------------------------------------


def test_eval_q101_dc12_far(district_tools):
    """Eval Q101: DC-12 FAR should be 12.0."""
    result = district_tools["lookup_district"](district_code="DC-12")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(12.0)


# ---------------------------------------------------------------------------
# Q102 — DR-10 category is Downtown Residential
# ---------------------------------------------------------------------------


def test_eval_q102_dr10_category(district_tools):
    """Eval Q102: DR-10 category should contain 'Downtown'."""
    result = district_tools["lookup_district"](district_code="DR-10")
    assert "error" not in result
    assert "Downtown" in result["category"]


# ---------------------------------------------------------------------------
# Q103 — DX-16 max floor area on 2000 sqft lot = 32000
# ---------------------------------------------------------------------------


def test_eval_q103_dx16_2000_envelope(development_tools):
    """Eval Q103: DX-16 FAR 16.0 × 2000 sqft lot = 32,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="DX-16", lot_area_sqft=2000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(32000.0)


# ---------------------------------------------------------------------------
# Q104 — DC-16 has higher FAR than DC-12
# ---------------------------------------------------------------------------


def test_eval_q104_dc16_higher_far_than_dc12(district_tools):
    """Eval Q104: compare_districts DC-12 vs DC-16 — DC-16 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="DC-12", district_b="DC-16")
    assert "error" not in result
    dc12_far = float(result["floor_area_ratio"]["DC-12"])
    dc16_far = float(result["floor_area_ratio"]["DC-16"])
    assert dc16_far > dc12_far, f"Expected DC-16 FAR ({dc16_far}) > DC-12 FAR ({dc12_far})"
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q105 — M3-3 FAR is 3.0
# ---------------------------------------------------------------------------


def test_eval_q105_m3_3_far(district_tools):
    """Eval Q105: M3-3 heavy manufacturing FAR should be 3.0."""
    result = district_tools["lookup_district"](district_code="M3-3")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Q106 — B1-1.5 height limit contains "35"
# ---------------------------------------------------------------------------


def test_eval_q106_b1_1_5_height(district_tools):
    """Eval Q106: B1-1.5 maximum building height should mention 35 ft."""
    result = district_tools["lookup_district"](district_code="B1-1.5")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "35" in str(height), f"Expected '35' in height '{height}'"


# ---------------------------------------------------------------------------
# Q107 — C1-2 max floor area on 3000 sqft lot = 6600
# ---------------------------------------------------------------------------


def test_eval_q107_c1_2_3000_envelope(development_tools):
    """Eval Q107: C1-2 FAR 2.2 × 3000 sqft lot = 6,600 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="C1-2", lot_area_sqft=3000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(6600.0)


# ---------------------------------------------------------------------------
# Q108 — M1-2 FAR is 2.2
# ---------------------------------------------------------------------------


def test_eval_q108_m1_2_far(district_tools):
    """Eval Q108: M1-2 limited manufacturing FAR should be 2.2."""
    result = district_tools["lookup_district"](district_code="M1-2")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(2.2)


# ---------------------------------------------------------------------------
# Q109 — DR-10 has higher FAR than DR-7
# ---------------------------------------------------------------------------


def test_eval_q109_dr10_higher_far_than_dr7(district_tools):
    """Eval Q109: compare_districts DR-7 vs DR-10 — DR-10 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="DR-7", district_b="DR-10")
    assert "error" not in result
    dr7_far = float(result["floor_area_ratio"]["DR-7"])
    dr10_far = float(result["floor_area_ratio"]["DR-10"])
    assert dr10_far > dr7_far, f"Expected DR-10 FAR ({dr10_far}) > DR-7 FAR ({dr7_far})"


# ---------------------------------------------------------------------------
# Q110 — list_district_types("Residential") includes RT-4
# ---------------------------------------------------------------------------


def test_eval_q110_list_residential_includes_rt4(district_tools):
    """Eval Q110: list_district_types('Residential') should include RT-4."""
    result = district_tools["list_district_types"](category="Residential")
    assert isinstance(result, list)
    codes = [d["district_type_code"] for d in result]
    assert "RT-4" in codes, f"Expected RT-4 in Residential list, got: {codes}"


# ---------------------------------------------------------------------------
# Q111 — B3-3 max floor area on 4000 sqft lot = 12000
# ---------------------------------------------------------------------------


def test_eval_q111_b3_3_4000_envelope(development_tools):
    """Eval Q111: B3-3 FAR 3.0 × 4000 sqft lot = 12,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="B3-3", lot_area_sqft=4000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(12000.0)


# ---------------------------------------------------------------------------
# Q112 — RM-6.5 lot area per unit contains "145"
# ---------------------------------------------------------------------------


def test_eval_q112_rm6_5_lot_area_per_unit(district_tools):
    """Eval Q112: RM-6.5 lot_area_per_unit should reference 145 sqft."""
    result = district_tools["lookup_district"](district_code="RM-6.5")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "145" in str(lot_area).replace(",", ""), (
        f"Expected '145' in lot_area_per_unit '{lot_area}'"
    )


# ---------------------------------------------------------------------------
# Q113 — RM-6.5 has higher FAR than RM-6
# ---------------------------------------------------------------------------


def test_eval_q113_rm6_5_higher_far_than_rm6(district_tools):
    """Eval Q113: compare_districts RM-6 vs RM-6.5 — RM-6.5 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="RM-6", district_b="RM-6.5")
    assert "error" not in result
    rm6_far = float(result["floor_area_ratio"]["RM-6"])
    rm6_5_far = float(result["floor_area_ratio"]["RM-6.5"])
    assert rm6_5_far > rm6_far, f"Expected RM-6.5 FAR ({rm6_5_far}) > RM-6 FAR ({rm6_far})"


# ---------------------------------------------------------------------------
# Q114 — list_district_types("Downtown Service") includes DS-3
# ---------------------------------------------------------------------------


def test_eval_q114_list_downtown_service_includes_ds3(district_tools):
    """Eval Q114: list_district_types('Downtown Service') should include DS-3."""
    result = district_tools["list_district_types"](category="Downtown Service")
    assert isinstance(result, list)
    codes = [d["district_type_code"] for d in result]
    assert "DS-3" in codes, f"Expected DS-3 in Downtown Service list, got: {codes}"


# ---------------------------------------------------------------------------
# Q115 — DX-7 has higher FAR than DX-3
# ---------------------------------------------------------------------------


def test_eval_q115_dx7_higher_far_than_dx3(district_tools):
    """Eval Q115: compare_districts DX-3 vs DX-7 — DX-7 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="DX-3", district_b="DX-7")
    assert "error" not in result
    dx3_far = float(result["floor_area_ratio"]["DX-3"])
    dx7_far = float(result["floor_area_ratio"]["DX-7"])
    assert dx7_far > dx3_far, f"Expected DX-7 FAR ({dx7_far}) > DX-3 FAR ({dx3_far})"


# ---------------------------------------------------------------------------
# Q116 — C2-2 height limit contains "38"
# ---------------------------------------------------------------------------


def test_eval_q116_c2_2_height(district_tools):
    """Eval Q116: C2-2 maximum building height should mention 38 ft."""
    result = district_tools["lookup_district"](district_code="C2-2")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "38" in str(height), f"Expected '38' in height '{height}'"


# ---------------------------------------------------------------------------
# Q117 — B2-1 FAR is 1.0
# ---------------------------------------------------------------------------


def test_eval_q117_b2_1_far(district_tools):
    """Eval Q117: B2-1 neighborhood mixed-use FAR should be 1.0."""
    result = district_tools["lookup_district"](district_code="B2-1")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Q118 — C3-1 category is Commercial
# ---------------------------------------------------------------------------


def test_eval_q118_c3_1_category(district_tools):
    """Eval Q118: C3-1 commercial manufacturing category should contain 'Commercial'."""
    result = district_tools["lookup_district"](district_code="C3-1")
    assert "error" not in result
    assert "Commercial" in result["category"], (
        f"Expected 'Commercial' in category '{result['category']}'"
    )


# ---------------------------------------------------------------------------
# Q119 — B3-5 max floor area on 5000 sqft lot = 25000
# ---------------------------------------------------------------------------


def test_eval_q119_b3_5_5000_envelope(development_tools):
    """Eval Q119: B3-5 FAR 5.0 × 5000 sqft lot = 25,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="B3-5", lot_area_sqft=5000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(25000.0)


# ---------------------------------------------------------------------------
# Q120 — RS-3 on 0.5 acre lot → 19602 sqft max floor area (acre routing)
# ---------------------------------------------------------------------------


def test_eval_q120_rs3_half_acre_envelope(development_tools):
    """Eval Q120: RS-3 FAR 0.9 × 0.5 acre (21780 sqft) = 19,602 sqft max floor area."""
    from web.gemini_client import GeminiZoningClient

    # 0.5 acres converted to sqft using the canonical constant
    lot_sqft = 0.5 * GeminiZoningClient.SQFT_PER_ACRE  # 21780.0
    result = development_tools["calculate_development_envelope"](
        district_code="RS-3", lot_area_sqft=lot_sqft
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(19602.0)


# ===========================================================================
# Q121–Q140: Zoning code text searches, address patterns, and new districts
# ===========================================================================

# Additional code search fixture entries for Q121-Q140

_CODE_SEARCH_FIXTURE_Q121 = _CODE_SEARCH_FIXTURE + [
    {
        "section": "17-4-0600",
        "title": "Home Occupation Standards",
        "chapter": "Chapter 17-4",
        "text": (
            "A home occupation is a business activity conducted in a dwelling unit by "
            "a resident of that unit. Home occupations are accessory uses subject to "
            "the following standards: no exterior sign larger than one square foot; "
            "no non-resident employees on the premises; no retail sales."
        ),
        "source_file": "chapter_17-4.txt",
    },
    {
        "section": "17-12-0200",
        "title": "Sign Regulations — Commercial Districts",
        "chapter": "Chapter 17-12",
        "text": (
            "In commercial and business districts, ground signs and wall signs are "
            "permitted subject to size limits. Sign area may not exceed 1.5 times the "
            "street frontage in square feet. Electronic message signs must comply with "
            "illumination and animation restrictions."
        ),
        "source_file": "chapter_17-12.txt",
    },
    {
        "section": "17-2-0100",
        "title": "Floor Area Ratio Definitions",
        "chapter": "Chapter 17-2",
        "text": (
            "Floor area ratio (FAR) is the ratio of the total gross floor area of all "
            "buildings on a lot to the total area of that lot. Gross floor area means "
            "the sum of the horizontal areas of each floor of a building measured from "
            "the exterior faces of the exterior walls."
        ),
        "source_file": "chapter_17-2.txt",
    },
]


# ---------------------------------------------------------------------------
# Q121 — get_zoning_section("17-3-0102") returns ADU text
# ---------------------------------------------------------------------------


def test_eval_q121_get_section_17_3_0102(code_search_tools):
    """Eval Q121: get_zoning_section('17-3-0102') returns accessory dwelling unit text."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["get_zoning_section"](section_number="17-3-0102")
    assert "error" not in result
    assert result["section"] == "17-3-0102"
    assert (
        "accessory" in result["title"].lower()
        or "accessory" in result["text"].lower()
    )


# ---------------------------------------------------------------------------
# Q122 — search "home occupation" returns relevant Title 17 section
# ---------------------------------------------------------------------------


def test_eval_q122_search_home_occupation(code_search_tools):
    """Eval Q122: search_zoning_code('home occupation') returns a Title 17 section."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_Q121,
    ):
        result = code_search_tools["search_zoning_code"](query="home occupation standards")
    assert "error" not in result
    assert result["result_count"] >= 1
    for section in result["results"]:
        assert section["section"].startswith("17-")
    assert any(
        "home" in r.get("title", "").lower() or "home" in r.get("text", "").lower()
        for r in result["results"]
    )


# ---------------------------------------------------------------------------
# Q123 — get_zoning_section("17-1-0101") returns Chicago Zoning Ordinance title
# ---------------------------------------------------------------------------


def test_eval_q123_get_section_17_1_0101(code_search_tools):
    """Eval Q123: get_zoning_section('17-1-0101') returns the ordinance title text."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["get_zoning_section"](section_number="17-1-0101")
    assert "error" not in result
    assert result["section"] == "17-1-0101"
    assert (
        "chicago zoning ordinance" in result["text"].lower()
        or "chicago" in result["text"].lower()
    )


# ---------------------------------------------------------------------------
# Q124 — search "sign regulations" returns a Chapter 17-12 section
# ---------------------------------------------------------------------------


def test_eval_q124_search_sign_regulations(code_search_tools):
    """Eval Q124: search_zoning_code('sign regulations') returns sign-related sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_Q121,
    ):
        result = code_search_tools["search_zoning_code"](
            query="sign regulations commercial districts"
        )
    assert "error" not in result
    assert result["result_count"] >= 1
    assert any(
        "sign" in r.get("title", "").lower() or "sign" in r.get("text", "").lower()
        for r in result["results"]
    )


# ---------------------------------------------------------------------------
# Q125 — DX-5 FAR is 5.0
# ---------------------------------------------------------------------------


def test_eval_q125_dx5_far(district_tools):
    """Eval Q125: DX-5 FAR should be 5.0."""
    result = district_tools["lookup_district"](district_code="DX-5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Q126 — RS-3 rear yard setback contains "28"
# ---------------------------------------------------------------------------


def test_eval_q126_rs3_rear_yard_setback(district_tools):
    """Eval Q126: RS-3 rear_yard_setback should reference 28 ft."""
    result = district_tools["lookup_district"](district_code="RS-3")
    assert "error" not in result
    setback = result.get("rear_yard_setback", "")
    assert "28" in str(setback), f"Expected '28' in rear_yard_setback, got: {setback!r}"


# ---------------------------------------------------------------------------
# Q127 — B2-2 category contains "Neighborhood Mixed-Use" or "Mixed-Use"
# ---------------------------------------------------------------------------


def test_eval_q127_b2_2_category(district_tools):
    """Eval Q127: B2-2 category should be Business/Shopping."""
    result = district_tools["lookup_district"](district_code="B2-2")
    assert "error" not in result
    cat = result.get("category", "")
    assert "Business" in cat, (
        f"Expected 'Business' in B2-2 category, got: {cat!r}"
    )


# ---------------------------------------------------------------------------
# Q128 — C1-1 max floor area on 4000 sqft lot = 4000 (FAR 1.0)
# ---------------------------------------------------------------------------


def test_eval_q128_c1_1_4000_envelope(development_tools):
    """Eval Q128: C1-1 FAR 1.0 × 4000 sqft lot = 4,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="C1-1", lot_area_sqft=4000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(4000.0)


# ---------------------------------------------------------------------------
# Q129 — C3-5 has higher FAR than C3-2
# ---------------------------------------------------------------------------


def test_eval_q129_c3_5_higher_far_than_c3_2(district_tools):
    """Eval Q129: compare_districts C3-2 vs C3-5 — C3-5 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="C3-2", district_b="C3-5")
    assert "error" not in result
    c3_2_far = float(result["floor_area_ratio"]["C3-2"])
    c3_5_far = float(result["floor_area_ratio"]["C3-5"])
    assert c3_5_far > c3_2_far, (
        f"Expected C3-5 FAR ({c3_5_far}) > C3-2 FAR ({c3_2_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q130 — M1-3 maximum building height contains "55"
# ---------------------------------------------------------------------------


def test_eval_q130_m1_3_height(district_tools):
    """Eval Q130: M1-3 maximum_building_height should mention 55 ft."""
    result = district_tools["lookup_district"](district_code="M1-3")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "55" in str(height), f"Expected '55' in M1-3 height, got: {height!r}"


# ---------------------------------------------------------------------------
# Q131 — list Business/Shopping districts includes B1-1
# ---------------------------------------------------------------------------


def test_eval_q131_list_business_districts(district_tools):
    """Eval Q131: list_district_types('Business/Shopping') should include B1-1."""
    result = district_tools["list_district_types"](category="Business/Shopping")
    assert isinstance(result, list)
    codes = [d["district_type_code"] for d in result]
    assert "B1-1" in codes, f"Expected B1-1 in Business/Shopping list, got: {codes}"


# ---------------------------------------------------------------------------
# Q132 — DX-12 max floor area on 1500 sqft lot = 18000
# ---------------------------------------------------------------------------


def test_eval_q132_dx12_1500_envelope(development_tools):
    """Eval Q132: DX-12 FAR 12.0 × 1500 sqft lot = 18,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="DX-12", lot_area_sqft=1500
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(18000.0)


# ---------------------------------------------------------------------------
# Q133 — list Parks and Open Space districts includes POS-1
# ---------------------------------------------------------------------------


def test_eval_q133_list_parks_districts(district_tools):
    """Eval Q133: list_district_types('Parks and Open Space') should include POS-1."""
    result = district_tools["list_district_types"](category="Parks and Open Space")
    assert isinstance(result, list)
    codes = [d["district_type_code"] for d in result]
    assert "POS-1" in codes, f"Expected POS-1 in Parks and Open Space list, got: {codes}"


# ---------------------------------------------------------------------------
# Q134 — B1-2 FAR is 2.2
# ---------------------------------------------------------------------------


def test_eval_q134_b1_2_far(district_tools):
    """Eval Q134: B1-2 neighborhood shopping FAR should be 2.2."""
    result = district_tools["lookup_district"](district_code="B1-2")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(2.2)


# ---------------------------------------------------------------------------
# Q135 — search "floor area ratio" returns a Chapter 17-2 section
# ---------------------------------------------------------------------------


def test_eval_q135_search_far_definition(code_search_tools):
    """Eval Q135: search_zoning_code('floor area ratio') returns a Chapter 17-2 section."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_Q121,
    ):
        result = code_search_tools["search_zoning_code"](query="floor area ratio definitions")
    assert "error" not in result
    assert result["result_count"] >= 1
    for section in result["results"]:
        assert section["section"].startswith("17-")
    assert any(
        "floor area" in r.get("title", "").lower() or "floor area" in r.get("text", "").lower()
        for r in result["results"]
    )


# ---------------------------------------------------------------------------
# Q136 — B1-3 has higher FAR than B1-2
# ---------------------------------------------------------------------------


def test_eval_q136_b1_3_higher_far_than_b1_2(district_tools):
    """Eval Q136: compare_districts B1-2 vs B1-3 — B1-3 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="B1-2", district_b="B1-3")
    assert "error" not in result
    b1_2_far = float(result["floor_area_ratio"]["B1-2"])
    b1_3_far = float(result["floor_area_ratio"]["B1-3"])
    assert b1_3_far > b1_2_far, (
        f"Expected B1-3 FAR ({b1_3_far}) > B1-2 FAR ({b1_2_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q137 — C2-5 max floor area on 3000 sqft lot = 15000 (FAR 5.0)
# ---------------------------------------------------------------------------


def test_eval_q137_c2_5_3000_envelope(development_tools):
    """Eval Q137: C2-5 FAR 5.0 × 3000 sqft lot = 15,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="C2-5", lot_area_sqft=3000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(15000.0)


# ---------------------------------------------------------------------------
# Q138 — C2-1 FAR is 1.0
# ---------------------------------------------------------------------------


def test_eval_q138_c2_1_far(district_tools):
    """Eval Q138: C2-1 motor vehicle commercial FAR should be 1.0."""
    result = district_tools["lookup_district"](district_code="C2-1")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Q139 — search "planned development application" returns Chapter 17-13 section
# ---------------------------------------------------------------------------


def test_eval_q139_search_planned_development(code_search_tools):
    """Eval Q139: search for 'planned development application' returns 17-13 sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["search_zoning_code"](
            query="planned development application procedures"
        )
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-13") for s in sections), (
        f"Expected a 17-13 section for planned development query, got: {sections}"
    )


# ---------------------------------------------------------------------------
# Q140 — B2-3 has higher FAR than B2-1
# ---------------------------------------------------------------------------


def test_eval_q140_b2_3_higher_far_than_b2_1(district_tools):
    """Eval Q140: compare_districts B2-1 vs B2-3 — B2-3 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="B2-1", district_b="B2-3")
    assert "error" not in result
    b2_1_far = float(result["floor_area_ratio"]["B2-1"])
    b2_3_far = float(result["floor_area_ratio"]["B2-3"])
    assert b2_3_far > b2_1_far, (
        f"Expected B2-3 FAR ({b2_3_far}) > B2-1 FAR ({b2_1_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q141 — RS-1 FAR is 0.5
# ---------------------------------------------------------------------------


def test_eval_q141_rs1_far(district_tools):
    """Eval Q141: RS-1 FAR should be 0.5."""
    result = district_tools["lookup_district"](district_code="RS-1")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Q142 — RS-2 lot area per unit contains 5000
# ---------------------------------------------------------------------------


def test_eval_q142_rs2_lot_area_per_unit(district_tools):
    """Eval Q142: RS-2 lot_area_per_unit should reference 5000 sqft per unit."""
    result = district_tools["lookup_district"](district_code="RS-2")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "5000" in lot_area.replace(",", "")


# ---------------------------------------------------------------------------
# Q143 — RT-3.5 maximum building height contains 35
# ---------------------------------------------------------------------------


def test_eval_q143_rt35_height(district_tools):
    """Eval Q143: RT-3.5 maximum building height should reference 35 ft."""
    result = district_tools["lookup_district"](district_code="RT-3.5")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "35" in str(height)


# ---------------------------------------------------------------------------
# Q144 — RM-4.5 FAR is 1.5
# ---------------------------------------------------------------------------


def test_eval_q144_rm45_far(district_tools):
    """Eval Q144: RM-4.5 FAR should be 1.5."""
    result = district_tools["lookup_district"](district_code="RM-4.5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# Q145 — RM-5 maximum building height contains 45
# ---------------------------------------------------------------------------


def test_eval_q145_rm5_height(district_tools):
    """Eval Q145: RM-5 maximum building height should reference 45 ft."""
    result = district_tools["lookup_district"](district_code="RM-5")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "45" in str(height)


# ---------------------------------------------------------------------------
# Q146 — RM-5.5 lot area per unit contains 400
# ---------------------------------------------------------------------------


def test_eval_q146_rm55_lot_area_per_unit(district_tools):
    """Eval Q146: RM-5.5 lot_area_per_unit should reference 400 sqft per unit."""
    result = district_tools["lookup_district"](district_code="RM-5.5")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "400" in lot_area.replace(",", "")


# ---------------------------------------------------------------------------
# Q147 — B1-5 development envelope on 2000 sqft lot = 10000 (FAR 5.0)
# ---------------------------------------------------------------------------


def test_eval_q147_b1_5_2000_envelope(development_tools):
    """Eval Q147: B1-5 FAR 5.0 × 2000 sqft lot = 10,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="B1-5", lot_area_sqft=2000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(10000.0)


# ---------------------------------------------------------------------------
# Q148 — B2-5 FAR is 5.0
# ---------------------------------------------------------------------------


def test_eval_q148_b2_5_far(district_tools):
    """Eval Q148: B2-5 FAR should be 5.0."""
    result = district_tools["lookup_district"](district_code="B2-5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Q149 — B3-1 is in the Business/Shopping category
# ---------------------------------------------------------------------------


def test_eval_q149_b3_1_category(district_tools):
    """Eval Q149: B3-1 should be in the Business/Shopping category."""
    result = district_tools["lookup_district"](district_code="B3-1")
    assert "error" not in result
    assert "Business" in result["category"]


# ---------------------------------------------------------------------------
# Q150 — C1-3 FAR is 3.0
# ---------------------------------------------------------------------------


def test_eval_q150_c1_3_far(district_tools):
    """Eval Q150: C1-3 FAR should be 3.0."""
    result = district_tools["lookup_district"](district_code="C1-3")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Q151 — C2-3 maximum building height contains 50
# ---------------------------------------------------------------------------


def test_eval_q151_c2_3_height(district_tools):
    """Eval Q151: C2-3 maximum building height should reference 50 ft."""
    result = district_tools["lookup_district"](district_code="C2-3")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "50" in str(height)


# ---------------------------------------------------------------------------
# Q152 — M1-1 FAR is 1.0
# ---------------------------------------------------------------------------


def test_eval_q152_m1_1_far(district_tools):
    """Eval Q152: M1-1 FAR should be 1.0."""
    result = district_tools["lookup_district"](district_code="M1-1")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Q153 — M2-1 is in the Manufacturing/Industrial category
# ---------------------------------------------------------------------------


def test_eval_q153_m2_1_category(district_tools):
    """Eval Q153: M2-1 should be in the Manufacturing/Industrial category."""
    result = district_tools["lookup_district"](district_code="M2-1")
    assert "error" not in result
    assert "Manufacturing" in result["category"]


# ---------------------------------------------------------------------------
# Q154 — M2-2 maximum building height contains 45
# ---------------------------------------------------------------------------


def test_eval_q154_m2_2_height(district_tools):
    """Eval Q154: M2-2 maximum building height should reference 45 ft."""
    result = district_tools["lookup_district"](district_code="M2-2")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "45" in str(height)


# ---------------------------------------------------------------------------
# Q155 — M2-3 development envelope on 3000 sqft lot = 9000 (FAR 3.0)
# ---------------------------------------------------------------------------


def test_eval_q155_m2_3_3000_envelope(development_tools):
    """Eval Q155: M2-3 FAR 3.0 × 3000 sqft lot = 9,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="M2-3", lot_area_sqft=3000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(9000.0)


# ---------------------------------------------------------------------------
# Q156 — DR-3 FAR is 3.0
# ---------------------------------------------------------------------------


def test_eval_q156_dr3_far(district_tools):
    """Eval Q156: DR-3 FAR should be 3.0."""
    result = district_tools["lookup_district"](district_code="DR-3")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Q157 — DR-5 development envelope on 2000 sqft lot = 10000 (FAR 5.0)
# ---------------------------------------------------------------------------


def test_eval_q157_dr5_2000_envelope(development_tools):
    """Eval Q157: DR-5 FAR 5.0 × 2000 sqft lot = 10,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="DR-5", lot_area_sqft=2000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(10000.0)


# ---------------------------------------------------------------------------
# Q158 — POS-2 FAR is 0.05
# ---------------------------------------------------------------------------


def test_eval_q158_pos2_far(district_tools):
    """Eval Q158: POS-2 FAR should be 0.05."""
    result = district_tools["lookup_district"](district_code="POS-2")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(0.05)


# ---------------------------------------------------------------------------
# Q159 — RM-5.5 has higher FAR than RM-5
# ---------------------------------------------------------------------------


def test_eval_q159_rm55_higher_far_than_rm5(district_tools):
    """Eval Q159: compare_districts RM-5 vs RM-5.5 — RM-5.5 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="RM-5", district_b="RM-5.5")
    assert "error" not in result
    rm5_far = float(result["floor_area_ratio"]["RM-5"])
    rm55_far = float(result["floor_area_ratio"]["RM-5.5"])
    assert rm55_far > rm5_far, (
        f"Expected RM-5.5 FAR ({rm55_far}) > RM-5 FAR ({rm5_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q160 — M2-3 has higher FAR than M2-2
# ---------------------------------------------------------------------------


def test_eval_q160_m2_3_higher_far_than_m2_2(district_tools):
    """Eval Q160: compare_districts M2-2 vs M2-3 — M2-3 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="M2-2", district_b="M2-3")
    assert "error" not in result
    m2_2_far = float(result["floor_area_ratio"]["M2-2"])
    m2_3_far = float(result["floor_area_ratio"]["M2-3"])
    assert m2_3_far > m2_2_far, (
        f"Expected M2-3 FAR ({m2_3_far}) > M2-2 FAR ({m2_2_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q161 — B1-1.5 FAR is 1.5
# ---------------------------------------------------------------------------


def test_eval_q161_b1_1_5_far(district_tools):
    """Eval Q161: B1-1.5 FAR should be 1.5."""
    result = district_tools["lookup_district"](district_code="B1-1.5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# Q162 — M3-3 development envelope on 4000 sqft lot = 12000 (FAR 3.0)
# ---------------------------------------------------------------------------


def test_eval_q162_m3_3_4000_envelope(development_tools):
    """Eval Q162: M3-3 FAR 3.0 × 4000 sqft lot = 12,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="M3-3", lot_area_sqft=4000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(12000.0)


# ---------------------------------------------------------------------------
# Q163 — DX-16 lot area per dwelling unit is 115 sqft
# ---------------------------------------------------------------------------


def test_eval_q163_dx16_lot_area_per_unit(district_tools):
    """Eval Q163: DX-16 lot_area_per_unit should reference 115 sqft."""
    result = district_tools["lookup_district"](district_code="DX-16")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "115" in lot_area.replace(",", ""), (
        f"Expected '115' in DX-16 lot_area_per_unit, got: {lot_area!r}"
    )


# ---------------------------------------------------------------------------
# Q164 — DC-12 FAR is 12.0
# ---------------------------------------------------------------------------


def test_eval_q164_dc12_far(district_tools):
    """Eval Q164: DC-12 FAR should be 12.0."""
    result = district_tools["lookup_district"](district_code="DC-12")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(12.0)


# ---------------------------------------------------------------------------
# Q165 — list downtown mixed-use districts includes DX-3
# ---------------------------------------------------------------------------


def test_eval_q165_list_downtown_mixed_use(district_tools):
    """Eval Q165: list_district_types(Downtown Mixed-Use) returns DX-series districts."""
    result = district_tools["list_district_types"](category="Downtown Mixed-Use")
    assert isinstance(result, list)
    codes = [d["district_type_code"] for d in result]
    assert any("DX" in c for c in codes), (
        f"Expected DX districts in Downtown Mixed-Use list, got: {codes}"
    )
    assert "DX-3" in codes or any(c.startswith("DX") for c in codes)


# ---------------------------------------------------------------------------
# Q166 — B1-1.5 has higher FAR than B1-1
# ---------------------------------------------------------------------------


def test_eval_q166_b1_1_5_higher_far_than_b1_1(district_tools):
    """Eval Q166: compare_districts B1-1 vs B1-1.5 — B1-1.5 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="B1-1", district_b="B1-1.5")
    assert "error" not in result
    b1_1_far = float(result["floor_area_ratio"]["B1-1"])
    b1_15_far = float(result["floor_area_ratio"]["B1-1.5"])
    assert b1_15_far > b1_1_far, (
        f"Expected B1-1.5 FAR ({b1_15_far}) > B1-1 FAR ({b1_1_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q167 — RM-4.5 max units on 12000 sqft lot = 16
# ---------------------------------------------------------------------------


def test_eval_q167_rm45_12000_units(development_tools):
    """Eval Q167: RM-4.5 lot_area_per_unit 750 sqft; 12000 / 750 = 16 units."""
    result = development_tools["calculate_development_envelope"](
        district_code="RM-4.5", lot_area_sqft=12000
    )
    assert "error" not in result
    assert result["max_dwelling_units"] == 16


# ---------------------------------------------------------------------------
# Q168 — DS-5 has higher FAR than DS-3
# ---------------------------------------------------------------------------


def test_eval_q168_ds5_higher_far_than_ds3(district_tools):
    """Eval Q168: compare_districts DS-3 vs DS-5 — DS-5 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="DS-3", district_b="DS-5")
    assert "error" not in result
    ds3_far = float(result["floor_area_ratio"]["DS-3"])
    ds5_far = float(result["floor_area_ratio"]["DS-5"])
    assert ds5_far > ds3_far, (
        f"Expected DS-5 FAR ({ds5_far}) > DS-3 FAR ({ds3_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q169 — C3-5 development envelope on 3000 sqft lot = 15000 (FAR 5.0)
# ---------------------------------------------------------------------------


def test_eval_q169_c3_5_3000_envelope(development_tools):
    """Eval Q169: C3-5 FAR 5.0 × 3000 sqft lot = 15,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="C3-5", lot_area_sqft=3000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(15000.0)


# ---------------------------------------------------------------------------
# Q170 — get section 17-13-0300 returns planned development content
# ---------------------------------------------------------------------------


def test_eval_q170_get_section_17_13_0300(code_search_tools):
    """Eval Q170: get_zoning_section('17-13-0300') returns planned development text."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["get_zoning_section"](section_number="17-13-0300")
    assert "error" not in result
    assert result["section"] == "17-13-0300"
    combined = (result.get("title", "") + " " + result.get("text", "")).lower()
    assert "planned" in combined, (
        f"Expected 'planned' in section 17-13-0300 content, got: {combined[:100]!r}"
    )


# ---------------------------------------------------------------------------
# Q171 — DC-16 lot area per dwelling unit is 115 sqft
# ---------------------------------------------------------------------------


def test_eval_q171_dc16_lot_area_per_unit(district_tools):
    """Eval Q171: DC-16 lot_area_per_unit should reference 115 sqft."""
    result = district_tools["lookup_district"](district_code="DC-16")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "115" in lot_area.replace(",", ""), (
        f"Expected '115' in DC-16 lot_area_per_unit, got: {lot_area!r}"
    )


# ---------------------------------------------------------------------------
# Q172 — M3-3 development envelope on 10000 sqft lot = 30000 (FAR 3.0)
# ---------------------------------------------------------------------------


def test_eval_q172_m3_3_10000_envelope(development_tools):
    """Eval Q172: M3-3 FAR 3.0 × 10000 sqft lot = 30,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="M3-3", lot_area_sqft=10000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(30000.0)


# ---------------------------------------------------------------------------
# Q173 — B1-2 lot area per dwelling unit is 700 sqft
# ---------------------------------------------------------------------------


def test_eval_q173_b1_2_lot_area_per_unit(district_tools):
    """Eval Q173: B1-2 lot_area_per_unit should reference 700 sqft."""
    result = district_tools["lookup_district"](district_code="B1-2")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "700" in lot_area.replace(",", ""), (
        f"Expected '700' in B1-2 lot_area_per_unit, got: {lot_area!r}"
    )


# ---------------------------------------------------------------------------
# Q174 — search green roof/sustainability returns Title 17 sections
# ---------------------------------------------------------------------------

_CODE_SEARCH_FIXTURE_SUSTAINABILITY = _CODE_SEARCH_FIXTURE + [
    {
        "section": "17-11-0100",
        "title": "Green Infrastructure and Sustainability Standards",
        "chapter": "Chapter 17-11",
        "text": (
            "Green roofs and other sustainability measures may be required or incentivized "
            "for new construction in certain districts. Green roof installations qualify "
            "for floor area bonus credits under the density bonus provisions of this title."
        ),
        "source_file": "chapter_17-11.txt",
    },
]


def test_eval_q174_search_green_roof(code_search_tools):
    """Eval Q174: search_zoning_code('green roof sustainability') returns Title 17 sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_SUSTAINABILITY,
    ):
        result = code_search_tools["search_zoning_code"](query="green roof sustainability")
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-") for s in sections)


# ---------------------------------------------------------------------------
# Q175 — RM-6 has higher FAR than RM-5
# ---------------------------------------------------------------------------


def test_eval_q175_rm6_higher_far_than_rm5(district_tools):
    """Eval Q175: compare_districts RM-5 vs RM-6 — RM-6 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="RM-5", district_b="RM-6")
    assert "error" not in result
    rm5_far = float(result["floor_area_ratio"]["RM-5"])
    rm6_far = float(result["floor_area_ratio"]["RM-6"])
    assert rm6_far > rm5_far, (
        f"Expected RM-6 FAR ({rm6_far}) > RM-5 FAR ({rm5_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q176 — search certificate of zoning compliance returns Title 17 sections
# ---------------------------------------------------------------------------

_CODE_SEARCH_FIXTURE_CERT_ZONING = _CODE_SEARCH_FIXTURE + [
    {
        "section": "17-13-0100",
        "title": "Zoning Certificates",
        "chapter": "Chapter 17-13",
        "text": (
            "A certificate of zoning compliance shall be required for any change "
            "of use or new construction. The certificate certifies that the proposed "
            "use or structure conforms to the applicable zoning district regulations."
        ),
        "source_file": "chapter_17-13.txt",
    },
]


def test_eval_q176_search_certificate_of_zoning(code_search_tools):
    """Eval Q176: search_zoning_code('certificate of zoning compliance') returns 17- sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_CERT_ZONING,
    ):
        result = code_search_tools["search_zoning_code"](
            query="certificate of zoning compliance"
        )
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-") for s in sections)
    assert any(
        "certificate" in r.get("title", "").lower()
        or "certificate" in r.get("text", "").lower()
        for r in result["results"]
    )


# ---------------------------------------------------------------------------
# Q177 — M3-3 maximum building height contains 55
# ---------------------------------------------------------------------------


def test_eval_q177_m3_3_height(district_tools):
    """Eval Q177: M3-3 maximum_building_height should reference 55 ft."""
    result = district_tools["lookup_district"](district_code="M3-3")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "55" in str(height), (
        f"Expected '55' in M3-3 maximum_building_height, got: {height!r}"
    )


# ---------------------------------------------------------------------------
# Q178 — RM-5 max units on 10000 sqft lot = 20
# ---------------------------------------------------------------------------


def test_eval_q178_rm5_10000_units(development_tools):
    """Eval Q178: RM-5 lot_area_per_unit 500 sqft; 10000 / 500 = 20 units."""
    result = development_tools["calculate_development_envelope"](
        district_code="RM-5", lot_area_sqft=10000
    )
    assert "error" not in result
    assert result["max_dwelling_units"] == 20


# ---------------------------------------------------------------------------
# Q179 — B1-2 has higher FAR than B1-1.5
# ---------------------------------------------------------------------------


def test_eval_q179_b1_2_higher_far_than_b1_1_5(district_tools):
    """Eval Q179: compare_districts B1-1.5 vs B1-2 — B1-2 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="B1-1.5", district_b="B1-2")
    assert "error" not in result
    b1_15_far = float(result["floor_area_ratio"]["B1-1.5"])
    b1_2_far = float(result["floor_area_ratio"]["B1-2"])
    assert b1_2_far > b1_15_far, (
        f"Expected B1-2 FAR ({b1_2_far}) > B1-1.5 FAR ({b1_15_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q180 — Willis Tower address routes to get_parcel_zoning (mocked, returns DC-16)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_eval_q180_willis_tower_address():
    """Eval Q180: 233 S Wacker Dr routes to get_parcel_zoning and returns DC-16.

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
                "properties": {"zone_class": "DC-16", "zone_type": "8"},
                "geometry": {"type": "MultiPolygon", "coordinates": []},
            }
        ],
    }

    with (
        patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo,
        patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_geo.return_value = (41.8789, -87.6359)  # Willis Tower coordinates

        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_socrata_response
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await tools["get_parcel_zoning"](address="233 S Wacker Dr")

    assert "error" not in result, f"Expected no error, got: {result.get('error')}"
    assert result.get("zone_class") == "DC-16"


# ---------------------------------------------------------------------------
# Q181 — POS-1 FAR is 0.1
# ---------------------------------------------------------------------------


def test_eval_q181_pos1_far(district_tools):
    """Eval Q181: POS-1 FAR should be 0.1."""
    result = district_tools["lookup_district"](district_code="POS-1")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(0.1)


# ---------------------------------------------------------------------------
# Q182 — RM-6.5 FAR is 6.6
# ---------------------------------------------------------------------------


def test_eval_q182_rm65_far(district_tools):
    """Eval Q182: RM-6.5 FAR should be 6.6."""
    result = district_tools["lookup_district"](district_code="RM-6.5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(6.6)


# ---------------------------------------------------------------------------
# Q183 — RM-6.5 has higher FAR than RM-6
# ---------------------------------------------------------------------------


def test_eval_q183_rm65_higher_far_than_rm6(district_tools):
    """Eval Q183: compare_districts RM-6 vs RM-6.5 — RM-6.5 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="RM-6", district_b="RM-6.5")
    assert "error" not in result
    rm6_far = float(result["floor_area_ratio"]["RM-6"])
    rm65_far = float(result["floor_area_ratio"]["RM-6.5"])
    assert rm65_far > rm6_far, (
        f"Expected RM-6.5 FAR ({rm65_far}) > RM-6 FAR ({rm6_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q184 — B2-1 category contains "Neighborhood" or "Shopping"
# ---------------------------------------------------------------------------


def test_eval_q184_b2_1_category(district_tools):
    """Eval Q184: B2-1 should be in the Neighborhood Mixed-Use / Business/Shopping category."""
    result = district_tools["lookup_district"](district_code="B2-1")
    assert "error" not in result
    category = result.get("category", "")
    assert "Neighborhood" in category or "Shopping" in category or "Business" in category, (
        f"Expected 'Neighborhood' or 'Shopping' in B2-1 category, got: {category!r}"
    )


# ---------------------------------------------------------------------------
# Q185 — DX-3 FAR is 3.0
# ---------------------------------------------------------------------------


def test_eval_q185_dx3_far(district_tools):
    """Eval Q185: DX-3 FAR should be 3.0."""
    result = district_tools["lookup_district"](district_code="DX-3")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Q186 — C2-5 FAR is 5.0
# ---------------------------------------------------------------------------


def test_eval_q186_c2_5_far(district_tools):
    """Eval Q186: C2-5 FAR should be 5.0."""
    result = district_tools["lookup_district"](district_code="C2-5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Q187 — RS-1 lot area per dwelling unit is 6500
# ---------------------------------------------------------------------------


def test_eval_q187_rs1_lot_area_per_unit(district_tools):
    """Eval Q187: RS-1 lot_area_per_unit should reference 6500 sqft per dwelling unit."""
    result = district_tools["lookup_district"](district_code="RS-1")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "6500" in lot_area.replace(",", ""), (
        f"Expected '6500' in lot_area_per_unit for RS-1, got: {lot_area!r}"
    )


# ---------------------------------------------------------------------------
# Q188 — RM-6.5 max floor area on 5000 sqft lot = 33000 (FAR 6.6)
# ---------------------------------------------------------------------------


def test_eval_q188_rm65_5000_envelope(development_tools):
    """Eval Q188: RM-6.5 FAR 6.6 × 5000 sqft lot = 33,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="RM-6.5", lot_area_sqft=5000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(33000.0)


# ---------------------------------------------------------------------------
# Q189 — POS-1 maximum building height contains "30"
# ---------------------------------------------------------------------------


def test_eval_q189_pos1_height(district_tools):
    """Eval Q189: POS-1 maximum_building_height should reference 30 ft."""
    result = district_tools["lookup_district"](district_code="POS-1")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "30" in str(height), (
        f"Expected '30' in POS-1 maximum_building_height, got: {height!r}"
    )


# ---------------------------------------------------------------------------
# Q190 — RS-2 has higher FAR than RS-1
# ---------------------------------------------------------------------------


def test_eval_q190_rs2_higher_far_than_rs1(district_tools):
    """Eval Q190: compare_districts RS-1 vs RS-2 — RS-2 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="RS-1", district_b="RS-2")
    assert "error" not in result
    rs1_far = float(result["floor_area_ratio"]["RS-1"])
    rs2_far = float(result["floor_area_ratio"]["RS-2"])
    assert rs2_far > rs1_far, (
        f"Expected RS-2 FAR ({rs2_far}) > RS-1 FAR ({rs1_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q191 — B3-1 category is Community Shopping
# ---------------------------------------------------------------------------


def test_eval_q191_b3_1_category(district_tools):
    """Eval Q191: B3-1 should be in the Community Shopping / Business/Shopping category."""
    result = district_tools["lookup_district"](district_code="B3-1")
    assert "error" not in result
    category = result.get("category", "")
    assert "Shopping" in category or "Business" in category or "Community" in category, (
        f"Expected 'Shopping' or 'Business' in B3-1 category, got: {category!r}"
    )


# ---------------------------------------------------------------------------
# Q192 — C3-1 FAR is 1.0
# ---------------------------------------------------------------------------


def test_eval_q192_c3_1_far(district_tools):
    """Eval Q192: C3-1 FAR should be 1.0."""
    result = district_tools["lookup_district"](district_code="C3-1")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Q193 — RM-4.5 maximum building height contains "38"
# ---------------------------------------------------------------------------


def test_eval_q193_rm45_height(district_tools):
    """Eval Q193: RM-4.5 maximum_building_height should reference 38 ft."""
    result = district_tools["lookup_district"](district_code="RM-4.5")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "38" in str(height), (
        f"Expected '38' in RM-4.5 maximum_building_height, got: {height!r}"
    )


# ---------------------------------------------------------------------------
# Q194 — DX-5 lot area per dwelling unit is 200
# ---------------------------------------------------------------------------


def test_eval_q194_dx5_lot_area_per_unit(district_tools):
    """Eval Q194: DX-5 lot_area_per_unit should reference 200 sqft per dwelling unit."""
    result = district_tools["lookup_district"](district_code="DX-5")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "200" in lot_area.replace(",", ""), (
        f"Expected '200' in lot_area_per_unit for DX-5, got: {lot_area!r}"
    )


# ---------------------------------------------------------------------------
# Q195 — search "rezoning procedures" returns Title 17 sections
# ---------------------------------------------------------------------------

_CODE_SEARCH_FIXTURE_REZONING = _CODE_SEARCH_FIXTURE + [
    {
        "section": "17-13-0300",
        "title": "Rezoning and Map Amendment Procedures",
        "chapter": "Chapter 17-13",
        "text": (
            "A zoning map amendment (rezoning) requires a recommendation from the "
            "Chicago Plan Commission and approval by the City Council. Applications "
            "must demonstrate consistency with the Comprehensive Plan and applicable "
            "planning policies."
        ),
        "source_file": "chapter_17-13.txt",
    },
]


def test_eval_q195_search_rezoning(code_search_tools):
    """Eval Q195: search_zoning_code('rezoning procedures') returns Title 17 sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_REZONING,
    ):
        result = code_search_tools["search_zoning_code"](query="rezoning procedures")
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-") for s in sections)


# ---------------------------------------------------------------------------
# Q196 — search "affordable housing" returns Title 17 sections
# ---------------------------------------------------------------------------

_CODE_SEARCH_FIXTURE_AFFORDABLE = _CODE_SEARCH_FIXTURE + [
    {
        "section": "17-4-1000",
        "title": "Affordable Housing Bonus",
        "chapter": "Chapter 17-4",
        "text": (
            "Developments that include affordable housing units may receive a floor "
            "area bonus under the Affordable Requirements Ordinance (ARO). Affordable "
            "units must remain affordable for a period of at least 30 years."
        ),
        "source_file": "chapter_17-4.txt",
    },
]


def test_eval_q196_search_affordable_housing(code_search_tools):
    """Eval Q196: search_zoning_code('affordable housing') returns Title 17 sections."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_AFFORDABLE,
    ):
        result = code_search_tools["search_zoning_code"](query="affordable housing requirements")
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-") for s in sections)
    assert any(
        "affordable" in r.get("title", "").lower()
        or "affordable" in r.get("text", "").lower()
        for r in result["results"]
    )


# ---------------------------------------------------------------------------
# Q197 — B1-3 max floor area on 5000 sqft lot = 15000 (FAR 3.0)
# ---------------------------------------------------------------------------


def test_eval_q197_b1_3_5000_envelope(development_tools):
    """Eval Q197: B1-3 FAR 3.0 × 5000 sqft lot = 15,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="B1-3", lot_area_sqft=5000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(15000.0)


# ---------------------------------------------------------------------------
# Q198 — DX-5 maximum building height contains "65"
# ---------------------------------------------------------------------------


def test_eval_q198_dx5_height(district_tools):
    """Eval Q198: DX-5 maximum_building_height should reference 65 ft."""
    result = district_tools["lookup_district"](district_code="DX-5")
    assert "error" not in result
    height = result.get("maximum_building_height", "")
    assert "65" in str(height), (
        f"Expected '65' in DX-5 maximum_building_height, got: {height!r}"
    )


# ---------------------------------------------------------------------------
# Q199 — address lookup at 4521 N Clark returns a B-series district (mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_eval_q199_clark_st_address():
    """Eval Q199: 4521 N Clark St routes to get_parcel_zoning and returns a B-series district.

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
                "properties": {"zone_class": "B3-2", "zone_type": "1"},
                "geometry": {"type": "MultiPolygon", "coordinates": []},
            }
        ],
    }

    with (
        patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo,
        patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_geo.return_value = (41.9620, -87.6591)  # 4521 N Clark St coordinates

        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_socrata_response
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await tools["get_parcel_zoning"](address="4521 N Clark St")

    assert "error" not in result, f"Expected no error, got: {result.get('error')}"
    zone = result.get("zone_class", "")
    assert zone.startswith("B"), f"Expected a B-series district for 4521 N Clark St, got: {zone!r}"


# ---------------------------------------------------------------------------
# Q200 — RM-6 max dwelling units on 5800 sqft lot = 29 (5800 / 200)
# ---------------------------------------------------------------------------


def test_eval_q200_rm6_5800_units(development_tools):
    """Eval Q200: RM-6 on 5800 sqft lot → 29 max dwelling units (5800 / 200)."""
    result = development_tools["calculate_development_envelope"](
        district_code="RM-6", lot_area_sqft=5800
    )
    assert "error" not in result
    assert result["max_dwelling_units"] == 29


# ---------------------------------------------------------------------------
# Q201 — DX-7 floor area ratio is 7.0
# ---------------------------------------------------------------------------


def test_eval_q201_dx7_far(district_tools):
    """Eval Q201: DX-7 FAR should be 7.0."""
    result = district_tools["lookup_district"](district_code="DX-7")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(7.0)


# ---------------------------------------------------------------------------
# Q202 — DX-12 floor area ratio is 12.0
# ---------------------------------------------------------------------------


def test_eval_q202_dx12_far(district_tools):
    """Eval Q202: DX-12 FAR should be 12.0."""
    result = district_tools["lookup_district"](district_code="DX-12")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(12.0)


# ---------------------------------------------------------------------------
# Q203 — DR-5 floor area ratio is 5.0
# ---------------------------------------------------------------------------


def test_eval_q203_dr5_far(district_tools):
    """Eval Q203: DR-5 FAR should be 5.0."""
    result = district_tools["lookup_district"](district_code="DR-5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Q204 — DR-7 floor area ratio is 7.0
# ---------------------------------------------------------------------------


def test_eval_q204_dr7_far(district_tools):
    """Eval Q204: DR-7 FAR should be 7.0."""
    result = district_tools["lookup_district"](district_code="DR-7")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(7.0)


# ---------------------------------------------------------------------------
# Q205 — B2-2 maximum building height contains "38"
# ---------------------------------------------------------------------------


def test_eval_q205_b2_2_height(district_tools):
    """Eval Q205: B2-2 maximum_building_height should reference 38 ft."""
    result = district_tools["lookup_district"](district_code="B2-2")
    assert "error" not in result
    assert "38" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q206 — C1-2 floor area ratio is 2.2
# ---------------------------------------------------------------------------


def test_eval_q206_c1_2_far(district_tools):
    """Eval Q206: C1-2 FAR should be 2.2."""
    result = district_tools["lookup_district"](district_code="C1-2")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(2.2)


# ---------------------------------------------------------------------------
# Q207 — M1-2 maximum building height contains "45"
# ---------------------------------------------------------------------------


def test_eval_q207_m1_2_height(district_tools):
    """Eval Q207: M1-2 maximum_building_height should reference 45 ft."""
    result = district_tools["lookup_district"](district_code="M1-2")
    assert "error" not in result
    assert "45" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q208 — RT-3.5 floor area ratio is 1.05
# ---------------------------------------------------------------------------


def test_eval_q208_rt35_far(district_tools):
    """Eval Q208: RT-3.5 FAR should be 1.05."""
    result = district_tools["lookup_district"](district_code="RT-3.5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(1.05)


# ---------------------------------------------------------------------------
# Q209 — RM-5.5 floor area ratio is 2.5
# ---------------------------------------------------------------------------


def test_eval_q209_rm55_far(district_tools):
    """Eval Q209: RM-5.5 FAR should be 2.5."""
    result = district_tools["lookup_district"](district_code="RM-5.5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(2.5)


# ---------------------------------------------------------------------------
# Q210 — B3-3 maximum building height contains "50"
# ---------------------------------------------------------------------------


def test_eval_q210_b3_3_height(district_tools):
    """Eval Q210: B3-3 maximum_building_height should reference 50 ft."""
    result = district_tools["lookup_district"](district_code="B3-3")
    assert "error" not in result
    assert "50" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q211 — compare DX-7 vs DX-12 — DX-12 has higher FAR
# ---------------------------------------------------------------------------


def test_eval_q211_dx7_vs_dx12_comparison(district_tools):
    """Eval Q211: compare_districts DX-7 vs DX-12 — DX-12 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="DX-7", district_b="DX-12")
    assert "error" not in result
    dx7_far = float(result["floor_area_ratio"]["DX-7"])
    dx12_far = float(result["floor_area_ratio"]["DX-12"])
    assert dx12_far > dx7_far, (
        f"Expected DX-12 FAR ({dx12_far}) > DX-7 FAR ({dx7_far})"
    )
    assert "floor_area_ratio" in result["_differences"]


# ---------------------------------------------------------------------------
# Q212 — DX-7 on 3000 sqft lot → 21,000 sqft max floor area
# ---------------------------------------------------------------------------


def test_eval_q212_dx7_3000_envelope(development_tools):
    """Eval Q212: DX-7 FAR 7.0 × 3000 sqft lot = 21,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="DX-7", lot_area_sqft=3000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(21000.0)


# ---------------------------------------------------------------------------
# Q213 — DR-5 on 4000 sqft lot → 20,000 sqft max floor area
# ---------------------------------------------------------------------------


def test_eval_q213_dr5_4000_envelope(development_tools):
    """Eval Q213: DR-5 FAR 5.0 × 4000 sqft lot = 20,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="DR-5", lot_area_sqft=4000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(20000.0)


# ---------------------------------------------------------------------------
# Q214 — B2-2 on 6000 sqft lot → 13,200 sqft max floor area
# ---------------------------------------------------------------------------


def test_eval_q214_b2_2_6000_envelope(development_tools):
    """Eval Q214: B2-2 FAR 2.2 × 6000 sqft lot = 13,200 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="B2-2", lot_area_sqft=6000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(13200.0)


# ---------------------------------------------------------------------------
# Q215 — M1-3 maximum building height contains "55"
# ---------------------------------------------------------------------------


def test_eval_q215_m1_3_height(district_tools):
    """Eval Q215: M1-3 maximum_building_height should reference 55 ft."""
    result = district_tools["lookup_district"](district_code="M1-3")
    assert "error" not in result
    assert "55" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q216 — C3-5 floor area ratio is 5.0
# ---------------------------------------------------------------------------


def test_eval_q216_c3_5_far(district_tools):
    """Eval Q216: C3-5 FAR should be 5.0."""
    result = district_tools["lookup_district"](district_code="C3-5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Q217 — POS-2 floor area ratio is 0.05
# ---------------------------------------------------------------------------


def test_eval_q217_pos2_far(district_tools):
    """Eval Q217: POS-2 FAR should be 0.05."""
    result = district_tools["lookup_district"](district_code="POS-2")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(0.05)


# ---------------------------------------------------------------------------
# Q218 — RM-5.5 lot area per unit contains "400"
# ---------------------------------------------------------------------------


def test_eval_q218_rm55_lot_area_per_unit(district_tools):
    """Eval Q218: RM-5.5 lot_area_per_unit should reference 400 sqft."""
    result = district_tools["lookup_district"](district_code="RM-5.5")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "400" in lot_area.replace(",", ""), (
        f"Expected '400' in RM-5.5 lot_area_per_unit, got: {lot_area!r}"
    )


# ---------------------------------------------------------------------------
# Q219 — Code search "sign regulations" returns a 17- section (fixture-based)
# ---------------------------------------------------------------------------

_CODE_SEARCH_FIXTURE_SIGNS = _CODE_SEARCH_FIXTURE + [
    {
        "section": "17-12-0100",
        "title": "Sign Regulations",
        "chapter": "Chapter 17-12",
        "text": (
            "Signs must comply with the regulations of this chapter. "
            "No sign may be erected, altered, relocated or maintained except in "
            "conformance with the provisions of this chapter. Outdoor advertising "
            "signs and billboards are regulated separately from on-premise signs."
        ),
        "source_file": "chapter_17-12.txt",
    },
]


def test_eval_q219_sign_regulations_code_search(code_search_tools):
    """Eval Q219: search_zoning_code('sign regulations') returns a Chapter 17-12 section."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_SIGNS,
    ):
        result = code_search_tools["search_zoning_code"](query="sign regulations")
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-12") for s in sections), (
        f"Expected a 17-12 section for sign regulations query, got: {sections}"
    )


# ---------------------------------------------------------------------------
# Q220 — address lookup at 121 N LaSalle St returns a DC-series district (mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_eval_q220_lasalle_st_address():
    """Eval Q220: 121 N LaSalle St routes to get_parcel_zoning and returns a DC-series district.

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
                "properties": {"zone_class": "DC-16", "zone_type": "8"},
                "geometry": {"type": "MultiPolygon", "coordinates": []},
            }
        ],
    }

    with (
        patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo,
        patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_geo.return_value = (41.8836, -87.6318)  # 121 N LaSalle St coordinates
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_socrata_response
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await tools["get_parcel_zoning"](address="121 N LaSalle St")

    assert "error" not in result, f"Expected no error, got: {result.get('error')}"
    zone = result.get("zone_class", "")
    assert zone.startswith("DC"), (
        f"Expected a DC-series district for 121 N LaSalle St, got: {zone!r}"
    )


# ---------------------------------------------------------------------------
# Q221 — M1-1 maximum building height contains "30"
# ---------------------------------------------------------------------------


def test_eval_q221_m1_1_height(district_tools):
    """Eval Q221: M1-1 maximum_building_height should reference 30 ft."""
    result = district_tools["lookup_district"](district_code="M1-1")
    assert "error" not in result
    assert "30" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q222 — RM-6 maximum building height contains "70"
# ---------------------------------------------------------------------------


def test_eval_q222_rm6_height(district_tools):
    """Eval Q222: RM-6 maximum_building_height should reference 70 ft."""
    result = district_tools["lookup_district"](district_code="RM-6")
    assert "error" not in result
    assert "70" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q223 — RM-6.5 maximum building height contains "80"
# ---------------------------------------------------------------------------


def test_eval_q223_rm65_height(district_tools):
    """Eval Q223: RM-6.5 maximum_building_height should reference 80 ft."""
    result = district_tools["lookup_district"](district_code="RM-6.5")
    assert "error" not in result
    assert "80" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q224 — DR-5 maximum building height contains "65"
# ---------------------------------------------------------------------------


def test_eval_q224_dr5_height(district_tools):
    """Eval Q224: DR-5 maximum_building_height should reference 65 ft."""
    result = district_tools["lookup_district"](district_code="DR-5")
    assert "error" not in result
    assert "65" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q225 — RS-1 front yard setback is 20 ft
# ---------------------------------------------------------------------------


def test_eval_q225_rs1_front_yard_setback(district_tools):
    """Eval Q225: RS-1 front_yard_setback should be 20 ft."""
    result = district_tools["lookup_district"](district_code="RS-1")
    assert "error" not in result
    setback = result.get("front_yard_setback", "")
    assert "20" in str(setback), f"Expected '20' in RS-1 front_yard_setback, got: {setback!r}"


# ---------------------------------------------------------------------------
# Q226 — RT-4 lot area per unit contains "1000"
# ---------------------------------------------------------------------------


def test_eval_q226_rt4_lot_area_per_unit(district_tools):
    """Eval Q226: RT-4 lot_area_per_unit should reference 1000 sqft."""
    result = district_tools["lookup_district"](district_code="RT-4")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "1000" in lot_area.replace(",", ""), (
        f"Expected '1000' in RT-4 lot_area_per_unit, got: {lot_area!r}"
    )


# ---------------------------------------------------------------------------
# Q227 — B2-3 maximum building height contains "45"
# ---------------------------------------------------------------------------


def test_eval_q227_b2_3_height(district_tools):
    """Eval Q227: B2-3 maximum_building_height should reference 45 ft."""
    result = district_tools["lookup_district"](district_code="B2-3")
    assert "error" not in result
    assert "45" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q228 — C1-3 maximum building height contains "50"
# ---------------------------------------------------------------------------


def test_eval_q228_c1_3_height(district_tools):
    """Eval Q228: C1-3 maximum_building_height should reference 50 ft."""
    result = district_tools["lookup_district"](district_code="C1-3")
    assert "error" not in result
    assert "50" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q229 — PD district FAR contains "Varies"
# ---------------------------------------------------------------------------


def test_eval_q229_pd_far_varies(district_tools):
    """Eval Q229: PD floor_area_ratio should reference 'Varies' (planned development)."""
    result = district_tools["lookup_district"](district_code="PD")
    assert "error" not in result
    far = result.get("floor_area_ratio", "")
    assert "Varies" in str(far), f"Expected 'Varies' in PD floor_area_ratio, got: {far!r}"


# ---------------------------------------------------------------------------
# Q230 — RM-6 lot area per unit contains "200"
# ---------------------------------------------------------------------------


def test_eval_q230_rm6_lot_area_per_unit(district_tools):
    """Eval Q230: RM-6 lot_area_per_unit should reference 200 sqft."""
    result = district_tools["lookup_district"](district_code="RM-6")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "200" in lot_area.replace(",", ""), (
        f"Expected '200' in RM-6 lot_area_per_unit, got: {lot_area!r}"
    )


# ---------------------------------------------------------------------------
# Q231 — list_district_types for Downtown Service includes DS-3 and DS-5
# ---------------------------------------------------------------------------


def test_eval_q231_list_downtown_service_districts(district_tools):
    """Eval Q231: list_district_types('Downtown Service') should include DS-3 and DS-5."""
    result = district_tools["list_district_types"](category="Downtown Service")
    assert isinstance(result, list)
    assert len(result) > 0
    district_codes = [d["district_type_code"] for d in result]
    assert any(code.startswith("DS") for code in district_codes), (
        f"Expected at least one DS district in results, got: {district_codes}"
    )


# ---------------------------------------------------------------------------
# Q232 — RM-6 development envelope on 4000 sqft lot = 17600
# ---------------------------------------------------------------------------


def test_eval_q232_rm6_4000_envelope(development_tools):
    """Eval Q232: RM-6 FAR 4.4 × 4000 sqft = 17,600 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="RM-6", lot_area_sqft=4000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(17600.0)


# ---------------------------------------------------------------------------
# Q233 — RM-6.5 development envelope on 3000 sqft lot = 19800
# ---------------------------------------------------------------------------


def test_eval_q233_rm65_3000_envelope(development_tools):
    """Eval Q233: RM-6.5 FAR 6.6 × 3000 sqft = 19,800 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="RM-6.5", lot_area_sqft=3000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(19800.0)


# ---------------------------------------------------------------------------
# Q234 — DR-3 development envelope on 5000 sqft lot = 15000
# ---------------------------------------------------------------------------


def test_eval_q234_dr3_5000_envelope(development_tools):
    """Eval Q234: DR-3 FAR 3.0 × 5000 sqft = 15,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="DR-3", lot_area_sqft=5000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(15000.0)


# ---------------------------------------------------------------------------
# Q235 — compare_districts M2-1 vs M2-2: M2-2 has higher FAR
# ---------------------------------------------------------------------------


def test_eval_q235_m2_1_vs_m2_2_far(district_tools):
    """Eval Q235: compare_districts M2-1 vs M2-2 — M2-2 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="M2-1", district_b="M2-2")
    assert "error" not in result
    m2_1_far = float(result["floor_area_ratio"]["M2-1"])
    m2_2_far = float(result["floor_area_ratio"]["M2-2"])
    assert m2_2_far > m2_1_far, f"Expected M2-2 FAR ({m2_2_far}) > M2-1 FAR ({m2_1_far})"


# ---------------------------------------------------------------------------
# Q236 — B1-2 maximum building height contains "38"
# ---------------------------------------------------------------------------


def test_eval_q236_b1_2_height(district_tools):
    """Eval Q236: B1-2 maximum_building_height should reference 38 ft."""
    result = district_tools["lookup_district"](district_code="B1-2")
    assert "error" not in result
    assert "38" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q237 — RS-1 rear yard setback contains "50"
# ---------------------------------------------------------------------------


def test_eval_q237_rs1_rear_yard_setback(district_tools):
    """Eval Q237: RS-1 rear_yard_setback should reference 50 ft."""
    result = district_tools["lookup_district"](district_code="RS-1")
    assert "error" not in result
    setback = result.get("rear_yard_setback", "")
    assert "50" in str(setback), f"Expected '50' in RS-1 rear_yard_setback, got: {setback!r}"


# ---------------------------------------------------------------------------
# Q238 — DR-3 maximum building height contains "45"
# ---------------------------------------------------------------------------


def test_eval_q238_dr3_height(district_tools):
    """Eval Q238: DR-3 maximum_building_height should reference 45 ft."""
    result = district_tools["lookup_district"](district_code="DR-3")
    assert "error" not in result
    assert "45" in result["maximum_building_height"]


# ---------------------------------------------------------------------------
# Q239 — Code search "special use permit" returns a 17- section (fixture-based)
# ---------------------------------------------------------------------------

_CODE_SEARCH_FIXTURE_SPECIAL_USE = _CODE_SEARCH_FIXTURE + [
    {
        "section": "17-13-0900",
        "title": "Special Use Permit Procedures",
        "chapter": "Chapter 17-13",
        "text": (
            "A special use permit authorizes uses that would not otherwise be permitted "
            "in a zoning district. Applications for special use permits must be submitted "
            "to the Zoning Board of Appeals. The Board shall hold a public hearing and "
            "may impose conditions to protect adjacent properties."
        ),
        "source_file": "chapter_17-13.txt",
    },
]


def test_eval_q239_special_use_code_search(code_search_tools):
    """Eval Q239: search_zoning_code('special use permit') returns a Chapter 17- section."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE_SPECIAL_USE,
    ):
        result = code_search_tools["search_zoning_code"](query="special use permit")
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-") for s in sections), (
        f"Expected a 17- section for special use permit query, got: {sections}"
    )


# ---------------------------------------------------------------------------
# Q240 — address lookup at 200 E Randolph St returns a DX-series district (mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_eval_q240_randolph_st_address():
    """Eval Q240: 200 E Randolph St routes to get_parcel_zoning and returns a DX-series district.

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
                "properties": {"zone_class": "DX-16", "zone_type": "7"},
                "geometry": {"type": "MultiPolygon", "coordinates": []},
            }
        ],
    }

    with (
        patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo,
        patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_geo.return_value = (41.8827, -87.6233)  # 200 E Randolph St coordinates
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_socrata_response
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await tools["get_parcel_zoning"](address="200 E Randolph St")

    assert "error" not in result, f"Expected no error, got: {result.get('error')}"
    zone = result.get("zone_class", "")
    assert zone.startswith("DX"), (
        f"Expected a DX-series district for 200 E Randolph St, got: {zone!r}"
    )


# ---------------------------------------------------------------------------
# Q241 — RS-2 floor area ratio is 0.65
# ---------------------------------------------------------------------------


def test_eval_q241_rs2_far(district_tools):
    """Eval Q241: RS-2 FAR should be 0.65."""
    result = district_tools["lookup_district"](district_code="RS-2")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(0.65)


# ---------------------------------------------------------------------------
# Q242 — RS-2 front yard setback contains "15"
# ---------------------------------------------------------------------------


def test_eval_q242_rs2_front_yard_setback(district_tools):
    """Eval Q242: RS-2 front_yard_setback should reference 15 ft."""
    result = district_tools["lookup_district"](district_code="RS-2")
    assert "error" not in result
    setback = result.get("front_yard_setback", "")
    assert "15" in str(setback), f"Expected '15' in RS-2 front_yard_setback, got: {setback!r}"


# ---------------------------------------------------------------------------
# Q243 — RS-2 rear yard setback contains "30"
# ---------------------------------------------------------------------------


def test_eval_q243_rs2_rear_yard_setback(district_tools):
    """Eval Q243: RS-2 rear_yard_setback should reference 30 ft."""
    result = district_tools["lookup_district"](district_code="RS-2")
    assert "error" not in result
    setback = result.get("rear_yard_setback", "")
    assert "30" in str(setback), f"Expected '30' in RS-2 rear_yard_setback, got: {setback!r}"


# ---------------------------------------------------------------------------
# Q244 — RM-5 floor area ratio is 2.0
# ---------------------------------------------------------------------------


def test_eval_q244_rm5_far(district_tools):
    """Eval Q244: RM-5 FAR should be 2.0."""
    result = district_tools["lookup_district"](district_code="RM-5")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Q245 — B1-1 floor area ratio is 1.0
# ---------------------------------------------------------------------------


def test_eval_q245_b1_1_far(district_tools):
    """Eval Q245: B1-1 FAR should be 1.0."""
    result = district_tools["lookup_district"](district_code="B1-1")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Q246 — DS-3 floor area ratio is 3.0
# ---------------------------------------------------------------------------


def test_eval_q246_ds3_far(district_tools):
    """Eval Q246: DS-3 FAR should be 3.0."""
    result = district_tools["lookup_district"](district_code="DS-3")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Q247 — POS-1 floor area ratio is 0.1
# ---------------------------------------------------------------------------


def test_eval_q247_pos1_far(district_tools):
    """Eval Q247: POS-1 FAR should be 0.1."""
    result = district_tools["lookup_district"](district_code="POS-1")
    assert "error" not in result
    assert float(result["floor_area_ratio"]) == pytest.approx(0.1)


# ---------------------------------------------------------------------------
# Q248 — RT-3.5 lot area per unit contains "1650"
# ---------------------------------------------------------------------------


def test_eval_q248_rt35_lot_area_per_unit(district_tools):
    """Eval Q248: RT-3.5 lot_area_per_unit should reference 1,650 sqft per dwelling unit."""
    result = district_tools["lookup_district"](district_code="RT-3.5")
    assert "error" not in result
    lot_area = result.get("lot_area_per_unit", "")
    assert "1650" in lot_area.replace(",", ""), (
        f"Expected '1650' in RT-3.5 lot_area_per_unit, got: {lot_area!r}"
    )


# ---------------------------------------------------------------------------
# Q249 — RS-2 6000 sqft lot → 3900 sqft max floor area (FAR 0.65)
# ---------------------------------------------------------------------------


def test_eval_q249_rs2_6000_envelope(development_tools):
    """Eval Q249: RS-2 FAR 0.65 × 6000 sqft lot = 3,900 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="RS-2", lot_area_sqft=6000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(3900.0)


# ---------------------------------------------------------------------------
# Q250 — RM-5 8000 sqft lot → 16000 sqft max floor area (FAR 2.0)
# ---------------------------------------------------------------------------


def test_eval_q250_rm5_8000_envelope(development_tools):
    """Eval Q250: RM-5 FAR 2.0 × 8000 sqft lot = 16,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="RM-5", lot_area_sqft=8000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(16000.0)


# ---------------------------------------------------------------------------
# Q251 — DS-3 4000 sqft lot → 12000 sqft max floor area (FAR 3.0)
# ---------------------------------------------------------------------------


def test_eval_q251_ds3_4000_envelope(development_tools):
    """Eval Q251: DS-3 FAR 3.0 × 4000 sqft lot = 12,000 sqft max floor area."""
    result = development_tools["calculate_development_envelope"](
        district_code="DS-3", lot_area_sqft=4000
    )
    assert "error" not in result
    assert result["max_floor_area_sqft"] == pytest.approx(12000.0)


# ---------------------------------------------------------------------------
# Q252 — compare_districts B3-3 vs B3-5: B3-5 has higher FAR
# ---------------------------------------------------------------------------


def test_eval_q252_b3_3_vs_b3_5_far(district_tools):
    """Eval Q252: compare_districts B3-3 vs B3-5 — B3-5 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="B3-3", district_b="B3-5")
    assert "error" not in result
    b3_3_far = float(result["floor_area_ratio"]["B3-3"])
    b3_5_far = float(result["floor_area_ratio"]["B3-5"])
    assert b3_5_far > b3_3_far, f"Expected B3-5 FAR ({b3_5_far}) > B3-3 FAR ({b3_3_far})"


# ---------------------------------------------------------------------------
# Q253 — compare_districts C1-2 vs C1-3: C1-3 has higher FAR
# ---------------------------------------------------------------------------


def test_eval_q253_c1_2_vs_c1_3_far(district_tools):
    """Eval Q253: compare_districts C1-2 vs C1-3 — C1-3 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="C1-2", district_b="C1-3")
    assert "error" not in result
    c1_2_far = float(result["floor_area_ratio"]["C1-2"])
    c1_3_far = float(result["floor_area_ratio"]["C1-3"])
    assert c1_3_far > c1_2_far, f"Expected C1-3 FAR ({c1_3_far}) > C1-2 FAR ({c1_2_far})"


# ---------------------------------------------------------------------------
# Q254 — compare_districts M1-1 vs M1-2: M1-2 has higher FAR
# ---------------------------------------------------------------------------


def test_eval_q254_m1_1_vs_m1_2_far(district_tools):
    """Eval Q254: compare_districts M1-1 vs M1-2 — M1-2 should have higher FAR."""
    result = district_tools["compare_districts"](district_a="M1-1", district_b="M1-2")
    assert "error" not in result
    m1_1_far = float(result["floor_area_ratio"]["M1-1"])
    m1_2_far = float(result["floor_area_ratio"]["M1-2"])
    assert m1_2_far > m1_1_far, f"Expected M1-2 FAR ({m1_2_far}) > M1-1 FAR ({m1_1_far})"


# ---------------------------------------------------------------------------
# Q255 — RS-3 side yard setback contains "8"
# ---------------------------------------------------------------------------


def test_eval_q255_rs3_side_setback(district_tools):
    """Eval Q255: RS-3 side_setback should reference combined 8 ft."""
    result = district_tools["lookup_district"](district_code="RS-3")
    assert "error" not in result
    side = result.get("side_setback", "")
    assert "8" in str(side), f"Expected '8' in RS-3 side_setback, got: {side!r}"


# ---------------------------------------------------------------------------
# Q256 — RS-1 minimum lot area contains "6500"
# ---------------------------------------------------------------------------


def test_eval_q256_rs1_minimum_lot_area(district_tools):
    """Eval Q256: RS-1 minimum_lot_area should reference 6,500 sqft."""
    result = district_tools["lookup_district"](district_code="RS-1")
    assert "error" not in result
    min_lot = result.get("minimum_lot_area", "")
    assert "6500" in str(min_lot).replace(",", ""), (
        f"Expected '6500' in RS-1 minimum_lot_area, got: {min_lot!r}"
    )


# ---------------------------------------------------------------------------
# Q257 — Code search "floor area ratio measurement" returns a 17- section (fixture-based)
# ---------------------------------------------------------------------------


def test_eval_q257_far_measurement_code_search(code_search_tools):
    """Eval Q257: search_zoning_code('floor area ratio measurement') returns Chapter 17-2."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["search_zoning_code"](query="floor area ratio measurement")
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-") for s in sections), (
        f"Expected a 17- section for FAR measurement query, got: {sections}"
    )


# ---------------------------------------------------------------------------
# Q258 — Code search "secondary residential unit" returns a 17- section (fixture-based)
# ---------------------------------------------------------------------------


def test_eval_q258_secondary_dwelling_code_search(code_search_tools):
    """Eval Q258: search_zoning_code('secondary residential unit') returns Chapter 17-3."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["search_zoning_code"](query="secondary residential unit")
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-") for s in sections), (
        f"Expected a 17- section for secondary dwelling unit query, got: {sections}"
    )


# ---------------------------------------------------------------------------
# Q259 — Code search "site plan traffic study" returns a 17- section (fixture-based)
# ---------------------------------------------------------------------------


def test_eval_q259_planned_development_code_search(code_search_tools):
    """Eval Q259: search_zoning_code('site plan traffic study') returns Chapter 17-13."""
    with patch(
        "src.tools.code_search.load_section_index",
        return_value=_CODE_SEARCH_FIXTURE,
    ):
        result = code_search_tools["search_zoning_code"](query="site plan traffic study")
    assert "error" not in result
    assert result["result_count"] >= 1
    sections = [r["section"] for r in result["results"]]
    assert any(s.startswith("17-") for s in sections), (
        f"Expected a 17- section for planned development query, got: {sections}"
    )


# ---------------------------------------------------------------------------
# Q260 — address lookup at 1060 W Addison St returns a B-series district (mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_eval_q260_wrigley_field_address():
    """Eval Q260: 1060 W Addison St (Wrigley Field) returns a B-series zoning district.

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
                "properties": {"zone_class": "B3-1", "zone_type": "1"},
                "geometry": {"type": "MultiPolygon", "coordinates": []},
            }
        ],
    }

    with (
        patch("src.tools.geospatial.geocode_address", new_callable=AsyncMock) as mock_geo,
        patch("src.tools.geospatial.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_geo.return_value = (41.9484, -87.6553)  # 1060 W Addison St coordinates
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
    zone = result.get("zone_class", "")
    assert zone.startswith("B"), (
        f"Expected a B-series district for 1060 W Addison St, got: {zone!r}"
    )
