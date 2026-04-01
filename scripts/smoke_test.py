"""Quick end-to-end smoke test of the MCP search tools."""
import sys
sys.path.insert(0, "src")
from tools.code_search import search_sections, get_section_by_number

results = search_sections("parking requirements residential")
print("Search: 'parking requirements residential'")
for item in results[:3]:
    sec = item["section"]
    title = item["title"]
    score = item["relevance_score"]
    chars = len(item["text"])
    print(f"  {sec}: {title}  (score={score}, {chars} chars)")

print()
r2 = get_section_by_number("17-9-0100")
if r2:
    print("Section 17-9-0100:", r2["title"])
    print("  Text (first 300):", r2["text"][:300].replace("\n", " "))
else:
    print("Section 17-9-0100: not found")
