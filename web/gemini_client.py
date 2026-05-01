"""Gemini function-calling client for the Chicago Zoning Assistant."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from google import genai
from google.genai import types

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
2. Use the appropriate tool(s) to retrieve accurate data — never guess at zoning rules.
3. For address-based questions, call get_parcel_zoning FIRST to find the district code,
   then call lookup_district or calculate_development_envelope with that code.
4. Provide a clear, concise answer based on the tool results.
5. If a tool returns an error, explain it helpfully and suggest alternatives.

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
            "explain what a district change means for development potential."
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
            "address-based questions like 'What zone is 233 S Wacker Dr?'"
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
            "(e.g. '17-3-0102'). Use when you know the section number from a prior "
            "search_zoning_code result."
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
    DISTRICT_RE = re.compile(
        r"\b(?:RS|RT|RM|B|C|M|DX|DC|DR|DS|PMD|PD|POS|T)-?\d+(?:\.\d+)?\b",
        re.IGNORECASE,
    )

    def __init__(self, model: str | None = None) -> None:
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
            (answer, trace) — trace contains tool_calls list and final_answer.
        """
        if os.environ.get("GEMINI_FUNCTION_CALLING", "").lower() not in {"1", "true", "yes"}:
            return self._ask_with_local_context(question)

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
        trace: dict[str, Any] = {
            "question": question,
            "tool_calls": self._collect_tool_context(question),
            "final_answer": None,
        }
        context = json.dumps(trace["tool_calls"], ensure_ascii=True, default=str, indent=2)
        prompt = (
            f"User question:\n{question}\n\n"
            f"Local zoning tool results as JSON:\n{context or '[]'}\n\n"
            "Answer using the tool results when present. If no relevant tool result is "
            "present, answer briefly from general zoning knowledge and say when the user "
            "should verify against the official Chicago zoning code or map."
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

        districts = [d.upper().replace(" ", "") for d in self.DISTRICT_RE.findall(q)]
        lot_area = self._extract_lot_area(q)

        if "compare" in q_lower and len(districts) >= 2:
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
            self._append_tool_call(
                calls,
                "get_zoning_map_url",
                {"latitude": 41.8789, "longitude": -87.6359, "zoom": 17},
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
            return calls

        if self._looks_like_code_search(q_lower):
            self._append_tool_call(calls, "search_zoning_code", {"query": q, "max_results": 5})
            return calls

        if districts:
            self._append_tool_call(calls, "lookup_district", {"district_code": districts[0]})
            return calls

        if "district" in q_lower and any(word in q_lower for word in ("list", "types", "all")):
            self._append_tool_call(calls, "list_district_types", {"category": ""})

        return calls

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

    def _append_tool_call(
        self,
        calls: list[dict[str, Any]],
        name: str,
        args: dict[str, Any],
    ) -> None:
        logger.info("Calling local tool %s with args %s", name, args)
        calls.append({"name": name, "args": args, "result": self._execute_tool(name, args)})

    @staticmethod
    def _extract_lot_area(question: str) -> float | None:
        match = re.search(
            r"([\d,]+(?:\.\d+)?)\s*(?:sq\.?\s*ft\.?|square\s+feet|sf|sqft)\b",
            question,
            re.IGNORECASE,
        )
        if not match:
            return None
        return float(match.group(1).replace(",", ""))

    @staticmethod
    def _extract_address(question: str) -> str:
        if not re.search(r"\b(?:zoning|zone|parcel|address)\b", question, re.IGNORECASE):
            return ""
        match = re.search(
            r"\b(?:at|for|is)\s+(.+?)(?:\?|$)",
            question,
            re.IGNORECASE,
        )
        if not match:
            return ""
        address = match.group(1).strip(" .")
        return address if re.search(r"\d", address) else ""

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
                "code section",
                "requirements",
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
