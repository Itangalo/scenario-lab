#!/usr/bin/env python3
"""Constraint interrogation for swedish-government-formation-2026 (Phase 3b).

Two independent tracks rule on the same edge cases from the drafted scenario
text alone. Divergence between tracks means the text underdetermines behavior.

Deliberately does not use scenario_lab's own LLM machinery: the point is an
audit of the prompt text, and reusing the framework's prompt assembly would
audit the framework instead.

Usage: OPENROUTER_API_KEY=... python3 interrogate.py [--models a,b]
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCENARIO = HERE.parent
API = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_MODELS = ["qwen/qwen3-235b-a22b-2507", "stealth/ox-alpha"]

SYSTEM = """You are auditing the text of a simulation scenario about Swedish government formation.

You will be shown the exact text that one actor in the simulation is given: the
constitutional rules, the shared starting context, and that actor's own briefing.
You will then be shown concrete situations.

For each situation, rule as that actor would, USING ONLY THE TEXT PROVIDED.
Do not use anything you know about Swedish politics from outside this text.
The question is not what is wise or likely. The question is what the provided
text determines.

Answer for each case with exactly one verdict:
  ALLOWED - the text permits this; the actor could do it without breaking a
            commitment it has made in the text
  BLOCKED - the text forbids this; doing it would break a commitment the text
            states
  UNCLEAR - the text genuinely does not determine it, and a careful reader
            could rule either way

UNCLEAR is a legitimate and useful answer. Do not force a verdict where the
text is silent or ambiguous. But do not use UNCLEAR merely because the
situation is politically delicate.

Respond with a JSON array and nothing else:
[{"id": "...", "verdict": "ALLOWED|BLOCKED|UNCLEAR", "quote": "the phrase in the text you are relying on, or NONE", "reason": "at most 25 words"}]
"""


def read(rel: str) -> str:
    return (SCENARIO / rel).read_text(encoding="utf-8")


def build_prompt(entry: dict) -> str:
    parts = [
        "## CONSTITUTIONAL RULES (given to every actor)\n",
        read("constitution.md"),
        "\n\n## SHARED STARTING CONTEXT (given to every actor)\n",
        read("background/context.md"),
        f"\n\n## BRIEFING FOR {entry['actor']} (this actor's own text)\n",
        read(f"background/actors/{entry['actor_file']}"),
        "\n\n## THE COMMITMENT UNDER EXAMINATION\n\n",
        # Name the topic only. Restating the intended wording here would let the
        # model rule from this prompt instead of from the actor's own briefing,
        # and the point is to test the briefing.
        entry["topic"],
        " Find what the text above says about it, and rule from that.",
        "\n\n## SITUATIONS TO RULE ON\n\n",
    ]
    for case in entry["cases"]:
        parts.append(f"{case['id']}: {case['text']}\n\n")
    return "".join(parts)


def call(model: str, prompt: str, retries: int = 3) -> str:
    body = json.dumps(
        {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
        }
    ).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                payload = json.load(resp)
            return payload["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError) as e:
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{model}: {last}")


def parse(text: str):
    """Extract the JSON array from a response that may carry prose or fences."""
    stripped = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE)
    match = re.search(r"\[.*\]", stripped, flags=re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS))
    ap.add_argument("--only", default=None, help="comma-separated constraint ids")
    args = ap.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    cases = json.loads((HERE / "edge-cases.json").read_text(encoding="utf-8"))
    if args.only:
        wanted = {c.strip() for c in args.only.split(",")}
        cases = {k: v for k, v in cases.items() if k in wanted}

    for model in models:
        slug = model.replace("/", "_")
        out_path = HERE / f"rulings-{slug}.json"
        results = json.loads(out_path.read_text()) if out_path.exists() else {}
        for cid, entry in cases.items():
            if cid in results:
                print(f"[{model}] {cid} cached", flush=True)
                continue
            print(f"[{model}] {cid} ...", flush=True)
            started = time.time()
            raw = call(model, build_prompt(entry))
            parsed = parse(raw)
            results[cid] = {
                "parsed": parsed,
                "raw": raw if parsed is None else None,
                "seconds": round(time.time() - started, 1),
            }
            out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
            status = "ok" if parsed else "PARSE FAILED"
            print(f"[{model}] {cid} {status} ({results[cid]['seconds']}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
