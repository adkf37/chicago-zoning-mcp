"""Ingest Title 17 of the Chicago Municipal Code into a section index.

This script parses the zoning ordinance text and creates a JSON index
at data/title_17/sections.json for use by the search_zoning_code tool.

Source: American Legal Publishing
https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2647389

Usage:
    python scripts/ingest_title_17.py           # Build the index
    python scripts/ingest_title_17.py --validate # Check an existing index

To download the raw text:
1. Go to: https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2647389
2. For each chapter (17-1 through 17-17), click through and copy the plain text.
3. Save each chapter as a .txt file in data/title_17/raw/
   e.g., data/title_17/raw/chapter_17-1.txt
4. Re-run this script.
"""

import argparse
import json
import re
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "title_17"
OUTPUT_FILE = OUTPUT_DIR / "sections.json"
RAW_DIR = OUTPUT_DIR / "raw"

# Maximum characters of child subsection text included in parent section aggregation
_MAX_CHILD_TEXT_LENGTH = 300

# Maximum number of numeric child sections to scan when aggregating section-group headers.
# Title 17 section groups (e.g. 17-2-0100, 17-2-0200) never contain more than ~15 direct
# numeric children, so 20 provides comfortable headroom without scanning too far forward.
_MAX_NUMERIC_CHILDREN = 20

# Boilerplate lines injected by amlegal.com's web interface
_BOILERPLATE_RE = re.compile(
    r"ShareDownloadBookmarkPrint|"
    r"Disclaimer:.*?American Legal Publishing.*?|"
    r"For further information.*?toll-free at 800-445-5588\.|"
    r"Hosted by: American Legal Publishing",
    re.IGNORECASE | re.DOTALL,
)


def _clean_text(raw: str) -> str:
    """Strip amlegal.com navigation and disclaimer boilerplate from section text."""
    cleaned = _BOILERPLATE_RE.sub("", raw)
    # Collapse runs of blank lines to at most two
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def parse_sections_from_text(text: str, source_file: str = "") -> list[dict]:
    """Parse Title 17 plain text into section entries.

    Handles section headers in the common amlegal.com formats, including
    indented subsections and letter-suffixed sub-items:
      17-1-0100  TITLE, PURPOSE AND APPLICABILITY
      17-1-0101  Title.
      Sec. 17-1-0101.  Title.
         17-1-0101-A  Sub-item text.
       17-1-0102 Another section.

    Returns list of {"section": "17-1-0101", "title": "...", "chapter": "...", "text": "..."}
    """
    # Match bare, "Sec." prefixed, and indented subsection headers.
    # Leading whitespace (spaces, tabs, non-breaking spaces \xa0 from amlegal.com)
    # is consumed but not captured so that indented subsections are also indexed.
    # Letter-suffixed sub-items like "17-15-0102-A" are also captured.
    section_pattern = re.compile(
        r"^\s*(?:Sec\.\s+)?(17-\d{1,2}-\d{4}(?:-[A-Za-z])?)\s*[.\s]+(.+?)$",
        re.MULTILINE,
    )

    matches = list(section_pattern.finditer(text))

    # Collect all candidate entries per section number, then keep the richest.
    # Each amlegal page repeats the section number in navigation before the
    # actual content, so there are typically 2 matches per section; we want
    # the one with the most body text.
    candidates: dict[str, dict] = {}

    for i, match in enumerate(matches):
        section_num = match.group(1).strip()
        # Normalize non-breaking spaces (\xa0) to regular spaces in the title line.
        # amlegal.com sometimes uses \xa0 as a sentence separator (e.g. "Title.\xa0Body..."),
        # which prevents the ". " split below from detecting the sentence boundary.
        raw_title = match.group(2).strip().replace("\xa0", " ")

        # Extract text until next section
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()

        # For single-line subsections the entire content is on the title line.
        # Split into a short title (first sentence up to the first period or
        # ~80 chars) and move the remainder into the body text if body is empty.
        first_dot = raw_title.find(". ")
        if body and first_dot == -1:
            # Multi-word title with no period — keep as-is
            title = raw_title.rstrip(".")
        elif first_dot != -1 and first_dot <= 80:
            title = raw_title[:first_dot].strip()
            remainder = raw_title[first_dot + 2 :].strip()
            if not body and remainder:
                body = remainder
        else:
            title = raw_title[:80].rstrip(" .,").rstrip(".")
            if not body and len(raw_title) > 80:
                body = raw_title[80:].strip()

        # Keep whichever occurrence has the most content
        existing = candidates.get(section_num)
        if existing is None or len(body) > len(existing["text"]):
            # Infer chapter from section number (17-X-XXXX → Chapter 17-X)
            parts = section_num.split("-")
            chapter = f"Chapter 17-{parts[1]}" if len(parts) >= 2 else ""
            candidates[section_num] = {
                "section": section_num,
                "title": title,
                "chapter": chapter,
                "text": _clean_text(body),
                "source_file": source_file,
            }

    # Return in document order (preserve first-seen order per section)
    seen_order: list[str] = []
    for match in matches:
        sec = match.group(1).strip()
        if sec not in seen_order:
            seen_order.append(sec)

    sections = []
    for sec in seen_order:
        entry = candidates.get(sec)
        if entry and (entry["text"] or entry["title"]):
            sections.append(entry)

    # Post-process: populate empty parent sections with text from their children.
    # e.g., 17-2-0104 (empty) gets summary text from 17-2-0104-A, -B, -C, etc.
    for section in sections:
        if section.get("text", "").strip():
            continue  # already has text

        parent_prefix = section["section"]
        # Collect direct child subsection text (letter-suffixed only: -A, -B, ...)
        child_texts = []
        for s in sections:
            sec_num = s["section"]
            if (
                sec_num.startswith(parent_prefix + "-")
                and len(sec_num) == len(parent_prefix) + 2  # exactly one letter suffix
                and s.get("text", "").strip()
            ):
                child_texts.append(f"({sec_num}) {s['text'][:_MAX_CHILD_TEXT_LENGTH]}")

        if child_texts:
            section["text"] = "\n".join(child_texts)

    # Post-process 2: populate empty section-group headers (sections ending in
    # a multiple of 100, e.g. 17-2-0100, 17-2-0200) with a list of their
    # numeric children's titles, so that get_zoning_section returns useful content
    # rather than an empty record.
    section_by_num = {s["section"]: s for s in sections}
    for section in sections:
        if section.get("text", "").strip():
            continue  # already has text

        parts = section["section"].split("-")
        if len(parts) < 3:
            continue
        try:
            base_num = int(parts[2])
        except ValueError:
            continue
        if base_num % 100 != 0:
            continue  # only process x00 header sections

        child_titles = []
        for i in range(1, _MAX_NUMERIC_CHILDREN + 1):
            child_key = f"{parts[0]}-{parts[1]}-{base_num + i:04d}"
            child = section_by_num.get(child_key)
            if child and child.get("title", "").strip():
                child_titles.append(f"({child_key}) {child['title']}")

        if child_titles:
            section["text"] = "Sections in this group:\n" + "\n".join(child_titles)

    # Post-process 3: use section title as text for any sections still empty.
    # This covers single-line list items (e.g. letter-suffix criteria like
    # "17-3-0502-A have a high concentration of...") and reserved placeholder
    # sections, ensuring every indexed section is keyword-searchable.
    for section in sections:
        if not section.get("text", "").strip() and section.get("title", "").strip():
            section["text"] = section["title"]

    return sections


