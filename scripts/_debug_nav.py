"""Debug: extract Jump links and section nodes from chapter TOC pages."""
import asyncio
import re
from curl_cffi.requests import AsyncSession

# Matches Jump links like: href="…/(0-0-0-XXXX)#JD_17-17-0100"
_JUMP_RE = re.compile(
    r'href="[^"]*/chicago_il/(0-0-0-\d+)#JD_(17-\d+-\d+)"',
    re.IGNORECASE,
)


async def debug():
    async with AsyncSession(impersonate="chrome124") as s:
        # Check chapter 17-17 and chapter 17-1 TOC pages
        for node, label in [("0-0-0-2684608", "Ch17-17"), ("0-0-0-2683170", "Ch17-11")]:
            await asyncio.sleep(1.5)
            r = await s.get(
                f"https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/{node}",
                timeout=30,
            )
            html = r.text
            jumps = _JUMP_RE.findall(html)
            print(f"\n=== {node} ({label}) — {len(html)} bytes HTML ===")
            print(f"Found {len(jumps)} Jump links:")
            seen_nodes = {}
            for content_node, section in jumps:
                seen_nodes.setdefault(content_node, []).append(section)
            for cn, secs in sorted(seen_nodes.items()):
                print(f"  {cn} → {secs[:3]}{'...' if len(secs) > 3 else ''} ({len(secs)} sections)")


asyncio.run(debug())




