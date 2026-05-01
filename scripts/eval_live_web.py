"""Run evals/zoning_qa.xml against a live Chicago Zoning web app.

Usage:
    python scripts/eval_live_web.py --base-url https://chicago-zoning-mcp-702795562168.us-central1.run.app/
    python scripts/eval_live_web.py --base-url http://127.0.0.1:8000 --include-network
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_FILE = ROOT / "evals" / "zoning_qa.xml"


@dataclass
class EvalCase:
    id: str
    prompt: str
    answer: str
    answer_contains: list[str]
    answer_regex: list[str]
    expected_tools: list[str]
    requires_network: bool
    requires_index: bool
    question_type: str
    prompt_complexity: str
    audience: str
    data_source: str


def _text(node: ET.Element, name: str) -> str:
    child = node.find(name)
    if child is None or child.text is None:
        return ""
    return " ".join(child.text.split())


def _texts(node: ET.Element, name: str) -> list[str]:
    return [
        " ".join(child.text.split())
        for child in node.findall(name)
        if child.text and child.text.strip()
    ]


def load_cases(path: Path) -> list[EvalCase]:
    tree = ET.parse(path)
    cases: list[EvalCase] = []
    for node in tree.findall("question"):
        expected_tools = [
            item.strip()
            for item in _text(node, "expected_tools").split(",")
            if item.strip()
        ]
        tool = node.attrib.get("tool", "")
        if not expected_tools and tool and tool != "multi_step":
            expected_tools = [tool]
        cases.append(
            EvalCase(
                id=node.attrib["id"],
                prompt=_text(node, "prompt"),
                answer=_text(node, "answer"),
                answer_contains=_texts(node, "answer_contains"),
                answer_regex=_texts(node, "answer_regex"),
                expected_tools=expected_tools,
                requires_network=node.attrib.get("requires_network") == "true",
                requires_index=node.attrib.get("requires_index") == "true",
                question_type=node.attrib.get("question_type", node.attrib.get("type", "")),
                prompt_complexity=node.attrib.get("prompt_complexity", ""),
                audience=node.attrib.get("audience", ""),
                data_source=node.attrib.get("data_source", ""),
            )
        )
    return cases


def post_chat(base_url: str, prompt: str, timeout: float) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/api/chat"
    body = json.dumps({"question": prompt}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {"error": payload}
        data["_http_status"] = exc.code
        return data


def grade(case: EvalCase, data: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    answer = str(data.get("answer", ""))
    answer_lower = answer.lower()

    if data.get("error"):
        reasons.append(f"api error: {data.get('error')}")

    normalized_answer = answer_lower.replace(",", "")
    expected_texts = case.answer_contains or ([case.answer] if case.answer else [])
    for expected_text in expected_texts:
        normalized_expected = expected_text.lower().replace(",", "")
        if normalized_expected not in normalized_answer:
            reasons.append(f"missing expected text: {expected_text!r}")

    for pattern in case.answer_regex:
        if not re.search(pattern, answer, flags=re.IGNORECASE):
            reasons.append(f"missing expected pattern: {pattern!r}")

    used_tools = [call.get("name", "") for call in data.get("tool_calls", [])]
    for tool in case.expected_tools:
        if tool not in used_tools:
            reasons.append(f"missing expected tool: {tool}")

    return not reasons, reasons


def print_breakdown(results: list[dict[str, Any]], field: str, label: str) -> None:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        key = item.get("metadata", {}).get(field) or "unspecified"
        groups[key].append(item)
    if len(groups) <= 1:
        return

    print()
    print(f"By {label}:")
    for key in sorted(groups):
        items = groups[key]
        passed = sum(1 for item in items if item["passed"])
        print(f"  {key}: {passed}/{len(items)} passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="Live app URL, without /api/chat")
    parser.add_argument("--eval-file", type=Path, default=DEFAULT_EVAL_FILE)
    parser.add_argument("--include-network", action="store_true")
    parser.add_argument("--include-index", action="store_true")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--sleep", type=float, default=0.5)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    cases = load_cases(args.eval_file)
    results: list[dict[str, Any]] = []

    for case in cases:
        if case.requires_network and not args.include_network:
            print(f"SKIP Q{case.id}: requires network")
            continue
        if case.requires_index and not args.include_index:
            print(f"SKIP Q{case.id}: requires Title 17 index")
            continue

        started = time.perf_counter()
        data = post_chat(args.base_url, case.prompt, args.timeout)
        elapsed = time.perf_counter() - started
        passed, reasons = grade(case, data)
        status = "PASS" if passed else "FAIL"
        print(f"{status} Q{case.id} ({elapsed:.1f}s): {case.prompt}")
        for reason in reasons:
            print(f"  - {reason}")

        results.append(
            {
                "id": case.id,
                "prompt": case.prompt,
                "passed": passed,
                "reasons": reasons,
                "elapsed_seconds": round(elapsed, 3),
                "expected_tools": case.expected_tools,
                "metadata": {
                    "question_type": case.question_type,
                    "prompt_complexity": case.prompt_complexity,
                    "audience": case.audience,
                    "data_source": case.data_source,
                },
                "response": data,
            }
        )
        time.sleep(args.sleep)

    total = len(results)
    passed_count = sum(1 for item in results if item["passed"])
    print()
    print(f"Summary: {passed_count}/{total} passed")
    print_breakdown(results, "question_type", "question type")
    print_breakdown(results, "prompt_complexity", "prompt complexity")
    print_breakdown(results, "audience", "audience")

    if args.json_out:
        args.json_out.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Wrote {args.json_out}")

    return 0 if passed_count == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
