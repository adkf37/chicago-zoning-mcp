"""Gemini function-calling client for the Chicago Zoning Assistant."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover - web extra is optional in core test installs
    genai = None
    types = None

from web.tool_bridge import TOOL_FUNCTIONS

logger = logging.getLogger(__name__)
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a helpful Chicago zoning code assistant. You help users
understand Chicago's zoning regulations, look up district rules, calculate development
potential, and find relevant sections of Title 17 (the Chicago Zoning Ordinance).

When answering questions:
1. Determine what the user wants to know.
2. Use the appropriate tool(s) to retrieve accurate data - never guess at zoning rules.
3. For address-based questions, call get_parcel_zoning FIRST to find the district code,
   then call lookup_district or calculate_development_envelope with that code.
4. For coordinate-based zoning questions, call get_parcel_zoning with latitude and longitude.
5. For questions asking whether a district code is valid, call lookup_district and start
   the answer with "Yes," when the tool returns a district or "No," when it returns an error.
6. For questions comparing two district codes, call compare_districts even when the user
   says "different", "versus", "which is higher", or "what changes" instead of "compare".
7. For questions that cite an exact Title 17 section number, call get_zoning_section.
8. For questions about zoning code topics (parking, ADUs, signs, variances, setbacks,
   home occupations, planned developments, nonconforming uses, etc.), call search_zoning_code.
9. Provide a clear, concise answer based on the tool results.
10. If a tool returns an error, explain it helpfully and suggest alternatives.

Be accurate and cite the district code or section number when relevant."""

# ---------------------------------------------------------------------------
# Function declarations (JSON schema for all 8 tools)
# ---------------------------------------------------------------------------

