"""Zoning code text search tools.

Searches a section-indexed copy of Title 17 (Chicago Zoning Ordinance).
The index is built by scripts/ingest_title_17.py and stored in
data/title_17/sections.json.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

from fastmcp import FastMCP

TITLE_17_INDEX = Path(__file__).parent.parent.parent / "data" / "title_17" / "sections.json"


@lru_cache(maxsize=1)
def load_section_index() -> list[dict]:
    """Load the Title 17 section index.

    Each entry: {"section": "17-3-0102", "title": "...", "chapter": "...", "text": "..."}
    """
    if not TITLE_17_INDEX.exists():
        return []
    with open(TITLE_17_INDEX, encoding="utf-8") as f:
        return json.load(f)


# Cache of (sections_id, [(section, title_lc, text_lc, chapter_lc), ...]).
# Keying on identity lets tests patch `load_section_index` and have the
# precomputed lowercase fields rebuilt automatically.
_indexed_cache: tuple[int, list[tuple[dict, str, str, str]]] | None = None


def _load_search_index() -> list[tuple[dict, str, str, str]]:
    """Return the section index with precomputed lowercase fields.

    Lowercasing every section's title/text/chapter on every search was the
    hottest path in `search_sections`. We do it once and reuse it as long as
    the underlying section list is the same object.
    """
    global _indexed_cache
    sections = load_section_index()
    if _indexed_cache is not None and _indexed_cache[0] == id(sections):
        return _indexed_cache[1]
    indexed = [
        (
            section,
            section.get("title", "").lower(),
            section.get("text", "").lower(),
            section.get("chapter", "").lower(),
        )
        for section in sections
    ]
    _indexed_cache = (id(sections), indexed)
    return indexed


def search_sections(query: str, max_results: int = 5) -> list[dict]:
    """Keyword search across section titles and text.

    Returns matching sections ranked by phrase and keyword hits, with title
    matches weighted above body matches.
    """
    indexed = _load_search_index()
    if not indexed:
        return []

    # Tokenize query into keywords
    keywords = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
    if not keywords:
        return []

    phrase = " ".join(keywords)
    scored = []
    for section, title, text, chapter in indexed:
        score = 0
        if phrase and phrase in title:
            score += 100
        if phrase and phrase in text:
            score += 20
        if all(keyword in title for keyword in keywords):
            score += 15

        score += sum(title.count(keyword) * 5 for keyword in keywords)
        score += sum(chapter.count(keyword) * 2 for keyword in keywords)
        score += sum(text.count(keyword) for keyword in keywords)

        if score > 0:
            scored.append((score, section))

    scored.sort(key=lambda x: (-x[0], x[1].get("section", "")))

    return [
        {
            "section": s["section"],
            "title": s.get("title", ""),
            "chapter": s.get("chapter", ""),
            "text": s.get("text", "")[:2000],  # Truncate long sections
            "relevance_score": score,
        }
        for score, s in scored[:max_results]
    ]


def get_section_by_number(section_number: str) -> dict | None:
    """Return a single section by its exact section number (e.g. '17-3-0102').

    Case-insensitive. Returns None if not found.
    """
    sections = load_section_index()
    normalized = section_number.strip().upper()
    for section in sections:
        if section.get("section", "").upper() == normalized:
            return section
    return None


def register_code_search_tools(mcp: FastMCP):
    """Register code search tools with the MCP server."""

    @mcp.tool()
    def search_zoning_code(query: str, max_results: int = 5) -> dict:
        """Search the full text of Title 17 of the Chicago Municipal Code (the Zoning Ordinance).

        Use this tool when the user asks about specific regulations, procedures,
        definitions, or requirements that are written in the text of the zoning code
        — not just district lookup data. This tool searches the actual ordinance text.

        Examples of good queries: "accessory dwelling unit", "parking requirements",
        "planned development approval process", "nonconforming use", "sign regulations",
        "landscaping requirements", "bulk and density".

        Note: Requires the Title 17 text index to be built. If the index is not built,
        this tool returns a helpful error with instructions. All district-level data
        (FAR, height, setbacks) is available without the index via lookup_district.

        Returns: result_count and a ranked list of matching sections, each with
        section number, title, chapter, text snippet, and relevance_score.
        """
        results = search_sections(query, max_results=min(max_results, 10))

        if not results:
            if not load_section_index():
                return {
                    "error": "Title 17 text index not yet built.",
                    "hint": "Run: python scripts/ingest_title_17.py",
                }
            return {
                "results": [],
                "result_count": 0,
                "query": query,
                "message": "No matching sections found. Try different keywords.",
            }

        return {
            "query": query,
            "result_count": len(results),
            "results": results,
        }

    @mcp.tool()
    def get_zoning_section(section_number: str) -> dict:
        """Retrieve the full text of a specific Title 17 section by its section number.

        Use this tool when you know the exact section number you need and want its
        full text. Faster and more precise than search_zoning_code when you have a
        cite (e.g. from a previous search result, a permit, or a legal reference).

        Section number format: "17-X-XXXX" (e.g. "17-3-0102", "17-15-0100").
        Section numbers are case-insensitive.

        Note: Requires the Title 17 text index to be built (same requirement as
        search_zoning_code). Returns an error with instructions if the index is missing.
        """
        if not load_section_index():
            return {
                "error": "Title 17 text index not yet built.",
                "hint": "Run: python scripts/ingest_title_17.py",
            }

        section = get_section_by_number(section_number)
        if section is None:
            return {
                "error": f"Section '{section_number}' not found in the index.",
                "hint": (
                    "Check the section number format (e.g. '17-3-0102'). "
                    "Use search_zoning_code to find sections by keyword."
                ),
            }

        return {
            "section": section["section"],
            "title": section.get("title", ""),
            "chapter": section.get("chapter", ""),
            "text": section.get("text", ""),
        }

    @mcp.tool()
    def get_use_table(district_code: str) -> dict:
        """Return the permitted-use table for a Chicago zoning district.

        Use this tool when the user asks what types of uses (residential, retail,
        industrial, restaurant, office, daycare, etc.) are allowed, require special
        use approval, or are prohibited in a given district.

        The table uses these permission codes:
        - P  = Permitted by-right (no extra approval needed)
        - S  = Special Use approval required from the Zoning Board of Appeals
        - PD = Planned Development approval required from City Council
        - -  = Not allowed in this district

        The tool returns:
        - use_table_section: the Title 17 section number containing the full table
        - column_label: which column in the table corresponds to the requested district
        - use_table_text: the full text of the use table (interpret the column above)
        - legend: key for P / S / PD / -

        Supported district prefixes: RS, RT, RM, B1–B3, C1–C3, DC, DX, DR, DS,
        M1–M3. T, PD, PMD, and POS districts do not have a standard use table.

        Examples: get_use_table("RS-3"), get_use_table("B2-1"), get_use_table("M1-2")
        """
        from src.data_loader import get_district as _get_district

        if not load_section_index():
            return {
                "error": "Title 17 text index not yet built.",
                "hint": "Run: python scripts/ingest_title_17.py",
            }

        code = district_code.strip().upper()
        district_info = _get_district(code)
        if district_info is None:
            return {
                "error": f"District '{district_code}' not found.",
                "hint": "Use list_district_types to see all valid district codes.",
            }

        section_number, column_label, notes = _map_use_table(code)
        if section_number is None:
            return {
                "error": (
                    f"District '{code}' does not have a standard Title 17 use table. "
                    f"{notes or ''}"
                ),
                "district_title": district_info["district_title"],
            }

        section = get_section_by_number(section_number)
        if section is None:
            return {
                "error": (
                    f"Use table section {section_number} was not found in the index. "
                    "The Title 17 index may be incomplete — re-run ingest_title_17.py."
                ),
            }

        return {
            "district_code": code,
            "district_title": district_info["district_title"],
            "use_table_section": section_number,
            "column_label": column_label,
            "column_hint": (
                f"Look for the column labelled '{column_label}' in the table below "
                "to see what is Permitted (P), requires Special Use (S), requires "
                "Planned Development approval (PD), or is Not Allowed (-)."
            ),
            "legend": {
                "P": "Permitted by-right",
                "S": "Special Use approval required (Zoning Board of Appeals)",
                "PD": "Planned Development approval required (City Council)",
                "-": "Not allowed",
            },
            "use_table_text": section.get("text", ""),
            "source": f"Title 17 §{section_number} — {section.get('title', '')}",
        }


# ---------------------------------------------------------------------------
# Helpers for get_use_table
# ---------------------------------------------------------------------------

_USE_TABLE_MAP: dict[str, tuple[str, str]] = {
    # Residential families (17-2-0207)
    "RS-1": ("17-2-0207", "RS / column 1"),
    "RS-2": ("17-2-0207", "RS / column 2"),
    "RS-3": ("17-2-0207", "RS / column 3"),
    "RT-3.5": ("17-2-0207", "RT / column 3.5"),
    "RT-4": ("17-2-0207", "RT / column 4"),
    "RT-4.5": ("17-2-0207", "RT / column 4.5"),
    "RM-4.5": ("17-2-0207", "RM / column 4.5"),
    "RM-5": ("17-2-0207", "RM / column 5-5.5"),
    "RM-5.5": ("17-2-0207", "RM / column 5-5.5"),
    "RM-6": ("17-2-0207", "RM / column 6-6.5"),
    "RM-6.5": ("17-2-0207", "RM / column 6-6.5"),
}

# Families where the use-table column is just the district prefix (B1, B2, …)
_PREFIX_TABLE: list[tuple[str, str, str]] = [
    # (district prefix, section, column label)
    ("B1", "17-3-0207", "B1"),
    ("B2", "17-3-0207", "B2"),
    ("B3", "17-3-0207", "B3"),
    ("C1", "17-3-0207", "C1"),
    ("C2", "17-3-0207", "C2"),
    ("C3", "17-3-0207", "C3"),
    ("DC", "17-4-0207", "DC"),
    ("DX", "17-4-0207", "DX"),
    ("DR", "17-4-0207", "DR"),
    ("DS", "17-4-0207", "DS"),
    ("M1", "17-5-0207", "M1"),
    ("M2", "17-5-0207", "M2"),
    ("M3", "17-5-0207", "M3"),
]


def _map_use_table(code: str) -> tuple[str | None, str | None, str | None]:
    """Map a district code to (section_number, column_label, notes).

    Returns (None, None, hint_message) for districts without a standard table.
    """
    if code in _USE_TABLE_MAP:
        sec, col = _USE_TABLE_MAP[code]
        return sec, col, None

    # Try prefix match for B/C/D/M families
    for prefix, section, col_label in _PREFIX_TABLE:
        if code.startswith(prefix):
            return section, col_label, None

    # Districts without a standard use table
    no_table_hint = (
        "T (Transportation) and PMD (Planned Manufacturing District) districts "
        "are regulated by their specific ordinances. PD (Planned Development) "
        "and POS (Parks and Open Space) districts have separate use tables "
        "in Title 17 §17-6-0203-E and §17-6-0403-F respectively."
    )
    return None, None, no_table_hint
