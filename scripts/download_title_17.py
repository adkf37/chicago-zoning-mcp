#!/usr/bin/env python3
"""Download Title 17 (Chicago Zoning Ordinance) from codelibrary.amlegal.com.

Strategy
--------
Title 17's last document in the linear chain is the "Land Use and Zoning
Tables" appendix at node 0-0-0-2685160 (the predecessor of the Title 18 TOC
at 0-0-0-2685165).  Every amlegal page exposes a "Previous Doc" anchor that
links to the preceding document in reading order.  This script follows those
links backward through the entire Title 17 chapter sequence, then reassembles
the text in forward order and writes one file per chapter.

Usage
-----
    # Preview: fetch up to 10 pages, print summary, do NOT write files
    python scripts/download_title_17.py --dry-run

    # Full download (takes several minutes; run once)
    python scripts/download_title_17.py

    # Limit total pages fetched (useful for testing)
    python scripts/download_title_17.py --limit 40
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
import time
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path

from curl_cffi.requests import AsyncSession

# ──────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────

BASE_URL = "https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il"

# Last document in the Title 17 linear chain (the appendix cross-reference
# tables, which precede the Title 18 TOC at 0-0-0-2685165).
START_NODE = "0-0-0-2685160"

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "title_17" / "raw"

# Be polite: at least 1.5 s between requests
RATE_LIMIT = 1.5

USER_AGENT = "chicago-zoning-mcp/0.1 (educational, non-commercial)"

# Default maximum number of section pages to fetch in Phase 2
MAX_SECTIONS = 500

# ──────────────────────────────────────────────────────────
# Regex helpers
# ──────────────────────────────────────────────────────────

# Finds Previous/Next Doc navigation anchor in raw HTML.
# (Kept as a fallback; see _parse_nav() for the actual logic.)
_NAV_LINK = re.compile(
    r'href="[^"]*/(0-0-0-\d+)"[^>]*>\s*(?:<[^>]+>)?\s*(Previous|Next)\s*Doc',
    re.IGNORECASE,
)

# Title 17 section number (e.g. "17-3-0500")
_SEC17 = re.compile(r"\b17-\d+-\d+")

# Chapter heading inside content (e.g. "CHAPTER 17-4" or "Chapter 17-4:")
_CH17 = re.compile(r"\bCHAPTER\s+17-(\d+)\b", re.IGNORECASE)

# Generic title heading used to detect when we leave Title 17
_TITLE_HDG = re.compile(r"\bTITLE\s+(\d+)\b", re.IGNORECASE)

# Detect a Chapter-level heading for titles OTHER than 17
_CH_OTHER = re.compile(r"\bCHAPTER\s+(\d+)-\d+\b", re.IGNORECASE)

# amlegal "not found" pages redirect to the city overview with this marker
_NOT_FOUND_MARKER = "http://www.cityofchicago.org/"

# Section Jump links embedded in chapter TOC pages:
# href="…/chicago_il/0-0-0-XXXX#JD_17-Y-ZZZZ"
_JUMP_RE = re.compile(
    r'href="[^"]*/chicago_il/(0-0-0-\d+)#JD_(17-\d+-\d+)"',
    re.IGNORECASE,
)

# ──────────────────────────────────────────────────────────
# Lightweight HTML → plain-text converter
# ──────────────────────────────────────────────────────────

_BLOCK_TAGS = {
    "p", "div", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6",
    "li", "td", "th", "tr", "br", "hr",
}
_SKIP_TAGS = {"script", "style", "noscript"}


class _TextExtractor(HTMLParser):
    """Strip HTML tags, inject newlines at block elements."""

    def __init__(self) -> None:
        super().__init__()
        self._buf = StringIO()
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        tl = tag.lower()
        if tl in _SKIP_TAGS:
            self._skip_depth += 1
        elif tl in _BLOCK_TAGS and self._skip_depth == 0:
            self._buf.write("\n")

    def handle_endtag(self, tag: str) -> None:
        tl = tag.lower()
        if tl in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tl in _BLOCK_TAGS and self._skip_depth == 0:
            self._buf.write("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._buf.write(data)

    def get_text(self) -> str:
        return self._buf.getvalue()


def _html_to_text(html: str) -> str:
    ex = _TextExtractor()
    ex.feed(html)
    raw = ex.get_text()
    # Collapse runs of blank lines
    lines = [ln.rstrip() for ln in raw.splitlines()]
    cleaned: list[str] = []
    blank_run = 0
    for ln in lines:
        if ln:
            blank_run = 0
            cleaned.append(ln)
        else:
            blank_run += 1
            if blank_run <= 2:
                cleaned.append("")
    return "\n".join(cleaned)


def _extract_section_body(html: str) -> str:
    """Extract only the ordinance text from a section page.

    amlegal wraps the actual ordinance content in
    <div class="codenav__section-body">.  We slice from there to just before
    the bottom navigation so we avoid the TOC sidebar (which would otherwise
    pollute the text with every section number in the chapter).
    """
    marker = 'class="codenav__section-body"'
    idx = html.find(marker)
    if idx < 0:
        return ""
    # Move to just after the opening >
    tag_open = html.index(">", idx) + 1
    # Slice to before the bottom navigation div
    for end_marker in ('class="codenav__bottom"', 'class="code-footer"'):
        end_idx = html.find(end_marker, tag_open)
        if end_idx > 0:
            return _html_to_text(f"<div>{html[tag_open:end_idx]}</div>")
    # Fallback: take up to 150 KB from the body start
    return _html_to_text(f"<div>{html[tag_open:tag_open + 150_000]}</div>")


# ──────────────────────────────────────────────────────────
# Navigation-link extraction
# ──────────────────────────────────────────────────────────

# Next Doc: <a href="…/0-0-0-XXXX">Next Doc …
_NEXT_DOC_RE = re.compile(
    r'href="[^"]*/chicago_il/(0-0-0-\d+)"[^>]*>\s*Next\s*Doc',
    re.IGNORECASE,
)

# Previous Doc layout (SVG arrow icon sits BETWEEN the opening <a href> and
# the label text, so we search backwards from ">Previous Doc</a>"):
_PREV_DOC_TEXT_RE = re.compile(r">Previous Doc</a>", re.IGNORECASE)
_HREF_RE = re.compile(
    r'href="[^"]*/chicago_il/(0-0-0-\d+)"',
    re.IGNORECASE,
)


def _parse_nav(html: str) -> dict[str, str]:
    """Return {'Previous': node_id, 'Next': node_id} from raw HTML."""
    result: dict[str, str] = {}

    # Next Doc — text appears immediately after the closing > of the <a> tag
    m = _NEXT_DOC_RE.search(html)
    if m:
        result["Next"] = m.group(1)

    # Previous Doc — icon SVG sits between the opening <a href="…"> and the
    # label text, so we find the label text and look backwards for the href.
    # The SVG path data can be several KB long, so use a large window (15 KB).
    pm = _PREV_DOC_TEXT_RE.search(html)
    if pm:
        window = html[max(0, pm.start() - 15000) : pm.start()]
        # Find ALL href matches in the window and take the LAST one
        # (i.e. the href closest to ">Previous Doc</a>").
        matches = list(_HREF_RE.finditer(window))
        if matches:
            result["Previous"] = matches[-1].group(1)

    return result


def _extract_section_nodes(html: str) -> list[str]:
    """Return unique section-content node IDs from a chapter TOC page."""
    return list(dict.fromkeys(node for node, _ in _JUMP_RE.findall(html)))


# ──────────────────────────────────────────────────────────
# Page classification
# ──────────────────────────────────────────────────────────

def _classify(text: str) -> dict:
    """Return metadata about a page's content relevance."""
    head = text[:2000]  # look at the first ~2000 chars for headings

    ch17 = _CH17.search(head)
    ch_other = _CH_OTHER.search(head)
    title_m = _TITLE_HDG.search(head)
    has_sec17 = bool(_SEC17.search(text))

    chapter_num: int | None = int(ch17.group(1)) if ch17 else None
    other_title: int | None = None

    if title_m:
        t = int(title_m.group(1))
        if t != 17:
            other_title = t
    if ch_other:
        t = int(ch_other.group(1))
        if t != 17:
            other_title = t

    return {
        "chapter_num": chapter_num,
        "other_title": other_title,
        "has_sec17": has_sec17,
        "is_not_found": _NOT_FOUND_MARKER in text and not has_sec17,
    }


