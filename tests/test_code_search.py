"""Tests for zoning code text search tools.

Unit tests use a small in-memory fixture index to avoid requiring the full
sections.json (which is built from manually-downloaded Title 17 text).
"""

from unittest.mock import patch

from fastmcp import FastMCP

from src.tools.code_search import (
    get_section_by_number,
    register_code_search_tools,
    search_sections,
)

# ---------------------------------------------------------------------------
# Fixture index — a minimal set of realistic sections
# ---------------------------------------------------------------------------

FIXTURE_SECTIONS = [
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


def _patched_load():
    """Patch load_section_index to return FIXTURE_SECTIONS."""
    return patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS)


# ---------------------------------------------------------------------------
# Tests for search_sections()
# ---------------------------------------------------------------------------


def test_search_returns_relevant_section():
    """Searching 'accessory dwelling unit' should find section 17-3-0102."""
    with _patched_load():
        results = search_sections("accessory dwelling unit")
    assert any(r["section"] == "17-3-0102" for r in results)


def test_search_parking():
    """'parking requirements' should find section 17-10-0200."""
    with _patched_load():
        results = search_sections("parking requirements")
    assert len(results) > 0
    assert results[0]["section"] == "17-10-0200"


def test_search_nonconforming():
    """'nonconforming use' should find chapter 17-15."""
    with _patched_load():
        results = search_sections("nonconforming use")
    assert any(r["section"] == "17-15-0100" for r in results)


def test_search_planned_development():
    """'planned development' should surface the PD procedures section."""
    with _patched_load():
        results = search_sections("planned development application")
    assert any(r["section"] == "17-13-0300" for r in results)


def test_search_boosts_exact_title_phrase():
    """Exact title phrases should beat long sections with many body hits."""
    sections = [
        {
            "section": "17-13-0300",
            "title": "Zoning Map Amendments",
            "chapter": "Chapter 17-13",
            "text": "Procedures for rezonings.",
            "source_file": "chapter_17-13.txt",
        },
        {
            "section": "17-99-9999",
            "title": "Administrative Procedures",
            "chapter": "Chapter 17-99",
            "text": "zoning map amendments " * 20,
            "source_file": "chapter_17-99.txt",
        },
    ]
    with patch("src.tools.code_search.load_section_index", return_value=sections):
        results = search_sections("zoning map amendments")
    assert results[0]["section"] == "17-13-0300"


def test_search_respects_max_results():
    """max_results parameter should cap the number of results."""
    with _patched_load():
        results = search_sections("the", max_results=2)
    assert len(results) <= 2


def test_search_empty_query_returns_empty():
    """A query with no meaningful tokens should return empty."""
    with _patched_load():
        results = search_sections("   ")
    assert results == []


def test_search_no_match_returns_empty():
    """A query with no keyword matches should return an empty list."""
    with _patched_load():
        results = search_sections("xyzzy_nomatchwhatsoever")
    assert results == []


def test_search_result_has_required_fields():
    """Each result must include section, title, chapter, text, relevance_score."""
    with _patched_load():
        results = search_sections("parking")
    assert len(results) > 0
    r = results[0]
    for field in ("section", "title", "chapter", "text", "relevance_score"):
        assert field in r, f"Missing field: {field}"


def test_search_text_truncated_at_2000_chars():
    """Text in results should be truncated to 2000 characters."""
    long_section = {
        "section": "17-99-0001",
        "title": "Long Section",
        "chapter": "Chapter 17-99",
        "text": "parking " * 500,  # ~4000 chars
        "source_file": "test.txt",
    }
    with patch("src.tools.code_search.load_section_index", return_value=[long_section]):
        results = search_sections("parking", max_results=1)
    assert len(results[0]["text"]) <= 2000


# ---------------------------------------------------------------------------
# Tests for get_section_by_number()
# ---------------------------------------------------------------------------


def test_get_section_exact_match():
    """Direct section lookup by exact number should return the section."""
    with _patched_load():
        result = get_section_by_number("17-3-0102")
    assert result is not None
    assert result["section"] == "17-3-0102"
    assert "accessory" in result["title"].lower()


def test_get_section_case_insensitive():
    """Section lookup should be case-insensitive."""
    with _patched_load():
        result = get_section_by_number("17-3-0102")
    assert result is not None


def test_get_section_not_found():
    """Missing section number should return None."""
    with _patched_load():
        result = get_section_by_number("17-99-9999")
    assert result is None


def test_get_section_strips_whitespace():
    """Leading/trailing whitespace in section number should be ignored."""
    with _patched_load():
        result = get_section_by_number("  17-1-0101  ")
    assert result is not None


# ---------------------------------------------------------------------------
# Tests for MCP tools (via tool registration introspection)
# ---------------------------------------------------------------------------


def _make_tools() -> dict:
    """Register tools and capture function references."""
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
    register_code_search_tools(mcp)
    return tools


def test_search_tool_no_index():
    """search_zoning_code should return a helpful error when index is missing."""
    tools = _make_tools()
    with patch("src.tools.code_search.load_section_index", return_value=[]):
        result = tools["search_zoning_code"](query="parking")
    assert "error" in result
    assert "ingest_title_17" in result.get("hint", "")


