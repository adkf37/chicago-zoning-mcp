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


def test_structured_dc16_question_routes_to_lookup():
    """Q22: Structured professional prompt for DC-16 routes to lookup_district.

    A code-search call may also fire because the prompt mentions 'code section'.
    """
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context(
            "Aim: Provide a professional developer information on zoning district DC-16. "
            "Output: Provide the district title, FAR, and the zoning code section used."
        )

    names = _tool_names(calls)
    assert "lookup_district" in names
    assert calls[0]["args"] == {"district_code": "DC-16"}


def test_dx7_developer_lookup_routes_to_lookup():
    """Q33: DX-7 developer summary routes to lookup_district."""
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context(
            "Aim: I am a professional developer and I want to build in DX-7. "
            "Output: Summarize the relevant district limits with citations or code references."
        )

    assert _tool_names(calls) == ["lookup_district"]
    assert calls[0]["args"] == {"district_code": "DX-7"}


def test_rezoning_comparison_routes_to_compare_then_envelope():
    """Q34: Rezoning evaluation routes to compare_districts and calculate_development_envelope."""
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context(
            "Aim: Evaluate whether rezoning a 6,000 sqft RS-3 lot to RT-4 increases "
            "residential development capacity. Output: Include FAR and dwelling unit implications."
        )

    names = _tool_names(calls)
    assert "compare_districts" in names or "lookup_district" in names
    assert "calculate_development_envelope" in names


def test_zoning_map_with_coords_uses_map_url():
    """Q35: 'zoning map link for coordinates' routes to get_zoning_map_url."""
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context(
            "Give me a zoning map link for coordinates 41.8789, -87.6359."
        )

    assert _tool_names(calls) == ["get_zoning_map_url"]


def test_pos1_floor_area_routes_to_development():
    """Q37: POS-1 floor area on 10,000 sqft lot routes to calculate_development_envelope."""
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context(
            "What is the maximum floor area on a 10,000 sqft lot in POS-1?"
        )

    assert _tool_names(calls) == ["calculate_development_envelope"]
    assert calls[0]["args"] == {"district_code": "POS-1", "lot_area_sqft": 10000.0}


def test_dc16_without_hyphen_normalizes():
    """Q42: 'DC16' without hyphen should be normalized to 'DC-16'."""
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context(
            "DC16 zoning Chicago FAR height code section"
        )

    names = _tool_names(calls)
    assert "lookup_district" in names
    lookup_call = next(c for c in calls if c["name"] == "lookup_district")
    assert lookup_call["args"] == {"district_code": "DC-16"}


def test_b1_3_floor_area_routes_to_development():
    """Q44: B1-3 max floor area on 2,500 sqft routes to calculate_development_envelope."""
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context(
            "What is the maximum floor area on a 2,500 sqft lot zoned B1-3?"
        )

    assert _tool_names(calls) == ["calculate_development_envelope"]
    assert calls[0]["args"] == {"district_code": "B1-3", "lot_area_sqft": 2500.0}


def test_letter_suffixed_section_routes_to_get_section():
    """Section number with letter suffix (17-15-0102-A) routes to get_zoning_section."""
    client = _client()

    with patch.object(GeminiZoningClient, "_execute_tool", side_effect=_fake_tool):
        calls = client._collect_tool_context("What does section 17-15-0102-A say?")

    assert _tool_names(calls) == ["get_zoning_section"]
    assert calls[0]["args"] == {"section_number": "17-15-0102-A"}