# ──────────────────────────────────────────────────────────
# Rate-limited HTTP fetch
# ──────────────────────────────────────────────────────────

_last_req: float = 0.0


async def _fetch(session: AsyncSession, node: str) -> tuple[str, str]:
    """Fetch a node page; return (html, plain_text)."""
    global _last_req
    wait = RATE_LIMIT - (time.monotonic() - _last_req)
    if wait > 0:
        await asyncio.sleep(wait)
    url = f"{BASE_URL}/{node}"
    resp = await session.get(url)
    resp.raise_for_status()
    _last_req = time.monotonic()
    html = resp.text
    text = _html_to_text(html)
    return html, text


# ──────────────────────────────────────────────────────────
# Phase 1: backward walk — collect chapter TOC nodes
# ──────────────────────────────────────────────────────────

async def traverse(
    session: AsyncSession, limit: int = 50
) -> list[tuple[str, int | None, str]]:
    """
    Walk backward from START_NODE collecting chapter-level TOC pages.

    Returns the list in REVERSE order (most-recent-first, i.e. Chapter 17-17
    first).  Caller should reverse it to get forward (reading) order.
    Each element is (node_id, chapter_num, html).
    """
    collected: list[tuple[str, int | None, str]] = []
    seen: set[str] = set()
    current = START_NODE

    while current and len(collected) < limit:
        if current in seen:
            print(f"  [warn] Cycle at {current} — stopping.")
            break
        seen.add(current)

        print(f"  {current} … ", end="", flush=True)
        try:
            html, text = await _fetch(session, current)
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            print(f"HTTP {status or 'network error'} — stopping.")
            break

        nav = _parse_nav(html)
        meta = _classify(text)

        if meta["is_not_found"] and not nav.get("Next"):
            print("not found — skipping.")
            current = nav.get("Previous")
            continue

        if meta["other_title"] is not None:
            print(f"Title {meta['other_title']} — reached end of Title 17, stopping.")
            break

        n_chars = len(text.strip())
        label = (
            f"Chapter 17-{meta['chapter_num']}" if meta["chapter_num"]
            else "appendix/header"
        )
        print(f"{n_chars:,} chars  [{label}]")

        collected.append((current, meta["chapter_num"], html))
        current = nav.get("Previous")

    return collected


