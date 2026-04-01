# Phase 5: Zoning Code Text Search

**Status:** Complete
**Depends on:** Phase 1
**Estimated scope:** M

## Objective

Ingest the full text of Title 17 (Chicago Zoning Ordinance) into a section-indexed JSON file and implement keyword search, so the LLM can answer questions about specific regulations, procedures, and definitions.

## Tasks

- [ ] Download Title 17 text from American Legal Publishing *(manual step — see Notes)*
  - Source: https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2647389
  - Save chapter-by-chapter as .txt files in `data/title_17/raw/`
- [x] Refine `scripts/ingest_title_17.py` parser for the actual text format
  - Handle section numbering: 17-X-XXXX
  - Handles both bare and `Sec.` prefixed headers (amlegal.com format)
  - Deduplication, per-chapter count, `--validate` flag, missing-chapter warnings
- [ ] Run ingestion → verify `data/title_17/sections.json` has 500+ sections *(blocked on manual download)*
- [x] Implement `search_zoning_code` tool
  - Keyword tokenization and scoring
  - Returns top N matching sections with context (truncated at 2000 chars)
- [x] Test with real queries (fixture-based unit tests cover all cases)
- [x] Added `get_zoning_section(section_number)` tool for direct section lookup

## Key Files

- `scripts/ingest_title_17.py` — one-time ingestion script
- `data/title_17/raw/*.txt` — raw chapter text (gitignored)
- `data/title_17/sections.json` — built index (gitignored)
- `src/tools/code_search.py` — search tool implementation

## Acceptance Criteria

- Section index contains 500+ entries covering all 17 chapters of Title 17
- `search_zoning_code("accessory dwelling unit")` returns relevant regulation sections
- `search_zoning_code("FAR bonus")` finds floor area bonus provisions
- Search returns within 100ms (JSON file is small enough for in-memory keyword search)

## Notes

- No vector embeddings needed. The zoning code is well-structured with numbered sections. Keyword search with section-level granularity is accurate and deterministic.
- If keyword search proves insufficient for fuzzy/conceptual queries, consider adding TF-IDF scoring (scikit-learn) as a lightweight upgrade — still no vector DB.
- American Legal Publishing may require manual copy-paste. The text is publicly available but not always easy to bulk-download. Plan for ~2 hours of manual work.
