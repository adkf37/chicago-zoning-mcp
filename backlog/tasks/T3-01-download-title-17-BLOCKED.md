# T3-01 — Download Title 17 Raw Text (BLOCKED — Requires Human)

**Sprint tier:** 3 (Title 17 Ingestion)  
**Owner:** HUMAN  
**Status:** ❌ BLOCKED — requires manual human action  
**Priority:** Low (all other tools work without it)  
**Depends on:** Nothing (first step)

## Objective

Manually download the text of Title 17 of the Chicago Municipal Code (the Zoning
Ordinance) from American Legal Publishing and save chapter files to
`data/title_17/raw/`.

## Instructions

See `backlog/phase-05-code-text-search.md` for full step-by-step instructions.

1. Open [https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2610001](https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2610001)
2. For each chapter (17-1 through 17-17), select the full chapter text and save to
   `data/title_17/raw/chapter_17-N.txt` (e.g. `chapter_17-3.txt`).
3. After saving all chapters, run: `python scripts/ingest_title_17.py`
4. Validate: `python scripts/ingest_title_17.py --validate`

## Unblocks

- T3-02 (save files)
- T3-03 (run ingestion)
- T3-04 (validate)
- T3-05 (confirm search works)

## Notes

- Estimated effort: ~2 hours of manual copy-paste
- `search_zoning_code` and `get_zoning_section` return a friendly error until done
- All other 6 tools work normally without this step