# ──────────────────────────────────────────────────────────
# Phase 2: fetch section-content pages via Jump links
# ──────────────────────────────────────────────────────────

async def fetch_sections(
    session: AsyncSession,
    chapter_headers: list[tuple[str, int | None, str]],
    limit: int,
    dry_run: bool,
) -> dict[int, list[str]]:
    """
    For each chapter TOC page, extract Jump links and fetch the individual
    section-content pages that hold the actual ordinance text.
    Returns {chapter_num: [section_text, …]}.  Chapter 0 = appendix/preamble.
    """
    result: dict[int, list[str]] = {}
    total = 0

    for _node_id, ch_num, html in chapter_headers:
        key = ch_num if ch_num is not None else 0
        section_nodes = _extract_section_nodes(html)
        label = f"Chapter 17-{ch_num}" if ch_num else "Appendix"

        if not section_nodes:
            print(f"  {label}: no Jump links — skipping")
            continue

        # In dry-run, preview at most 2 sections per chapter
        fetch_nodes = section_nodes[:2] if dry_run else section_nodes
        suffix = f" (preview: {len(fetch_nodes)})" if dry_run else ""
        print(f"  {label}: {len(section_nodes)} section(s){suffix}")

        for sec_node in fetch_nodes:
            if total >= limit:
                print(f"  [limit] Reached {limit} sections — stopping.")
                return result
            print(f"    {sec_node} … ", end="", flush=True)
            try:
                sec_html, _full_text = await _fetch(session, sec_node)
            except Exception as exc:
                print(f"error ({exc}) — skipping.")
                continue
            # Use the section body extractor to get just the ordinance text,
            # avoiding the TOC sidebar that repeats all section numbers.
            sec_text = _extract_section_body(sec_html) or _full_text
            n_chars = len(sec_text.strip())
            print(f"{n_chars:,} chars")
            if n_chars > 100:
                result.setdefault(key, []).append(sec_text)
                total += 1

    total_secs = sum(len(v) for v in result.values())
    total_chars = sum(len(t) for v in result.values() for t in v)
    print(f"\n  {total_secs} sections collected, {total_chars:,} total chars")
    return result


