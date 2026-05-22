# Security Report — chicago-zoning-mcp

## Scan Summary
- **Scanned:** 2026-05-22
- **Tools run:** pip-audit, npm audit (N/A: no package.json), gitleaks (unavailable), trufflehog (unavailable), regex secret grep fallback, bandit, semgrep (skipped: no JS/TS files)
- **Status:** findings

## Findings

### Flask Debug Mode Enabled in App Runner
**Severity:** High
**Tool:** bandit
**Location:** web/app.py:220
**Description:** Bandit flagged that the Flask app is run with `debug=True`, which can expose the Werkzeug interactive debugger and enable arbitrary code execution paths if reachable in non-development contexts.
**Recommendation:** Ensure debug mode is disabled in all non-local runtime paths, default to `debug=False`, and gate any debug enablement behind explicit local-only environment checks.
**Status:** unresolved

### Flask App Binds to All Interfaces
**Severity:** Medium
**Tool:** bandit
**Location:** web/app.py:220
**Description:** Bandit reported host binding to `0.0.0.0`, which increases network exposure and can unintentionally publish development endpoints beyond localhost.
**Recommendation:** Restrict host binding to localhost for development by default, and only bind all interfaces when explicitly required and protected by deployment controls.
**Status:** unresolved

### XML Parsing of Potentially Untrusted Input (script)
**Severity:** Medium
**Tool:** bandit
**Location:** scripts/eval_live_web.py:58
**Description:** Bandit flagged `xml.etree.ElementTree.parse` usage as potentially vulnerable to XML parser abuse when handling untrusted XML.
**Recommendation:** Replace `xml.etree.ElementTree` parsing with `defusedxml` equivalents, or defensively validate/trust-boundary-constrain all XML inputs before parsing.
**Status:** unresolved

### URL Open Without Scheme Restriction
**Severity:** Medium
**Tool:** bandit
**Location:** scripts/eval_live_web.py:98
**Description:** Bandit reported `urlopen` usage without explicit scheme restrictions, which can permit unexpected schemes (for example, `file:`) if input is attacker-controlled.
**Recommendation:** Validate and allowlist schemes (for example, `http` and `https` only) before invoking URL fetch APIs.
**Status:** unresolved

### XML Parsing of Potentially Untrusted Input (test)
**Severity:** Medium
**Tool:** bandit
**Location:** tests/test_eval_xml.py:7
**Description:** Bandit flagged `xml.etree.ElementTree.parse` usage in tests as potentially vulnerable to XML attacks when parsing untrusted XML payloads.
**Recommendation:** Use `defusedxml` parser helpers in tests as well, so test code models secure parsing behavior and avoids normalizing unsafe parser usage.
**Status:** unresolved

## Remediation Notes
<!-- Squad: update Status above to "resolved" or "wontfix" after addressing. -->