def validate_index(index: list[dict]) -> list[str]:
    """Return a list of warning messages about index quality."""
    warnings = []

    if len(index) < 100:
        warnings.append(
            f"Only {len(index)} sections found — expected 100+. "
            "Some chapters may be missing from data/title_17/raw/."
        )

    # Check for duplicate section numbers
    seen: dict[str, int] = {}
    for entry in index:
        num = entry["section"]
        seen[num] = seen.get(num, 0) + 1
    dupes = {k: v for k, v in seen.items() if v > 1}
    if dupes:
        warnings.append(f"Duplicate section numbers ({len(dupes)}): {list(dupes)[:10]}")

    # Check all expected chapters are represented (chapter 1 requires the raw file)
    chapters_found = {e["section"].split("-")[1] for e in index if "-" in e["section"]}
    # Chapter 17-1 requires the raw file; only warn if other chapters are missing
    expected_chapters = {str(i) for i in range(2, 18)}
    missing = expected_chapters - chapters_found
    if missing:
        warnings.append(f"Chapters missing: {sorted(missing, key=int)}")
    if "1" not in chapters_found:
        warnings.append(
            "Chapter 17-1 (Title, Purpose, Definitions) is missing. "
            "Download chapter_17-1.txt from amlegal.com and re-run ingestion."
        )

    # Check for sections with no body text
    empty = [e["section"] for e in index if not e.get("text", "").strip()]
    if empty:
        warnings.append(f"{len(empty)} sections have no body text.")

    return warnings


def main():
    parser = argparse.ArgumentParser(description="Build or validate Title 17 section index.")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Check an existing sections.json instead of rebuilding.",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if args.validate:
        if not OUTPUT_FILE.exists():
            print(f"No index found at {OUTPUT_FILE}. Run without --validate to build it.")
            return
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            index = json.load(f)
        print(f"Index contains {len(index)} sections.")
        warnings = validate_index(index)
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  [WARN] {w}")
        else:
            print("Index looks good — no warnings.")
        return

    # --- Build mode ---
    raw_files = sorted(RAW_DIR.glob("*.txt"))
    if not raw_files:
        print("No raw text files found in data/title_17/raw/")
        print()
        print("To populate the index:")
        print("1. Go to: https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2647389")
        print("2. Copy the text of each chapter (17-1 through 17-17)")
        print("3. Save as .txt files in data/title_17/raw/")
        print("   e.g., data/title_17/raw/chapter_17-1.txt")
        print()
        print("Then re-run this script.")
        return

    all_sections: list[dict] = []
    seen_numbers: set[str] = set()

    for filepath in raw_files:
        print(f"Parsing {filepath.name}...")
        text = filepath.read_text(encoding="utf-8")
        sections = parse_sections_from_text(text, source_file=filepath.name)

        added = 0
        for section in sections:
            if section["section"] not in seen_numbers:
                seen_numbers.add(section["section"])
                all_sections.append(section)
                added += 1
            else:
                print(f"  Skipping duplicate: {section['section']}")

        print(f"  Found {len(sections)} sections, added {added}")

    # Validate before writing
    warnings = validate_index(all_sections)
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  [WARN] {w}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_sections, f, indent=2, ensure_ascii=False)

    print(f"\nWritten {len(all_sections)} sections to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

