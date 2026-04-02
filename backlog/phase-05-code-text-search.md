# Phase 5: Zoning Code Text Search

**Status:** Code complete — blocked on manual Title 17 download (human step)
**Depends on:** Phase 1
**Estimated scope:** M

## Objective

Ingest the full text of Title 17 (Chicago Zoning Ordinance) into a section-indexed JSON file
and implement keyword search, so the LLM can answer questions about specific regulations,
procedures, and definitions.

## Inputs

- `data/title_17/raw/chapter_17-N.txt` — raw plain-text chapter files (manually downloaded; gitignored)
- `src/data_loader.py` — `TITLE_17_INDEX` path constant

## Outputs

- `data/title_17/sections.json` — section index (gitignored); array of objects:
  ```json
  [{"section": "17-2-0100", "title": "...", "chapter": "Chapter 17-2", "text": "...", "source_file": "..."}]
  ```
- `src/tools/code_search.py` — `search_zoning_code` and `get_zoning_section` MCP tools

## Tasks

### Automated (code complete ✓)

- [x] Implement `scripts/ingest_title_17.py` parser for amlegal.com text format
  - Handles section numbering pattern `17-X-XXXX` (bare) and `Sec. 17-X-XXXX.` (with prefix)
  - Deduplication: keeps the occurrence with the most body text per section number
  - Per-chapter counts logged to stdout
  - `--validate` flag: reports section count, duplicates, missing chapters, empty sections
  - Graceful exit with instructions if `data/title_17/raw/` is empty
- [x] Implement `search_zoning_code` tool (`src/tools/code_search.py`)
  - Keyword tokenization (>2-character tokens, lowercased)
  - Frequency-based scoring across section title + text + chapter
  - Returns top N results (default 5, max 10), each truncated at 2000 chars
  - Returns structured error with hint if index not built
- [x] Implement `get_zoning_section` tool (`src/tools/code_search.py`)
  - Case-insensitive exact match on section number
  - Returns full section text (not truncated)
  - Returns helpful error if section not found or index not built
- [x] Unit tests (`tests/test_code_search.py`)
  - Fixture-based tests covering: keyword hit, no results, empty index, section lookup,
    invalid section number, max_results clamping

### Manual / Human-gated (BLOCKED)

- [ ] **[HUMAN STEP]** Download Title 17 text from American Legal Publishing
  - URL: https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2647389
  - Navigate each chapter (17-1 through 17-17) and copy the plain text
  - Save each as `data/title_17/raw/chapter_17-N.txt` (e.g., `chapter_17-1.txt`)
  - Estimated effort: ~2 hours (17 chapters, manual copy-paste required)
  - Alternative: Run the download helper: `python scripts/download_title_17.py` if the
    site allows automated scraping (check robots.txt / ToS first)
- [ ] **[BLOCKED]** Run ingestion after download:
  ```bash
  python scripts/ingest_title_17.py
  python scripts/ingest_title_17.py --validate
  # Should print: "Index contains 500+ sections."
  ```
- [ ] **[BLOCKED]** Smoke-test the built index:
  ```bash
  python scripts/smoke_test.py   # or run pytest tests/test_code_search.py -m network
  ```

## Key Files

| File | Owner | Status |
|------|-------|--------|
| `scripts/ingest_title_17.py` | Data Engineer | ✓ Complete |
| `scripts/download_title_17.py` | Data Engineer | ✓ Complete (helper) |
| `src/tools/code_search.py` | Data Engineer | ✓ Complete |
| `tests/test_code_search.py` | Tester | ✓ Complete |
| `data/title_17/raw/*.txt` | **Human** | ✗ Not downloaded (gitignored) |
| `data/title_17/sections.json` | Data Engineer | ✗ Not built (gitignored) |

## Acceptance Criteria

- [ ] Section index contains 500+ entries covering all 17 chapters of Title 17
- [x] `search_zoning_code("accessory dwelling unit")` returns relevant regulation sections
      *(verified with fixture data in unit tests)*
- [x] `search_zoning_code("FAR bonus")` finds floor area bonus provisions
      *(verified with fixture data in unit tests)*
- [x] Search returns within 100ms (JSON file small enough for in-memory keyword search;
      benchmarked with fixture data)
- [x] When index is not built, tools return a helpful error message (not a crash)
- [ ] `pytest tests/test_code_search.py` passes with real index data (post-download)

## Notes

- No vector embeddings needed. The zoning code is well-structured with numbered sections.
  Keyword search with section-level granularity is accurate and deterministic.
- If keyword search proves insufficient for fuzzy/conceptual queries, consider adding
  TF-IDF scoring (`scikit-learn`) as a lightweight upgrade — still no vector DB.
- American Legal Publishing may require manual copy-paste. Text is publicly available but
  bulk-download is not guaranteed. The `download_title_17.py` helper attempts scraping;
  if it fails, fall back to manual copy-paste. Plan for ~2 hours of manual work.
- Until the index is built, all other tools (Phases 2–4) work normally. Code search tools
  return a structured error directing the user to the ingestion instructions.
- **Workaround for CI/offline testing:** Unit tests use in-memory fixture data and never
  read from disk. All tests pass with `pytest tests/test_code_search.py` without the index.
