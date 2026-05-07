"""Tests for get_use_table tool."""

from unittest.mock import patch

from fastmcp import FastMCP

from src.tools.code_search import _map_use_table, register_code_search_tools

# ---------------------------------------------------------------------------
# Minimal fixture index containing the four use-table sections
# ---------------------------------------------------------------------------

FIXTURE_SECTIONS = [
    {
        "section": "17-2-0207",
        "title": "Use Table and Standards",
        "chapter": "Chapter 17-2",
        "text": (
            "USE GROUP\nZoning Districts\nRS RS RS RT RT RM RM RM\n"
            "1  2  3  3.5 4  4.5 5-5.5 6-6.5\n"
            "P= permitted by-right  S = special use  - = Not allowed\n\n"
            "RESIDENTIAL\nA. Household Living\n"
            "1. Detached House  P P P P/- P/- P/- P/- P/-\n"
            "3. Two-Flat  - - P P P P/- P/- P/-\n"
            "5. Multi-Unit (3+ units)  - - - P P P P P\n"
        ),
    },
    {
        "section": "17-3-0207",
        "title": "Use Table and Standards",
        "chapter": "Chapter 17-3",
        "text": (
            "USE GROUP\nZoning Districts\nB1 B2 B3 C1 C2 C3\n"
            "P= permitted by-right  S = special use  - = Not allowed\n\n"
            "RETAIL AND SERVICE\n1. Eating and Drinking  P P P P P P\n"
            "2. Drive-through facility  S S S P P P\n"
        ),
    },
    {
        "section": "17-4-0207",
        "title": "Use Table and Standards",
        "chapter": "Chapter 17-4",
        "text": (
            "USE GROUP\nZoning Districts\nDC DX DR DS\n"
            "P= permitted by-right  - = Not allowed\n\n"
            "RESIDENTIAL\n1. Dwelling Units above ground floor  P P P -\n"
        ),
    },
    {
        "section": "17-5-0207",
        "title": "Use Table and Standards",
        "chapter": "Chapter 17-5",
        "text": (
            "USE GROUP\nDistrict\nM1 M2 M3\n"
            "P= permitted by-right  S = special use  - = Not allowed\n\n"
            "MANUFACTURING\n1. Heavy Manufacturing  - S P\n"
        ),
    },
]


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
    with patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS):
        register_code_search_tools(mcp)
    return tools["get_use_table"]


# ---------------------------------------------------------------------------
# Tests for _map_use_table helper
# ---------------------------------------------------------------------------


def test_map_residential_districts():
    assert _map_use_table("RS-1") == ("17-2-0207", "RS / column 1", None)
    assert _map_use_table("RS-3") == ("17-2-0207", "RS / column 3", None)
    assert _map_use_table("RT-4") == ("17-2-0207", "RT / column 4", None)
    assert _map_use_table("RM-5") == ("17-2-0207", "RM / column 5-5.5", None)
    assert _map_use_table("RM-6.5") == ("17-2-0207", "RM / column 6-6.5", None)


def test_map_business_commercial_districts():
    assert _map_use_table("B1-1")[0] == "17-3-0207"
    assert _map_use_table("B1-1")[1] == "B1"
    assert _map_use_table("B2-3")[1] == "B2"
    assert _map_use_table("C3-2")[1] == "C3"


def test_map_downtown_districts():
    assert _map_use_table("DC-16") == ("17-4-0207", "DC", None)
    assert _map_use_table("DX-7") == ("17-4-0207", "DX", None)
    assert _map_use_table("DR-3") == ("17-4-0207", "DR", None)


def test_map_manufacturing_districts():
    assert _map_use_table("M1-1") == ("17-5-0207", "M1", None)
    assert _map_use_table("M2-2") == ("17-5-0207", "M2", None)
    assert _map_use_table("M3-3") == ("17-5-0207", "M3", None)


def test_map_no_table_districts():
    sec, col, notes = _map_use_table("T")
    assert sec is None
    assert notes is not None

    sec2, col2, notes2 = _map_use_table("PD")
    assert sec2 is None


# ---------------------------------------------------------------------------
# Tests for the registered MCP tool (with mocked index)
# ---------------------------------------------------------------------------


def test_get_use_table_rs3():
    """RS-3 should map to 17-2-0207 with the correct column hint."""
    tool = _get_tool()
    with patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS):
        result = tool("RS-3")

    assert "error" not in result
    assert result["district_code"] == "RS-3"
    assert result["use_table_section"] == "17-2-0207"
    assert "RS / column 3" in result["column_label"]
    assert "use_table_text" in result
    assert "P" in result["legend"]
    assert "S" in result["legend"]


def test_get_use_table_b2():
    tool = _get_tool()
    with patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS):
        result = tool("B2-1")

    assert "error" not in result
    assert result["use_table_section"] == "17-3-0207"
    assert result["column_label"] == "B2"


def test_get_use_table_m1():
    tool = _get_tool()
    with patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS):
        result = tool("M1-1")

    assert "error" not in result
    assert result["use_table_section"] == "17-5-0207"


def test_get_use_table_unknown_district():
    tool = _get_tool()
    with patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS):
        result = tool("ZZ-99")
    assert "error" in result


def test_get_use_table_no_standard_table():
    """T (Transportation) district has no standard use table."""
    tool = _get_tool()
    with patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS):
        result = tool("T")
    assert "error" in result


def test_get_use_table_no_index():
    """Should return a helpful error when the Title 17 index is not built."""
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
    with patch("src.tools.code_search.load_section_index", return_value=[]):
        register_code_search_tools(mcp)
        result = tools["get_use_table"]("RS-3")

    assert "error" in result
    assert "index" in result["error"].lower() or "hint" in result


def test_get_use_table_response_has_legend():
    tool = _get_tool()
    with patch("src.tools.code_search.load_section_index", return_value=FIXTURE_SECTIONS):
        result = tool("DC-16")
    assert "legend" in result
    assert result["legend"]["P"] == "Permitted by-right"
