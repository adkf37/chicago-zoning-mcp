"""Tests for deterministic tool routing in the web Gemini client."""

from unittest.mock import patch

from web.gemini_client import GeminiZoningClient


def _client() -> GeminiZoningClient:
    return GeminiZoningClient.__new__(GeminiZoningClient)


def _fake_tool(name: str, args: dict) -> dict:
    if name == "get_parcel_zoning":
        return {"zone_class": "B3-2"}
    return {"ok": True, **args}


def _tool_names(calls: list[dict]) -> list[str]:
    return [call["name"] for call in calls]


def test_valid_district_question_routes_to_lookup():
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context("Is DC-16 a valid zoning district code?")

    assert _tool_names(calls) == ["lookup_district"]
    assert calls[0]["args"] == {"district_code": "DC-16"}


def test_for_phrase_with_district_is_not_misread_as_address():
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context(
            "my zoning info for single family home in RS-3 residential district Chicago"
        )

    assert _tool_names(calls) == ["lookup_district"]
    assert calls[0]["args"] == {"district_code": "RS-3"}


def test_bare_street_address_routes_to_parcel_zoning():
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context("2821 w sherwin")

    assert _tool_names(calls) == ["get_parcel_zoning"]
    assert calls[0]["args"] == {"address": "2821 w sherwin"}


def test_b_district_comparison_preserves_full_codes():
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context(
            "What is different about the floor area ratio between B1-1 and B1-3?"
        )

    assert _tool_names(calls) == ["compare_districts"]
    assert calls[0]["args"] == {"district_a": "B1-1", "district_b": "B1-3"}


def test_coordinate_question_routes_to_parcel_zoning():
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context(
            "What zoning district are coordinates 41.8789, -87.6359 in?"
        )

    assert _tool_names(calls) == ["get_parcel_zoning"]
    assert calls[0]["args"] == {"latitude": 41.8789, "longitude": -87.6359}


def test_zoning_map_question_with_coordinates_routes_to_map_url():
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context(
            "Give me a zoning map link for coordinates 41.8789, -87.6359."
        )

    assert _tool_names(calls) == ["get_zoning_map_url"]
    assert calls[0]["args"] == {"latitude": 41.8789, "longitude": -87.6359, "zoom": 17}


def test_direct_section_question_routes_to_get_section():
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context("What does section 17-15-0100 say?")

    assert _tool_names(calls) == ["get_zoning_section"]
    assert calls[0]["args"] == {"section_number": "17-15-0100"}


def test_address_development_question_chains_parcel_then_envelope():
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context(
            "What's the zoning at 4521 N Clark St, and how much floor area can "
            "I build on a 3,000 sqft lot there?"
        )

    assert _tool_names(calls) == ["get_parcel_zoning", "calculate_development_envelope"]
    assert calls[0]["args"] == {"address": "4521 N Clark St"}
    assert calls[1]["args"] == {"district_code": "B3-2", "lot_area_sqft": 3000.0}
