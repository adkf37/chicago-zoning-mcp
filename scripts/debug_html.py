"""Test content extraction from codenav__section-body."""
import asyncio
from curl_cffi.requests import AsyncSession
from scripts.download_title_17 import _html_to_text

SECTION_NODE = "0-0-0-2684612"  # 17-17-0100 Use group and category descriptions

def extract_section_body(html: str) -> str:
    """Extract ordinance text from codenav__section-body, stopping before codenav__bottom."""
    # Find the content container
    marker = 'class="codenav__section-body"'
    idx = html.find(marker)
    if idx < 0:
        return ""
    # Move to just after the opening >
    tag_open = html.index(">", idx) + 1
    # Slice to before the bottom navigation
    for end_marker in ('class="codenav__bottom"', 'class="code-footer"'):
        end_idx = html.find(end_marker, tag_open)
        if end_idx > 0:
            return _html_to_text(f"<div>{html[tag_open:end_idx]}</div>")
    # Fallback: take up to 150 KB from section body start
    return _html_to_text(f"<div>{html[tag_open:tag_open + 150_000]}</div>")

async def main():
    async with AsyncSession(impersonate="chrome124") as s:
        await asyncio.sleep(1.5)
        r = await s.get(
            f"https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/{SECTION_NODE}",
            timeout=30,
        )
        html = r.text

        body = extract_section_body(html)
        print(f"Body chars: {len(body)}")
        print("--- First 600 chars ---")
        print(body[:600])

asyncio.run(main())