def test_search_tool_no_results():
    """search_zoning_code should return empty results (not an error) for no-match."""
    tools = _make_tools()
    with patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS):
        result = tools["search_zoning_code"](query="xyzzy_nomatchwhatsoever")
    assert "error" not in result
    assert result["results"] == []
    # result_count should be present and 0 even when no results found
    assert result["result_count"] == 0


def test_search_tool_no_results_includes_query():
    """search_zoning_code no-results response should include the original query."""
    tools = _make_tools()
    with patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS):
        result = tools["search_zoning_code"](query="xyzzy_nomatchwhatsoever")
    assert result["query"] == "xyzzy_nomatchwhatsoever"


def test_search_tool_max_results_clamped_at_10():
    """search_zoning_code should cap results at 10 even when max_results > 10 is passed."""
    # Build a large fixture: 12 sections all matching the query
    large_fixture = [
        {
            "section": f"17-99-{i:03d}",
            "title": f"Parking Section {i}",
            "chapter": "Chapter 17-99",
            "text": "parking requirements apply here",
            "source_file": "chapter_17-99.txt",
        }
        for i in range(12)
    ]
    tools = _make_tools()
    with patch("src.tools.code_search.load_section_index", return_value=large_fixture):
        result = tools["search_zoning_code"](query="parking", max_results=20)
    assert "error" not in result
    assert len(result["results"]) <= 10
    assert result["result_count"] <= 10


def test_search_tool_returns_results():
    """search_zoning_code should return matching results."""
    tools = _make_tools()
    with patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS):
        result = tools["search_zoning_code"](query="accessory dwelling unit")
    assert result["result_count"] >= 1
    assert any(r["section"] == "17-3-0102" for r in result["results"])


def test_get_section_tool_no_index():
    """get_zoning_section should return a helpful error when index is missing."""
    tools = _make_tools()
    with patch("src.tools.code_search.load_section_index", return_value=[]):
        result = tools["get_zoning_section"](section_number="17-3-0102")
    assert "error" in result


def test_get_section_tool_found():
    """get_zoning_section should return the section when it exists."""
    tools = _make_tools()
    with patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS):
        result = tools["get_zoning_section"](section_number="17-3-0102")
    assert "error" not in result
    assert result["section"] == "17-3-0102"
    assert "title" in result
    assert "text" in result


def test_get_section_tool_not_found():
    """get_zoning_section should return an error for unknown section numbers."""
    tools = _make_tools()
    with patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS):
        result = tools["get_zoning_section"](section_number="17-99-9999")
    assert "error" in result
    assert "search_zoning_code" in result.get("hint", "")


# ---------------------------------------------------------------------------
# Tests for ingest_title_17 parser (unit test the parser directly)
# ---------------------------------------------------------------------------


def test_parser_extracts_sections():
    """parse_sections_from_text should extract section entries from raw text."""
    from scripts.ingest_title_17 import parse_sections_from_text

    sample = """\
17-3-0102  Accessory Dwelling Units.
An accessory dwelling unit (ADU) is a secondary residential unit.

17-3-0201  Setback Requirements.
Front yard setbacks shall be a minimum of 20 feet.
"""
    sections = parse_sections_from_text(sample)
    assert len(sections) == 2
    assert sections[0]["section"] == "17-3-0102"
    assert sections[0]["chapter"] == "Chapter 17-3"
    assert "accessory" in sections[0]["text"].lower()


def test_parser_handles_sec_prefix():
    """Parser handles 'Sec. 17-X-XXXX.' header format from amlegal.com."""
    from scripts.ingest_title_17 import parse_sections_from_text

    sample = """\
Sec. 17-10-0200.  Off-Street Parking Requirements.
Parking requirements vary by use and district.

Sec. 17-10-0201.  Bicycle Parking.
Bicycle parking is required for all new construction.
"""
    sections = parse_sections_from_text(sample)
    assert len(sections) == 2
    assert sections[0]["section"] == "17-10-0200"


def test_validate_index_warns_on_small_index():
    """validate_index should warn when fewer than 100 sections."""
    from scripts.ingest_title_17 import validate_index

    warnings = validate_index(FIXTURE_SECTIONS)
    # Should warn about count and missing chapters
    assert any("100" in w for w in warnings)


def test_validate_index_warns_on_duplicates():
    """validate_index should warn on duplicate section numbers."""
    from scripts.ingest_title_17 import validate_index

    dupe = FIXTURE_SECTIONS + [FIXTURE_SECTIONS[0]]  # add a duplicate
    warnings = validate_index(dupe)
    assert any("uplicate" in w for w in warnings)


def test_validate_index_no_warnings_on_full_valid_index():
    """A valid full-sized index with all chapters present should produce no warnings."""
    from scripts.ingest_title_17 import validate_index

    # Build a synthetic index with 500+ sections covering all 17 chapters
    big_index = []
    for chapter_num in range(1, 18):
        for section_num in range(100, 132):  # 31 sections per chapter = 527 total
            big_index.append({
                "section": f"17-{chapter_num}-0{section_num}",
                "title": f"Section {section_num}",
                "chapter": f"Chapter 17-{chapter_num}",
                "text": "Some regulation text here.",
                "source_file": f"chapter_17-{chapter_num}.txt",
            })

    warnings = validate_index(big_index)
    assert warnings == []
