# Decisions Log — chicago-zoning-mcp

> Significant architectural and data decisions are recorded here by the Lead.
> Format: `### YYYY-MM-DD — [Agent] — [Decision Title]`

### 2026-04-02 — Lead — Backlog organized as phase files, not individual task files

**Context:** The problem statement referenced `backlog/tasks/` as a directory of individual
task files. The actual backlog uses a flat `backlog/phase-0N-*.md` structure.

**Decision:** Treat each phase file as the canonical task specification for that phase.
Created `backlog/README.md` and `backlog/data_sources.md` as the missing cross-cutting
reference documents. No restructuring of existing phase files needed.

**Rationale:** The phase files contain sufficient task-level detail. Restructuring would
create unnecessary churn with no implementation benefit.

### 2026-04-02 — Lead — Title 17 ingestion is a human-gated step, not a code blocker

**Context:** `search_zoning_code` and `get_zoning_section` tools depend on
`data/title_17/sections.json`, which is built from manually downloaded text.

**Decision:** Mark Title 17 ingestion as BLOCKED on human action in both `STATUS.md` and
`.squad/sprint.md`. All other tools (Phases 2–4) work without it. The code-search tools
return a structured error with instructions when the index is absent.

**Rationale:** We cannot automate downloading from American Legal Publishing without
potentially violating their ToS. The helper script (`download_title_17.py`) attempts
scraping as a best-effort approach; if it fails, manual copy-paste is the fallback.

### 2026-04-02 — Lead — Sprint Tier structure separates automated from manual validation

**Context:** Sprint planning needed to distinguish tasks that automated agents can execute
from tasks requiring a human or local Ollama setup.

**Decision:** Organized `.squad/sprint.md` into 6 tiers:
- Tier 1: Offline automated tests (run immediately)
- Tier 2: Network integration tests
- Tier 3: Title 17 ingestion (human-gated)
- Tier 4: MCP Inspector manual verification
- Tier 5: Ollama end-to-end testing
- Tier 6: Documentation/fresh-clone verification

**Rationale:** Agents can immediately execute Tiers 1–2 without human involvement. Tiers
3–6 gate on human setup but should not block sprint progress for automated work.

### 2026-04-02 — Tester — Tier 1 offline tests executed and all pass

**Context:** Coder phase kicked off. First automated action was running the full offline test suite.

**Decision:** Treat a green `pytest tests/ -m "not network"` run as the official sprint Tier 1
completion gate. Result: 69 passed, 5 deselected (network tests marked with `@pytest.mark.network`).

**Rationale:** All 8 tools are registered and callable; all data-layer, tool-layer, and
integration assertions pass with real CSV data and lightweight mocks for external APIs.

### 2026-04-02 — Lead — .gitignore was missing from repo

**Context:** Phase 1 backlog listed `.gitignore` creation as a completed task, but the file
was absent from the repository. Running tests before the file existed caused `__pycache__`
directories to be tracked by git.

**Decision:** Create `.gitignore` covering Python artifacts (`__pycache__`, `*.pyc`, `.venv`,
`dist/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`), the gitignored data directory
(`data/title_17/`), and common editor/OS files. Remove previously tracked `__pycache__`
entries from git history.

**Rationale:** Without `.gitignore`, every test run pollutes the repo with compiled bytecode.
The `data/title_17/` exclusion is intentional per Phase 5 design — Title 17 raw text and the
generated `sections.json` index must not be committed (large files, manually downloaded).

