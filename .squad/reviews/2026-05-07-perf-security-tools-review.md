# Project Review — Performance, Security, Advanced Tools

Date: 2026-05-07
Scope: Full repo audit per user request — speed, additional tools, security.

## 1. Performance findings & fixes

### Implemented in this pass

| # | Issue | Fix | Expected impact |
|---|-------|-----|-----------------|
| P1 | `web/tool_bridge.py` opened a new `httpx.Client()` per geocode and per Socrata call (TLS handshake, DNS each call) | Module-level reusable `httpx.Client` with connection pool | ~50–200 ms saved per network tool call after the first one |
| P2 | `src/tools/geospatial.py` opened a new `httpx.AsyncClient()` per call | Module-level reusable async client | Same as P1 for the MCP-stdio path |
| P3 | `search_zoning_code` re-lowercased every section's `title`, `text`, and `chapter` on every query (O(N×L)) | Precompute lowercase fields once at index load | 2×–4× faster keyword search; matters more as Title 17 ingestion fills in |
| P4 | Geocoding hit Nominatim every time (with a forced 1.1 s sleep) even for repeated addresses | LRU cache on normalized address → coords | Repeat queries answer in <1 ms instead of >1 s |
| P5 | Socrata point-in-polygon lookup repeated for the same coordinates | LRU cache keyed on coordinates rounded to ~1 m | Cuts a 200–800 ms HTTP call to <1 ms on repeats |
| P6 | Socrata response was a full GeoJSON FeatureCollection with all geometry fields | Added `$select=zone_class,zone_type,edit_date,objectid,case_number` so the wire payload is small | 10×+ smaller responses; less JSON parsing |
| P7 | `pandas>=2.0` was a runtime dependency but was never imported anywhere | Dropped from `pyproject.toml` | ~70 MB lighter install; faster cold start on Docker |

### Not implemented (deliberate — flagged for future work)

- **Title 17 search ranking** — current implementation is keyword-count scoring. A `rapidfuzz`-based or BM25 ranker would improve relevance, but the index is small enough today that the linear pass is fast.
- **Streaming Gemini responses** — the web UI waits for the full answer. Switching `/api/chat` to Server-Sent Events would noticeably improve perceived latency on long answers; this is a larger UX change and out of scope for a perf pass.
- **Persistent on-disk cache for Socrata/Nominatim** — current caches are in-process. A small SQLite cache (e.g. `diskcache`) would survive restarts. Worth doing if the web app is deployed long-running.

## 2. Security findings & fixes

### Implemented in this pass

| # | Severity | Issue | Fix |
|---|---------|-------|-----|
| S1 | **High** | `web/templates/index.html` rendered LLM/tool-controlled markdown via `body.innerHTML = marked.parse(content)`. Marked v4+ no longer sanitizes; a prompt-injected (or otherwise malicious) tool result could execute `<script>` or `<img onerror>` — classic stored XSS in a chat UI. | Added [DOMPurify](https://github.com/cure53/DOMPurify) and now do `body.innerHTML = DOMPurify.sanitize(marked.parse(content))`. |
| S2 | Medium | CDN scripts (`marked`, `DOMPurify`) loaded without [Subresource Integrity](https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity) hashes, so a CDN compromise could execute arbitrary JS in the chat UI. | Pinned versions and added `integrity=` + `crossorigin="anonymous"`. |
| S3 | Medium | `/api/chat` accepted unbounded `question` strings, so a single client could fan a 10 MB question into a Gemini call, billing/DoS risk. | Reject `question` longer than 4 000 chars with HTTP 413. |
| S4 | Low | `pandas` was an unused dependency, expanding the supply-chain attack surface and Docker image size. | Removed. |

### Verified safe (no change needed)

- **SOQL injection in Socrata calls** — `lat`/`lng` are coerced to `float` before the f-string, and `address` never reaches the Socrata `$where` clause. No injection vector.
- **Geocoder rate limiting** — Nominatim's 1 req/sec policy is honored for both the async (`src/geocoder.py`) and sync (`web/tool_bridge.py`) paths.
- **TLS verification** — All `httpx` calls use defaults (verify=True). No insecure overrides.
- **Server-side errors** — The Flask error handler emits a generic message and never echoes the raw exception to the client.
- **No persisted user data, no auth surface** — the server doesn't write user input to disk and exposes no admin endpoints. Any production deployment should still front this with a reverse proxy + rate limiter.

### Production hardening to-do (flagged, not implemented)

- Add a real rate limiter (e.g. `flask-limiter`) to `/api/chat` if exposed beyond localhost.
- Set strict `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`, and `Permissions-Policy` response headers.
- Run `pip-audit` / `safety` in CI on every push.
- Consider a self-hosted geocoder (or an API-keyed provider) so the public Nominatim instance isn't a single point of failure.

## 3. Advanced tool ideas (not yet implemented)

These were considered for this pass but are scoped as follow-ups since each requires either new external data wiring, new tests, or both. Listed roughly in expected user value.

| Idea | What it does | Data source |
|------|--------------|-------------|
| `get_use_table` | Given a district, return permitted / special / not-allowed land uses. | Title 17 ch. 17-3, 17-4, 17-5 use tables. |
| `estimate_parking_requirement` | Given a district + use + sq ft (or unit count), compute minimum off-street parking. | Title 17 ch. 17-10. |
| `get_overlay_districts` | Return overlay zones (TOD, downtown design, pedestrian street, etc.) for a parcel. | `data.cityofchicago.org` — separate Socrata datasets. |
| `get_ward_and_alderman` | Map a parcel to its ward + alderman (useful for permits/zoning changes). | Chicago Data Portal `2024 Wards` dataset. |
| `get_landmark_status` | Whether a parcel is in a landmark district or is itself landmarked. | `data.cityofchicago.org/Landmarks`. |
| `get_floodplain_status` | FEMA flood zone for a parcel. | FEMA NFHL or city floodplain dataset. |
| `find_districts_meeting_criteria` | "Which districts allow ≥ 4 dwelling units on a 5,000 sq ft lot?" → filter `zoning_codes.csv`. | Already in repo (no new data needed — easy win). |
| `nearby_zoning` | Return adjacent block zoning around a coordinate (helpful for spot-zoning context). | Existing Socrata dataset, buffered query. |
| `get_pd_summary` | Look up Planned Development by ordinance number and return summary attributes. | Chicago Data Portal PD dataset. |
| `summarize_section` | LLM-summarize a Title 17 section with a deterministic citation footer. | Existing `sections.json`. |

Recommended next slice: **`find_districts_meeting_criteria`** (zero new data) and **`get_use_table`** (already-ingested Title 17 text). Both are pure additions, low risk, and would meaningfully increase agent capability.

## 4. Dependency / environment notes

- `pandas` removed from `pyproject.toml` (was unused).
- `marked` and `DOMPurify` are pinned in `index.html` with SRI hashes — bump them deliberately, not via floating versions.
- No other dependency updates were attempted in this pass.