# ──────────────────────────────────────────────────────────
# File writing
# ──────────────────────────────────────────────────────────

def _write_chapters(chapters: dict[int, list[str]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for ch_num in sorted(k for k in chapters if k > 0):
        content = "\n\n".join(chapters[ch_num])
        fname = OUTPUT_DIR / f"chapter_17-{ch_num:02d}.txt"
        fname.write_text(content, encoding="utf-8")
        kchars = len(content) // 1024
        print(f"  Wrote {fname.name}  ({kchars} KB)")
        written += 1

    if 0 in chapters:
        preamble = "\n\n".join(chapters[0])
        fname = OUTPUT_DIR / "title_17_header.txt"
        fname.write_text(preamble, encoding="utf-8")
        print(f"  Wrote title_17_header.txt  ({len(preamble) // 1024} KB)")
        written += 1

    print(f"\n  {written} file(s) written to {OUTPUT_DIR}/")


# ──────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────

async def main_async(dry_run: bool, limit: int, start_node: str = START_NODE) -> None:
    global START_NODE
    START_NODE = start_node
    print("Phase 1 — collecting chapter TOC nodes (backward traversal)")
    print(f"  Starting from : {START_NODE}")
    print(f"  Rate limit    : {RATE_LIMIT}s/request")
    if dry_run:
        print("  DRY RUN — files will NOT be written.")
    print()

    async with AsyncSession(impersonate="chrome124") as session:
        # Warm-up so the server can set session cookies
        try:
            await session.get(
                "https://codelibrary.amlegal.com/codes/chicago/latest/",
                timeout=30,
            )
            await asyncio.sleep(RATE_LIMIT)
            _last_req = time.monotonic()
        except Exception:
            pass

        headers_reversed = await traverse(session, limit=50)
        chapter_headers = list(reversed(headers_reversed))

        ch_nums = sorted(c for _, c, _ in chapter_headers if c is not None)
        print(f"\nPhase 1 complete: {len(chapter_headers)} TOC page(s) found")
        print(f"  Chapters: {ch_nums}")

        if not chapter_headers:
            print("No content found. Check network access.")
            sys.exit(1)

        print(f"\nPhase 2 — fetching section content ({limit} sections max)")
        print(f"  Rate limit: {RATE_LIMIT}s/request\n")

        content = await fetch_sections(
            session, chapter_headers, limit=limit, dry_run=dry_run
        )

    if not content:
        print("No section content collected. Check network access and try --dry-run.")
        sys.exit(1)

    if dry_run:
        print("\nDry-run preview (first section per chapter):")
        for ch in sorted(content):
            label = f"Chapter 17-{ch}" if ch else "Appendix"
            if content[ch]:
                snippet = content[ch][0].strip().splitlines()[0][:80]
                print(f"  {label}: {snippet}")
        print("\n(dry-run — no files written)")
        return

    print("\nWriting files …")
    _write_chapters(content)

    print("\nNext step:")
    print("  python scripts/ingest_title_17.py --validate")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch a few pages, print info, do NOT write files.",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=MAX_SECTIONS,
        metavar="N",
        help=f"Maximum section pages to fetch in Phase 2 (default: {MAX_SECTIONS}).",
    )
    ap.add_argument(
        "--start",
        default=START_NODE,
        metavar="NODE",
        help=f"Starting node ID (default: {START_NODE}).",
    )
    args = ap.parse_args()

    asyncio.run(main_async(args.dry_run, args.limit, args.start))


if __name__ == "__main__":
    main()
