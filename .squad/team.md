# Squad Team — chicago-zoning-mcp

| Name | Role | Charter |
|------|------|---------|
| Lead | Project coordinator, integration owner, phase gating | [charter](.squad/agents/lead/charter.md) |
| Data Engineer | Data loading, ingestion scripts, Socrata API, CSV pipeline | [charter](.squad/agents/data-engineer/charter.md) |
| Geo Developer | Geocoding, geospatial queries, Nominatim, spatial tools | [charter](.squad/agents/geo-developer/charter.md) |
| Tester | Unit tests, integration tests, eval Q&A, coverage | [charter](.squad/agents/tester/charter.md) |
| Scribe | Documentation, README, CONTRIBUTING, inline comments | [charter](.squad/agents/scribe/charter.md) |
| Ralph | Code review, security scanning, quality enforcement | [charter](.squad/agents/ralph/charter.md) |

## Roster Notes

- **Lead** gates phase transitions and owns final artifact assembly.
- **Data Engineer** and **Geo Developer** are the primary domain builders.
- **Tester** pairs with every implementation agent; tests ship with code.
- **Scribe** runs after each phase to keep docs current.
- **Ralph** reviews every PR before merge; his approval is required to close a phase.
