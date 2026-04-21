# T4-01–T4-10 — MCP Inspector Verification (Manual)

**Sprint tier:** 4 (MCP Inspector)  
**Owner:** Lead + Tester  
**Status:** ⏳ Pending — requires local toolchain (Node.js + Python)  
**Priority:** Medium  
**Depends on:** Nothing (all 8 tools are coded and registered)

## Objective

Verify that all 8 MCP tools are visible and callable in the MCP Inspector UI.

## Steps

```bash
# Terminal 1 — Start the server
python -m src.server

# Terminal 2 — Open inspector
npx @modelcontextprotocol/inspector python -m src.server
```

Then call each tool from the inspector UI and verify the response:

| # | Tool | Input | Expected |
|---|------|-------|----------|
| T4-03 | (all) | — | 8 tools appear in sidebar |
| T4-04 | `lookup_district` | `RS-3` | FAR 0.9, height 30 ft |
| T4-05 | `compare_districts` | `RS-3`, `RT-4` | RT-4 has higher FAR |
| T4-06 | `list_district_types` | `Residential` | List of RS/RT/RM/RT districts |
| T4-07 | `calculate_development_envelope` | `RS-3`, 5000 | 4500 sqft max floor area |
| T4-08 | `get_parcel_zoning` | `"233 S Wacker Dr"` | DC-16 (requires network) |
| T4-09 | `get_zoning_map_url` | — | gisapps.chicago.gov URL |
| T4-10 | `search_zoning_code` | `"parking"` | Helpful error (no index) |
| T4-10b | `get_zoning_section` | `"17-3-0102"` | Helpful error (no index) |

## Acceptance Criteria

- [ ] All 8 tools appear in MCP Inspector
- [ ] Each tool returns a structured dict (not an exception)
- [ ] `lookup_district("RS-3")` returns FAR 0.9
- [ ] `calculate_development_envelope("RS-3", 5000)` returns 4500 sqft
- [ ] `search_zoning_code` returns friendly error (not a crash)

## Notes

- Requires `Node.js` for `npx`; install via `nvm` or Homebrew
- Run from the root of the repository
