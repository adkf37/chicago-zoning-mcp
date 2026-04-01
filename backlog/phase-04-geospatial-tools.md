# Phase 4: Geospatial Tools

**Status:** Complete
**Depends on:** Phase 1
**Estimated scope:** M

## Objective

Implement address/coordinate-based zoning lookup so users can ask "what's the zoning at [address]?" and get a real answer from live Chicago data.

## Tasks

- [x] Implement `geocoder.py` — address → lat/lng via Nominatim (already scaffolded)
- [x] Implement `get_parcel_zoning` tool — geocode → Socrata spatial query → district lookup
- [x] Implement `get_zoning_map_url` tool — construct official Chicago zoning map link
- [x] Add rate limiting for Nominatim (1 req/sec)
- [x] Handle edge cases: address outside Chicago, ambiguous addresses, coordinates in Lake Michigan
- [x] Test with known addresses:
  - Wrigley Field: 1060 W Addison St → should be in a PD district
  - Willis Tower: 233 S Wacker Dr → DC-16
  - A residential block: e.g., 4521 N Clark St → RS-3 or similar
- [x] Write integration tests (can be marked as requiring network)

## Key Files

- `src/geocoder.py` — Nominatim geocoding client
- `src/tools/geospatial.py` — get_parcel_zoning, get_zoning_map_url
- `tests/test_geospatial.py` — integration tests

## Acceptance Criteria

- `get_parcel_zoning(address="233 S Wacker Dr")` returns a valid district code
- `get_parcel_zoning(latitude=41.8781, longitude=-87.6298)` works with coordinates
- `get_zoning_map_url()` returns a valid URL to Chicago's zoning map viewer
- Graceful error message for addresses outside Chicago

## Notes

- Nominatim has a 1 req/sec rate limit for the public instance. For heavier use, consider hosting a local Nominatim instance or using the Chicago geocoder API.
- The Socrata `intersects()` SoQL function may not work on all Socrata endpoints. The parent repo's `data_utils.py` has fallback patterns (`try_spatial_filter`).
