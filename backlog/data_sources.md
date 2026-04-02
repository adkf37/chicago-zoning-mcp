# Data Sources — chicago-zoning-mcp

## Static Data (in-repo)

### `data/zoning_codes.csv`

- **Source:** Ported from the parent `Plan_for_Chicago_2030` analysis repo
- **Contents:** One row per zoning district (~80 districts), columns include:
  - `district_type_code` — primary key (e.g., `RS-3`, `B2-5`, `DX-12`)
  - `zone_type` — integer category code (1–13)
  - `district_title` — human-readable district name
  - `old_description` — legacy description text
  - `juan_description` — plain-language description (note: loaded as `plain_description`)
  - `zoning_code_section` — Title 17 section reference
  - `floor_area_ratio` — numeric FAR value
  - `maximum_building_height` — height limit (often text with conditionals)
  - `lot_area_per_unit` — min lot area per dwelling unit
  - `front_yard_setback`, `side_setback`, `rear_yard_setback`, `rear_yard_open_space`, `on_site_open_space`
  - `minimum_lot_area`
- **Update frequency:** Static — reflects current Chicago zoning ordinance
- **Access:** Already in repo, no download required
- **Used by:** `src/data_loader.py`, all district lookup and development tools

### `data/title_17/sections.json` *(generated — gitignored)*

- **Source:** Built by running `python scripts/ingest_title_17.py` against manually
  downloaded raw text from American Legal Publishing
- **Contents:** JSON array of section objects:
  ```json
  [{"section": "17-2-0100", "title": "...", "text": "...", "chapter": "17-2"}, ...]
  ```
- **Update frequency:** Static until ordinance amended
- **Access:** **Requires manual step** — see Phase 5 and README for instructions
- **Used by:** `src/tools/code_search.py`
- **Note:** Until this file exists, `search_zoning_code` and `get_zoning_section` return a
  helpful error message directing the user to the ingestion instructions

---

## External APIs (live network calls)

### Chicago Data Portal — Zoning Districts (Socrata)

- **Endpoint:** `https://data.cityofchicago.org/resource/dj47-wfun.geojson`
- **Auth:** None required (public dataset)
- **Query method:** SoQL `$where=intersects(the_geom, 'POINT(lng lat)')` spatial filter
- **Returns:** GeoJSON FeatureCollection; `zone_class` property contains the district code
- **Rate limit:** Not formally documented; Chicago Data Portal is generally permissive
- **Used by:** `src/tools/geospatial.py` → `get_parcel_zoning`
- **Failure mode:** Returns helpful error dict on timeout (15s) or HTTP error; does not crash the server
- **Known issue:** The `intersects()` SoQL function may occasionally return 0 features
  for valid Chicago coordinates. Fallback: direct browse at
  `https://data.cityofchicago.org/Community-Economic-Development/Boundaries-Zoning-Districts-current-/7cve-jgbp`

### Nominatim (OpenStreetMap Geocoder)

- **Endpoint:** `https://nominatim.openstreetmap.org/search`
- **Auth:** None (public API, requires `User-Agent` header per OSM policy)
- **Query method:** Structured address search with `?q=<address>&format=json&limit=1`
- **Rate limit:** **1 request/second maximum** (OSM usage policy — enforced in `src/geocoder.py`)
- **Returns:** JSON array; lat/lon from first result
- **Used by:** `src/geocoder.py` → called by `get_parcel_zoning`
- **Failure mode:** Returns `None` on no result; caller returns error dict
- **Note:** For production/heavier use, consider running a local Nominatim instance
  or using the City of Chicago's geocoding API (`https://gisapps.chicago.gov/ARCGIS/rest/services/`)

---

## Data Freshness & Limitations

| Source | Freshness | Known Gaps |
|--------|-----------|------------|
| `zoning_codes.csv` | Reflects current ordinance (as of CSV creation) | Does not include Planned Development (PD) sub-area rules |
| Chicago Data Portal (Socrata) | Near-real-time (official city dataset) | Some PD parcels may not have a matching `zone_class` entry in our CSV |
| Title 17 text | Static copy from American Legal Publishing | Must be manually re-downloaded after ordinance amendments |
| Nominatim | Current OSM data | May lag official city records for new subdivisions or address changes |

---

## Data Not Used (and Why)

- **Cook County Assessor parcel data** — not needed; Socrata parcel geometry is sufficient for zoning lookup
- **Chicago Building Footprints** — not needed; development calculator uses user-supplied lot area
- **Zoning Board of Appeals decisions** — out of scope for v1
- **TIF district boundaries** — out of scope for v1