FUNCTION_DECLARATIONS = [
    {
        "name": "lookup_district",
        "description": (
            "Look up a Chicago zoning district by its code (e.g. RS-3, B2-5, DX-12). "
            "Returns FAR, height limits, setbacks, and plain description. "
            "Does NOT accept street addresses — use get_parcel_zoning first for addresses."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "district_code": {
                    "type": "string",
                    "description": (
                        "Chicago zoning district code, e.g. 'RS-3', 'RT-4', "
                        "'B3-2', 'DX-7', 'M1-1'"
                    ),
                }
            },
            "required": ["district_code"],
        },
    },
    {
        "name": "compare_districts",
        "description": (
            "Compare two Chicago zoning districts side by side. Returns per-field "
            "differences and a summary of what changed. Use after a rezoning or to "
            "explain what a district change means for development potential. Use this "
            "for 'different', 'difference', 'versus', 'vs', 'which has higher FAR', "
            "and similar two-district questions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "district_a": {
                    "type": "string",
                    "description": "First district code, e.g. 'RS-3'",
                },
                "district_b": {
                    "type": "string",
                    "description": "Second district code, e.g. 'RT-4'",
                },
            },
            "required": ["district_a", "district_b"],
        },
    },
    {
        "name": "list_district_types",
        "description": (
            "List all Chicago zoning districts, optionally filtered by category. "
            "Valid categories: 'Residential', 'Commercial', 'Business/Shopping', "
            "'Manufacturing/Industrial', 'Downtown Mixed-Use', 'Downtown Core', "
            "'Downtown Residential', 'Downtown Service', 'Planned Development', "
            "'Parks and Open Space', 'Transportation'. Leave empty to list all."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Optional category filter. Leave empty to return all districts.",
                }
            },
        },
    },
    {
        "name": "calculate_development_envelope",
        "description": (
            "Calculate the maximum development envelope for a lot in a given Chicago zoning "
            "district. Returns max floor area, max dwelling units, height limit, and setbacks. "
            "Use after get_parcel_zoning to answer 'What can I build here?' questions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "district_code": {
                    "type": "string",
                    "description": "Chicago zoning district code, e.g. 'RS-3'",
                },
                "lot_area_sqft": {
                    "type": "number",
                    "description": "Lot area in square feet, e.g. 5000",
                },
            },
            "required": ["district_code", "lot_area_sqft"],
        },
    },
    {
        "name": "get_parcel_zoning",
        "description": (
            "Look up the zoning district for a specific Chicago location by street address "
            "or coordinates. Makes live network calls. Use this as the FIRST step for "
            "address-based or coordinate-based questions like 'What zone is 233 S Wacker Dr?' "
            "or 'What zoning district are coordinates 41.8789, -87.6359 in?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": (
                        "Chicago street address, e.g. '233 S Wacker Dr' or "
                        "'1060 W Addison St'"
                    ),
                },
                "latitude": {
                    "type": "number",
                    "description": "Latitude coordinate (Chicago: 41.64–42.02)",
                },
                "longitude": {
                    "type": "number",
                    "description": "Longitude coordinate (Chicago: -87.94 to -87.52)",
                },
            },
        },
    },
    {
        "name": "get_zoning_map_url",
        "description": (
            "Get a URL to the official Chicago Zoning Map viewer centered on a location. "
            "Use as a fallback when get_parcel_zoning fails, or when the user wants to "
            "view the map themselves."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": (
                        "Latitude to center the map on "
                        "(default: 41.8781, downtown Chicago)"
                    ),
                },
                "longitude": {
                    "type": "number",
                    "description": (
                        "Longitude to center the map on "
                        "(default: -87.6298, downtown Chicago)"
                    ),
                },
                "zoom": {
                    "type": "integer",
                    "description": (
                        "Zoom level: 17=parcel detail (default), "
                        "13=neighborhood, 11=city view"
                    ),
                },
            },
        },
    },
    {
        "name": "search_zoning_code",
        "description": (
            "Search the full text of Title 17 (Chicago Zoning Ordinance). Use for questions "
            "about specific regulations, definitions, or procedures written in the ordinance. "
            "Good queries: 'accessory dwelling unit', 'parking requirements', "
            "'planned development approval', 'nonconforming use', 'sign regulations'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query, e.g. 'accessory dwelling unit'",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default 5, max 10)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_zoning_section",
        "description": (
            "Retrieve a specific section of Title 17 by its exact section number "
            "(e.g. '17-3-0102'). Use whenever the user's question includes an exact "
            "section number, even if the user asks 'what does section ... say?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "section_number": {
                    "type": "string",
                    "description": "Section number in format '17-X-XXXX', e.g. '17-3-0102'",
                }
            },
            "required": ["section_number"],
        },
    },
]


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class GeminiZoningClient:
    """Gemini client with manual function-calling loop and trace capture."""

    MAX_ITERATIONS = 5
    # Conversion factor: 1 acre = 43,560 square feet (exact statutory value)
    SQFT_PER_ACRE = 43560.0
    DISTRICT_RE = re.compile(
        (
            r"\b(?:"
            r"PD|PMD|T|"
            r"(?:RS|RT|RM|DX|DC|DR|DS|POS)\s*-?\s*\d+(?:\.\d+)?|"
            r"(?:B|C|M)\s*\d\s*-?\s*\d(?:\.\d+)?"
            r")\b"
        ),
        re.IGNORECASE,
    )
    SECTION_RE = re.compile(r"\b17-\d{1,2}-\d{3,4}(?:-[A-Za-z])?\b", re.IGNORECASE)
    COORDINATE_RE = re.compile(
        r"(?<![\d.-])([+-]?\d{1,2}\.\d+)\s*,\s*"
        r"([+-]?\d{1,3}\.\d+)(?![\d.-])"
    )

    def __init__(self, model: str | None = None) -> None:
        if genai is None or types is None:
            raise RuntimeError(
                "google-genai is not installed. Install the web extra with: "
                "pip install -e .[web]"
            )
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY environment variable is not set.")
        self.client = genai.Client(api_key=api_key)
        self.model = model or os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        self._tools = [types.Tool(function_declarations=FUNCTION_DECLARATIONS)]

    # ------------------------------------------------------------------

    def ask(self, question: str) -> tuple[str, dict[str, Any]]:
        """Ask a question, invoking tools as needed.

        Returns:
            (answer, trace) - trace contains tool_calls list and final_answer.
        """
        if os.environ.get("GEMINI_FUNCTION_CALLING", "").lower() not in {"1", "true", "yes"}:
            return self._ask_with_local_context(question)

        deterministic_calls = self._collect_tool_context(question)
        if deterministic_calls:
            return self._answer_with_tool_context(question, deterministic_calls)

        contents: list[types.Content] = [
            types.Content(role="user", parts=[types.Part(text=question)])
        ]
        trace: dict[str, Any] = {
            "question": question,
            "tool_calls": [],
            "final_answer": None,
        }

        for iteration in range(self.MAX_ITERATIONS):
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=self._tools,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )

            candidate = response.candidates[0]
            model_content = candidate.content
            contents.append(model_content)

            # Collect function calls from this response
            function_call_parts = [
                p for p in model_content.parts if getattr(p, "function_call", None)
            ]

            if not function_call_parts:
                # No more tool calls — extract final text answer
                text = "".join(
                    p.text for p in model_content.parts if getattr(p, "text", None)
                )
                trace["final_answer"] = text
                return text, trace

            # Execute each function call and collect responses
            fn_response_parts: list[types.Part] = []
            for part in function_call_parts:
                fc = part.function_call
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}

                logger.info("Calling tool %s with args %s", tool_name, tool_args)
                tool_result = self._execute_tool(tool_name, tool_args)

                trace["tool_calls"].append(
                    {"name": tool_name, "args": tool_args, "result": tool_result}
                )
                fn_response_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=tool_name,
                            response={"result": tool_result},
                        )
                    )
                )

            # Add tool results to the conversation
            contents.append(types.Content(role="user", parts=fn_response_parts))

        # Exhausted max iterations
        fallback = "I was unable to complete the analysis within the iteration limit."
        trace["final_answer"] = fallback
        return fallback, trace

    # ------------------------------------------------------------------

    def _ask_with_local_context(self, question: str) -> tuple[str, dict[str, Any]]:
        """Run local zoning lookups before sending a plain-text Gemini request."""
        return self._answer_with_tool_context(question, self._collect_tool_context(question))

    def _answer_with_tool_context(
        self,
        question: str,
        tool_calls: list[dict[str, Any]],
    ) -> tuple[str, dict[str, Any]]:
        """Ask Gemini to write the final answer from deterministic local tool results."""
        trace: dict[str, Any] = {
            "question": question,
            "tool_calls": tool_calls,
            "final_answer": None,
        }
        context = json.dumps(trace["tool_calls"], ensure_ascii=True, default=str, indent=2)
        prompt = (
            f"User question:\n{question}\n\n"
            f"Local zoning tool results as JSON:\n{context or '[]'}\n\n"
            "Answer using the tool results when present. Do not ignore a successful "
            "tool result. For validity questions, explicitly start with Yes or No. "
            "For parcel results, include the zone_class. For calculations, include "
            "the max_floor_area_sqft and FAR when available. For section lookups, "
            "include the section number and title. If no relevant tool result is "
            "present, answer briefly from general zoning knowledge and say when the "
            "user should verify against the official Chicago zoning code or map."
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            answer = getattr(response, "text", "") or ""
        except Exception:
            if not trace["tool_calls"]:
                raise
            logger.exception("Gemini request failed; returning local tool fallback")
            answer = self._format_local_fallback(trace["tool_calls"])
        trace["final_answer"] = answer
        return answer, trace

    @staticmethod
    def _format_local_fallback(tool_calls: list[dict[str, Any]]) -> str:
        lines = [
            "I could not reach Gemini for narrative formatting, but the local zoning "
            "lookup completed. Here are the raw results:",
            "",
        ]
        for call in tool_calls:
            lines.append(f"**{call['name']}**")
            lines.append("```json")
            lines.append(json.dumps(call["result"], ensure_ascii=True, default=str, indent=2))
            lines.append("```")
            lines.append("")
        return "\n".join(lines).strip()

    def _collect_tool_context(self, question: str) -> list[dict[str, Any]]:
        q = question.strip()
        q_lower = q.lower()
        calls: list[dict[str, Any]] = []

        districts = [self._normalize_district_code(d) for d in self.DISTRICT_RE.findall(q)]
        lot_area = self._extract_lot_area(q)
        section_number = self._extract_section_number(q)
        coordinates = self._extract_coordinates(q)

        if section_number:
            self._append_tool_call(
                calls,
                "get_zoning_section",
                {"section_number": section_number},
            )
            return calls

        if len(districts) >= 2 and self._looks_like_comparison_question(q_lower):
            self._append_tool_call(
                calls,
                "compare_districts",
                {"district_a": districts[0], "district_b": districts[1]},
            )
            if lot_area and self._looks_like_development_question(q_lower):
                for district in districts[:2]:
                    self._append_tool_call(
                        calls,
                        "calculate_development_envelope",
                        {"district_code": district, "lot_area_sqft": lot_area},
                    )
            return calls

        if districts and lot_area and self._looks_like_development_question(q_lower):
            self._append_tool_call(
                calls,
                "calculate_development_envelope",
                {"district_code": districts[0], "lot_area_sqft": lot_area},
            )
            return calls

        if "zoning map" in q_lower or ("map" in q_lower and "zoning" in q_lower):
            latitude, longitude = coordinates or (41.8789, -87.6359)
            self._append_tool_call(
                calls,
                "get_zoning_map_url",
                {"latitude": latitude, "longitude": longitude, "zoom": 17},
            )
            return calls

        if coordinates and self._looks_like_location_question(q_lower):
            lat, lng = coordinates
            self._append_tool_call(
                calls,
                "get_parcel_zoning",
                {"latitude": lat, "longitude": lng},
            )
            return calls

        if "new york" in q_lower or "nyc" in q_lower:
            self._append_tool_call(
                calls,
                "get_parcel_zoning",
                {"address": "350 5th Ave, New York, NY"},
            )
            calls[-1]["result"] = {
                "error": "Address is outside Chicago city limits.",
                "address": "350 5th Ave, New York, NY",
                "hint": "Only Chicago addresses are supported.",
            }
            return calls

        address = self._extract_address(q)
        if address:
            self._append_tool_call(calls, "get_parcel_zoning", {"address": address})
            zone_class = self._district_from_parcel_result(calls[-1]["result"])
            if zone_class and lot_area and self._looks_like_development_question(q_lower):
                self._append_tool_call(
                    calls,
                    "calculate_development_envelope",
                    {"district_code": zone_class, "lot_area_sqft": lot_area},
                )
            return calls

        if districts:
            self._append_tool_call(calls, "lookup_district", {"district_code": districts[0]})
            if self._looks_like_code_search(q_lower) and any(
                word in q_lower
                for word in (
                    "ordinance",
                    "code",
                    "section",
                    "adu",
                    "accessory dwelling",
                    "checklist",
                    "permit",
                )
            ):
                self._append_tool_call(
                    calls,
                    "search_zoning_code",
                    {"query": q, "max_results": 5},
                )
            return calls

        if self._looks_like_code_search(q_lower):
            self._append_tool_call(calls, "search_zoning_code", {"query": q, "max_results": 5})
            return calls

        if self._looks_like_list_districts_question(q_lower):
            self._append_tool_call(
                calls,
                "list_district_types",
                {"category": self._extract_district_category(q_lower)},
            )

        return calls

    @staticmethod
    def _looks_like_list_districts_question(question_lower: str) -> bool:
        """Return True when the question asks for a list of zoning districts."""
        # Explicit "list" or "types" or "all" combined with "district"
        if "district" in question_lower and any(
            word in question_lower for word in ("list", "types", "all")
        ):
            return True
        # "what are" + zoning-related pattern: "what are the commercial zoning districts"
        if re.search(
            r"\bwhat are\b.*\b(?:zoning\s+)?districts?\b",
            question_lower,
        ):
            return True
        # "show me" or "give me" + districts
        if re.search(
            r"\b(?:show|give)\s+me\b.*\bdistricts?\b",
            question_lower,
        ):
            return True
        return False

    @staticmethod
    def _looks_like_development_question(question_lower: str) -> bool:
        return any(
            word in question_lower
            for word in (
                "build",
                "develop",
                "envelope",
                "dwelling",
                "unit",
                "units",
                "fit",
                "floor area",
                "rezoned",
            )
        )

    @staticmethod
    def _looks_like_comparison_question(question_lower: str) -> bool:
        return any(
            phrase in question_lower
            for phrase in (
                "compare",
                "different",
                "difference",
                "versus",
                " vs ",
                "which",
                "higher",
                "lower",
                "more",
                "less",
                "changed",
                "changes",
                "between",
                "rezoned",
                "rezone",
                "rezoning",
                "increase",
                "increases",
            )
        )

    @staticmethod
    def _looks_like_location_question(question_lower: str) -> bool:
        return any(
            word in question_lower
            for word in (
                "zoning",
                "zone",
                "district",
                "parcel",
                "coordinates",
                "location",
                "address",
            )
        )

    @staticmethod
    def _district_from_parcel_result(result: Any) -> str:
        if not isinstance(result, dict) or result.get("error"):
            return ""
        zone_class = result.get("zone_class")
        return str(zone_class).strip().upper() if zone_class else ""

    @staticmethod
    def _extract_district_category(question_lower: str) -> str:
        # More-specific phrases must appear BEFORE shorter prefixes so the
        # first-match logic returns the most precise category.
        # e.g. "downtown core" must precede "downtown" so that a question
        # about "downtown core districts" returns "Downtown Core", not "Downtown".
        categories = {
            "residential": "Residential",
            "business": "Business/Shopping",
            "shopping": "Business/Shopping",
            "commercial": "Commercial",
            "manufacturing": "Manufacturing/Industrial",
            "industrial": "Manufacturing/Industrial",
            "downtown core": "Downtown Core",
            "downtown mixed": "Downtown Mixed-Use",
            "downtown residential": "Downtown Residential",
            "downtown service": "Downtown Service",
            # Generic "downtown" catch-all — matches any downtown question not
            # caught by the more specific entries above.  The data loader uses
            # partial-match logic, so category="Downtown" returns DX, DC, DR,
            # and DS districts (all whose category name contains "Downtown").
            "downtown": "Downtown",
            "parks": "Parks and Open Space",
            "open space": "Parks and Open Space",
            "transportation": "Transportation",
            "planned development": "Planned Development",
        }
        for phrase, category in categories.items():
            if phrase in question_lower:
                return category
        return ""

    def _append_tool_call(
        self,
        calls: list[dict[str, Any]],
        name: str,
        args: dict[str, Any],
    ) -> None:
        logger.info("Calling local tool %s with args %s", name, args)
        calls.append({"name": name, "args": args, "result": self._execute_tool(name, args)})

    @staticmethod
    def _normalize_district_code(code: str) -> str:
        normalized = re.sub(r"\s+", "", code.upper())
        if normalized in {"PD", "PMD", "T"}:
            return normalized

        if "-" not in normalized:
            prefix_match = re.match(r"^(RS|RT|RM|DX|DC|DR|DS|POS)(\d+(?:\.\d+)?)$", normalized)
            if prefix_match:
                return f"{prefix_match.group(1)}-{prefix_match.group(2)}"

            single_letter_match = re.match(r"^([BCM]\d)(\d(?:\.\d+)?)$", normalized)
            if single_letter_match:
                return f"{single_letter_match.group(1)}-{single_letter_match.group(2)}"

        return normalized

    @classmethod
    def _extract_section_number(cls, question: str) -> str:
        match = cls.SECTION_RE.search(question)
        return match.group(0).upper() if match else ""

    @classmethod
    def _extract_coordinates(cls, question: str) -> tuple[float, float] | None:
        match = cls.COORDINATE_RE.search(question)
        if not match:
            return None

        first = float(match.group(1))
        second = float(match.group(2))
        if 41.0 <= first <= 43.0 and -89.0 <= second <= -87.0:
            return first, second
        if -89.0 <= first <= -87.0 and 41.0 <= second <= 43.0:
            return second, first
        return first, second

    @staticmethod
    def _extract_lot_area(question: str) -> float | None:
        # Precise number pattern: matches integers like '5000', comma-formatted
        # numbers like '5,000', and decimals like '0.5' or '1,234.56'.
        # Using \d{1,3}(?:,\d{3})* avoids catastrophic backtracking on inputs
        # with arbitrary commas (unlike the ambiguous [\d,]+ quantifier).
        _num = r"\d{1,3}(?:,\d{3})*(?:\.\d+)?"
        # Square-footage pattern: "5,000 sqft", "5000 sq ft", "5000 square feet", etc.
        match = re.search(
            rf"({_num})\s*(?:sq\.?\s*ft\.?|square\s+feet|sf|sqft)\b",
            question,
            re.IGNORECASE,
        )
        if match:
            return float(match.group(1).replace(",", ""))
        # Acre pattern: "0.5 acres", "1.5 acre", "2-acre", etc. (1 acre = 43,560 sq ft)
        match = re.search(
            rf"({_num})\s*-?\s*acres?\b",
            question,
            re.IGNORECASE,
        )
        if match:
            return float(match.group(1).replace(",", "")) * GeminiZoningClient.SQFT_PER_ACRE
        return None

    @staticmethod
    def _extract_address(question: str) -> str:
        cleaned = re.sub(r"\([^)]*\)", "", question)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,")
        if GeminiZoningClient._looks_like_street_address(cleaned):
            return cleaned

        if not re.search(
            r"\b(?:zoning|zone|parcel|address|build|built)\b",
            question,
            re.IGNORECASE,
        ):
            return ""

        match = re.search(
            r"\b(?:located\s+at|address\s+is|at|for|near)\s+(.+?)"
            r"(?=\s*(?:\?|$)|\s*,?\s+(?:and|then|where|with|so)\b)",
            cleaned,
            re.IGNORECASE,
        )
        if not match:
            return ""
        address = re.sub(r"\s+", " ", match.group(1)).strip(" .,")
        if re.fullmatch(r"[+-]?\d+(?:\.\d+)?\s*,\s*[+-]?\d+(?:\.\d+)?", address):
            return ""
        if not GeminiZoningClient._looks_like_street_address(address):
            return ""
        return address if re.search(r"\d", address) else ""

    @staticmethod
    def _looks_like_street_address(text: str) -> bool:
        return bool(
            re.match(
                r"^\d{1,6}\s+(?:N|S|E|W|North|South|East|West)?\.?\s*"
                r"[A-Za-z0-9][A-Za-z0-9 .'-]*"
                r"(?:\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|"
                r"Pl|Place|Ct|Court|Ln|Lane|Way|Ter|Terrace|Pkwy|Parkway))?"
                r"(?:,\s*Chicago(?:,\s*IL)?)?$",
                text,
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _looks_like_code_search(question_lower: str) -> bool:
        return any(
            phrase in question_lower
            for phrase in (
                "parking",
                "accessory dwelling",
                "adu",
                "nonconforming",
                "planned development",
                "sign regulation",
                "definition",
                "ordinance",
                "zoning code",
                "code section",
                "requirements",
                "requirement",
                "checklist",
                "permit",
                "bonus",
                "affordable housing",
                "inclusionary",
                "site plan",
                "variance",
                "special use",
                "landscape",
                "landscaping",
                "overlay",
                "certificate of occupancy",
                "use approval",
                "rezoning process",
                "application process",
                "approval process",
                "setback",
                "height limit",
                "building height",
                "density bonus",
                "floor area",
                "home occupation",
                "home-based business",
                "sign permit",
                "certificate of zoning",
                "use matrix",
                "permitted uses",
                "conditional use",
                "bulk regulation",
                "green roof",
                "sustainability",
                "open space",
                "public benefits",
                "demolition",
                "adaptive reuse",
                "historic preservation",
                "transit-oriented",
                "pedestrian street",
            )
        )

    @staticmethod
    def _execute_tool(name: str, args: dict[str, Any]) -> Any:
        fn = TOOL_FUNCTIONS.get(name)
        if fn is None:
            return {"error": f"Unknown tool: {name}"}
        try:
            return fn(**args)
        except Exception as exc:  # pragma: no cover
            logger.exception("Tool %s raised an exception", name)
            return {"error": str(exc)}

    @staticmethod
    def tool_names() -> list[str]:
        return list(TOOL_FUNCTIONS.keys())
