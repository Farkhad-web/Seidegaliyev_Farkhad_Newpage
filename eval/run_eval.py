"""Tiny retrieval/answer-quality regression harness.

Not a unit test — it drives a *running* Chat With Your Docs instance over HTTP the same
way a real user would, so it also exercises ingestion, hybrid retrieval, and
the live Claude call end to end. Intended to be run by hand after a prompt
or retrieval-tuning change, to sanity-check nothing regressed, before it
becomes a real eval framework (see README "What's next").

Usage:
    docker compose up -d          # or run the backend locally
    pip install httpx
    python eval/run_eval.py [base_url]   # base_url defaults to http://localhost:8000
"""
import json
import sys
from pathlib import Path

import httpx

FIXTURES_DIR = Path(__file__).parent / "fixtures"
GOLDEN_PATH = Path(__file__).parent / "golden_qa.json"


def ensure_documents_indexed(client: httpx.Client, base_url: str) -> None:
    existing = {d["filename"] for d in client.get(f"{base_url}/api/documents").json()}
    for path in sorted(FIXTURES_DIR.glob("*.txt")):
        if path.name in existing:
            continue
        with open(path, "rb") as f:
            resp = client.post(f"{base_url}/api/documents", files={"file": (path.name, f, "text/plain")})
        resp.raise_for_status()
        print(f"  indexed {path.name}")


def ask(client: httpx.Client, base_url: str, question: str) -> tuple[str, list[dict], bool]:
    answer_parts: list[str] = []
    sources: list[dict] = []
    low_confidence = False
    with client.stream("POST", f"{base_url}/api/chat", json={"message": question}) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line.startswith("data:"):
                continue
            payload = json.loads(line[len("data:"):].strip())
            if payload["type"] == "sources":
                sources = payload["sources"]
                low_confidence = payload["low_confidence"]
            elif payload["type"] == "delta":
                answer_parts.append(payload["text"])
    return "".join(answer_parts), sources, low_confidence


def evaluate_case(case: dict, answer: str, sources: list[dict], low_confidence: bool) -> bool:
    if case.get("expect_refusal"):
        refusal_markers = ("don't have", "doesn't cover", "not covered", "no information")
        return low_confidence or any(m in answer.lower() for m in refusal_markers)
    keyword_hit = case["expect_keyword"].lower() in answer.lower()
    source_hit = any(case["expect_source_contains"] in s["filename"] for s in sources)
    return keyword_hit and source_hit


def main() -> None:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    cases = json.loads(GOLDEN_PATH.read_text())

    print(f"Target: {base_url}")
    with httpx.Client(timeout=60.0) as client:
        print("Ensuring fixture documents are indexed…")
        ensure_documents_indexed(client, base_url)

        print(f"\nRunning {len(cases)} cases…\n")
        passed = 0
        for case in cases:
            answer, sources, low_confidence = ask(client, base_url, case["question"])
            ok = evaluate_case(case, answer, sources, low_confidence)
            passed += ok
            status = "PASS" if ok else "FAIL"
            print(f"[{status}] {case['question']}")
            print(f"       -> {answer[:140].replace(chr(10), ' ')}")

        print(f"\n{passed}/{len(cases)} cases passed ({passed / len(cases):.0%})")
        if passed < len(cases):
            sys.exit(1)


if __name__ == "__main__":
    main()
