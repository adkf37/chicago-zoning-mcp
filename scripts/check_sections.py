import json, pathlib

data = json.loads(pathlib.Path("data/title_17/sections.json").read_text(encoding="utf-8"))
print(f"Total sections: {len(data)}")
print(f"Keys in first item: {list(data[0].keys())}")
print()
for item in data[:2]:
    sec = item.get("section", "?")
    title = item.get("title", "")[:60]
    chars = len(item.get("text", ""))
    print(f"  {sec}: {title}  ({chars} chars)")
    print("  Text snippet:", item.get("text", "")[:200].replace("\n", " "))
    print()
print("...")
for item in data[-2:]:
    sec = item.get("section", "?")
    title = item.get("title", "")[:60]
    chars = len(item.get("text", ""))
    print(f"  {sec}: {title}  ({chars} chars)")
    print("  Text snippet:", item.get("text", "")[:200].replace("\n", " "))
    print()
