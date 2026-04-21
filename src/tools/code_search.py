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


def search_sections(query: str, max_results: int = 5) -> list[dict]:
    """Keyword search across section titles and text.

    Returns matching sections ranked by number of keyword hits.
    """
    sections = load_section_index()
    if not sections:
        return []

    # Tokenize query into keywords
    keywords = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
    if not keywords:
        return []

    scored = []
    for section in sections:
        searchable = (
            f"{section.get('title', '')} {section.get('text', '')} {section.get('chapter', '')}"
        ).lower()
        score = sum(searchable.count(kw) for kw in keywords)
        if score > 0:
            scored.append((score, section))

    scored.sort(key=lambda x: x[0], reverse=True)

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
        """Search the text of Title 17 of the Chicago Municipal Code (the Zoning Ordinance).

        Finds sections matching your keywords. Useful for questions about
        specific regulations, procedures, definitions, or requirements
        that go beyond basic district lookup.

        Examples: "accessory dwelling unit", "parking requirements",
        "planned development approval process", "nonconforming use"
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
        """Retrieve the full text of a specific Title 17 section by its number.

        Use this when you know the exact section number you need (e.g. "17-3-0102",
        "17-15-0100"). Faster and more precise than keyword search when you have
        a specific cite.
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
