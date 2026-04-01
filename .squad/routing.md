# Squad Routing — chicago-zoning-mcp

## Routing Table

| Work Type | Primary Agent | Secondary Agent |
|-----------|---------------|-----------------|
| Data loading, CSV pipeline, `data_loader.py` | Data Engineer | Lead |
| Socrata API, external HTTP calls | Data Engineer | Geo Developer |
| Title 17 ingestion script (`scripts/ingest_title_17.py`) | Data Engineer | Tester |
| Zoning code text search (`src/tools/code_search.py`) | Data Engineer | Tester |
| Geocoding, Nominatim, `src/geocoder.py` | Geo Developer | Data Engineer |
| Geospatial tools (`src/tools/geospatial.py`) | Geo Developer | Tester |
| District lookup tools (`src/tools/district_lookup.py`) | Data Engineer | Tester |
| Development envelope calculator (`src/tools/development.py`) | Data Engineer | Tester |
| FastMCP server wiring (`src/server.py`) | Lead | Data Engineer |
| Unit tests (`tests/`) | Tester | — |
| Integration tests (`tests/test_integration.py`) | Tester | Lead |
| Eval Q&A pairs (`evals/`) | Tester | Scribe |
| README, CONTRIBUTING, inline docs | Scribe | Lead |
| Dockerfile, docker-compose.yml | Lead | Data Engineer |
| Code review, security, quality | Ralph | Lead |
| Phase planning, STATUS.md updates | Lead | — |
| Decisions log (`.squad/decisions.md`) | Lead | Scribe |

## Routing Rules

1. **Default rule:** Route to Primary Agent. If Primary is blocked or unavailable, escalate to Secondary.
2. **Phase gates:** Lead reviews all work before marking a phase complete.
3. **Tests ship with code:** Tester is always CC'd when Data Engineer or Geo Developer opens work in `src/`.
4. **Docs follow code:** Scribe runs after each implementation phase to update README and inline comments.
5. **Ralph last:** Ralph reviews the final assembled PR. He does not block mid-phase work, but his sign-off is required before closing a phase.
6. **Parallel safe:** Data Engineer and Geo Developer may work concurrently on separate modules. Tester may write tests concurrently with implementation.
