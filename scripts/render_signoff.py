"""Assemble prompt sign-off documents from a run's LLM transcripts.

A scenario is a pile of markdown that only matters insofar as it reaches a
prompt. Nothing in the pipeline tells you when it does not: `europe-2032`
carried 2,619 tokens of actor background -- the ten measure categories, the
rule that the Union cannot see which trajectory it is in -- that `load_actor`
silently dropped, and it went unnoticed through two thirty-run batches.

These documents are the check. They are not a reconstruction of what the
prompts probably look like; they are the bytes that were actually sent, taken
from the `--log-llm-io` transcripts, plus a coverage table showing which
headings of which source files survived the journey into them.

Usage:
    python -m scenario_lab.cli run scenarios/<name> --turns 2 --log-llm-io
    python scripts/render_signoff.py scenarios/<name>/runs/run-YYYYMMDD-HHMMSS

Writes to `scenarios/<name>/sign-off/` unless --out says otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

# The four prompts worth a human's signature, and why each one is here.
SIGNOFF_TASKS: list[tuple[str, int, str, str]] = [
    (
        "actor-turn-1",
        1,
        "actor",
        "The actor's opening prompt. Everything the actor will ever know about "
        "itself that is not carried by state passes through here. Read it "
        "against the actor's background file section by section.",
    ),
    (
        "actor-turn-2",
        2,
        "actor",
        "The same actor one turn later. The point of reading this next to "
        "turn 1 is the carry-forward: the statement ledger, the portfolio, the "
        "world state from turn 1, and the previous response. Anything that "
        "should persist between turns and does not appear here does not "
        "persist.",
    ),
    (
        "game-master-turn-2",
        2,
        "metrics",
        "The Game Master step that writes the world state. It decides what the "
        "actor's actions achieved and what the metrics become, so the metric "
        "rules must be visible here in full and unambiguous.",
    ),
    (
        "events-turn-2",
        2,
        "events",
        "The events step. Every event condition, gate and probability the "
        "world runs on is either in this prompt or is not enforced at all.",
    ),
]


def find_transcript(run_dir: Path, turn: int, task_prefix: str) -> Optional[Path]:
    """Return the first llm-io transcript for a task in a turn, if logged."""
    io_dir = run_dir / f"turn-{turn:02d}" / "llm-io"
    if not io_dir.is_dir():
        return None
    matches = sorted(p for p in io_dir.glob("*.md") if task_prefix in p.name)
    return matches[0] if matches else None


def split_transcript(text: str) -> dict[str, str]:
    """Split a saved transcript into its labelled blocks.

    The transcript wraps each prompt in a ``` fence, and the prompts themselves
    routinely contain fences -- the output format the actor must follow is
    given as a fenced example. So the fences cannot be matched as delimiters.
    Nor can ``## `` headings in general: the prompts carry their own, several of
    them. Only the three labels the transcript writer emits are safe anchors,
    and the outer fence is stripped as the first and last line between them.
    """
    sections: dict[str, str] = {}
    parts = re.split(r"^## (System prompt|User prompt|Raw response)$", text, flags=re.M)
    for i in range(1, len(parts) - 1, 2):
        label = parts[i].strip().lower()
        body = parts[i + 1].strip("\n").splitlines()
        if body and body[0].strip() == "```":
            body = body[1:]
        if body and body[-1].strip() == "```":
            body = body[:-1]
        sections[label] = "\n".join(body)
    return sections


def source_headings(path: Path) -> list[tuple[str, str]]:
    """Return (heading, first substantial line beneath it) for one markdown file."""
    out: list[tuple[str, str]] = []
    heading = "(top of file)"
    seeking = True
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            seeking = True
            continue
        if seeking and len(stripped) > 40 and not stripped.startswith(("|", "{#", "<!--")):
            out.append((heading, stripped))
            seeking = False
    return out


def normalise(text: str) -> str:
    """Collapse whitespace and markdown emphasis so prompt rendering survives comparison."""
    return re.sub(r"[\s*_`>-]+", " ", text).lower()


def coverage_table(scenario_dir: Path, haystack: str) -> list[str]:
    """Report which headings of which scenario source files reached the prompts."""
    haystack_norm = normalise(haystack)
    lines = [
        "| source file | heading | in a prompt |",
        "|---|---|---|",
    ]
    targets = sorted(
        list(scenario_dir.glob("background/**/*.md"))
        + list(scenario_dir.glob("*.md"))
    )
    for path in targets:
        if path.name.lower() in {"readme.md", "design-notes.md", "constraint-ledger.md"}:
            continue
        for heading, probe in source_headings(path):
            probe_norm = normalise(probe)[:60]
            present = probe_norm in haystack_norm
            rel = path.relative_to(scenario_dir)
            lines.append(f"| `{rel}` | {heading} | {'yes' if present else '**NO**'} |")
    return lines



def load_sources(scenario_dir: Path, repo: Path) -> list[tuple[str, str]]:
    """Return (label, text) for every file a prompt could have been built from.

    Scenario files come first, so that a scenario's own override is reported in
    preference to the shared template it replaces when both would match.
    """
    sources: list[tuple[str, str]] = []
    scenario_files = (
        sorted(scenario_dir.glob("*.md"))
        + sorted(scenario_dir.glob("background/**/*.md"))
        + sorted(scenario_dir.glob("user-prompts/*.md"))
        + sorted(scenario_dir.glob("variants/*.md"))
    )
    for path in scenario_files:
        label = f"`{path.relative_to(scenario_dir)}` (this scenario)"
        sources.append((label, path.read_text(encoding="utf-8")))
    for path in sorted((repo / "templates").glob("**/*.md")):
        label = f"`templates/{path.relative_to(repo / 'templates')}` (shared template)"
        sources.append((label, path.read_text(encoding="utf-8")))
    return sources


def attribute(block: str, sources: list[tuple[str, str]]) -> str:
    """Say where a rendered block came from, by matching its own longest lines.

    A prompt is a template with values interpolated into it, so a block is
    rarely byte-identical to any one file. Matching whole lines is enough to be
    certain and cheap enough to be honest about: a line of prose that appears
    verbatim in a source file came from it, and a block whose lines appear
    nowhere was assembled from scenario data rather than copied from a file.
    """
    lines = [line.strip() for line in block.splitlines() if len(line.strip()) > 45]
    if not lines:
        return "too short to attribute"
    probes = sorted(lines, key=len, reverse=True)[:8]
    best_label, best_hits = "", 0
    for label, text in sources:
        hits = sum(1 for probe in probes if probe in text)
        if hits > best_hits:
            best_label, best_hits = label, hits
    if not best_hits:
        return "assembled from scenario data (metrics, events, ledgers, run state) - not copied from any file"
    if best_hits == len(probes):
        return f"verbatim from {best_label}"
    return f"mostly from {best_label} ({best_hits} of {len(probes)} sampled lines matched verbatim; the rest are interpolated values or come from elsewhere)"


def annotate(prompt: str, sources: list[tuple[str, str]]) -> str:
    """Prefix each `## ` section of a rendered prompt with where it came from."""
    parts = re.split(r"^(#{1,3} .+)$", prompt, flags=re.M)
    out: list[str] = []
    if parts[0].strip():
        out.append(f"<!-- PROVENANCE: {attribute(parts[0], sources)} -->")
        out.append(parts[0].rstrip())
    for i in range(1, len(parts) - 1, 2):
        heading, body = parts[i], parts[i + 1]
        out.append("")
        out.append(f"<!-- PROVENANCE: {attribute(heading + body, sources)} -->")
        out.append(heading)
        out.append(body.rstrip())
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", help="Run directory produced with --log-llm-io")
    parser.add_argument("--out", default=None, help="Output directory (default: <scenario>/sign-off)")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    scenario_dir = run_dir.parent.parent
    out_dir = Path(args.out).resolve() if args.out else scenario_dir / "sign-off"
    out_dir.mkdir(parents=True, exist_ok=True)

    sources = load_sources(scenario_dir, REPO)
    all_prompts: list[str] = []
    written: list[tuple[str, str]] = []
    missing: list[str] = []

    for name, turn, task, why in SIGNOFF_TASKS:
        transcript = find_transcript(run_dir, turn, task)
        if transcript is None:
            missing.append(f"{name} (no `{task}` transcript in turn-{turn:02d}/llm-io/)")
            continue
        sections = split_transcript(transcript.read_text(encoding="utf-8"))
        system = sections.get("system prompt", "")
        user = sections.get("user prompt", "")
        all_prompts.append(system + "\n" + user)

        body = [
            f"# Sign-off: {name}",
            "",
            why,
            "",
            f"Source: `{transcript.relative_to(scenario_dir)}`. This is the prompt as sent, "
            "not a reconstruction. Regenerate after any change to the templates, the "
            "scenario's prompt overrides, or the background files.",
            "",
            "## Reviewer checklist",
            "",
            "- Every section of the actor and background files you expect is present below, not merely present in the file on disk",
            "- Nothing contradicts anything else: the scenario's own prompt overrides say the same thing as the templates they replace",
            "- No leakage: nothing here tells the actor something the scenario means it to infer",
            "- Numbers, thresholds and category names match the scenario definition exactly",
            "",
            "## Where each block came from",
            "",
            "Every section below is preceded by a `PROVENANCE` comment naming the file it "
            "was rendered from. `verbatim from` means the sampled lines appear unchanged in "
            "that file; `mostly from` means the block is that file with values interpolated "
            "into it; `assembled from scenario data` means no file contains it and it was "
            "built at run time from metrics, events, ledgers or run state. A scenario's own "
            "`user-prompts/` override is reported in preference to the shared template it "
            "replaces.",
            "",
            "## System prompt",
            "",
            annotate(system, sources),
            "",
            "## User prompt",
            "",
            annotate(user, sources),
            "",
        ]
        target = out_dir / f"{name}.md"
        target.write_text("\n".join(body), encoding="utf-8")
        written.append((name, str(target.relative_to(scenario_dir))))

    index = [
        "# Prompt sign-off",
        "",
        f"Generated from `{run_dir.name}`. These documents exist because a scenario file that never "
        "reaches a prompt changes nothing, and nothing else in the pipeline will tell you which "
        "ones those are.",
        "",
        "Read them once when the scenario is built, and again after any change to the templates, "
        "the scenario's prompt overrides, or the background files. Sign off by saying so in the "
        "scenario's design notes, with the date.",
        "",
        "## Documents",
        "",
    ]
    for name, rel in written:
        index.append(f"- [{name}]({name}.md) – `{rel}`")
    if missing:
        index += ["", "## Not generated", ""]
        index += [f"- {item}" for item in missing]
        index += [
            "",
            "Re-run the source run with `--log-llm-io` and at least two turns to fill these in.",
        ]

    index += [
        "",
        "## Source coverage",
        "",
        "Every heading in the scenario's background and definition files, and whether the text "
        "under it reached any of the prompts above. A **NO** is not automatically wrong, and "
        "there are three ordinary reasons for one. The heading may be documentation rather than "
        "instruction. Its content may reach the model through a different channel – an event's "
        "prose section is design rationale, while the operative text is the per-event "
        "`Condition:` and `Probability:` fields the events prompt renders from. Or it may belong "
        "to a mechanism that only becomes live in a later turn than the two sampled here, which "
        "these documents cannot show and whose absence proves nothing. What a **NO** must never "
        "be is unexamined: the failure this whole exercise exists to catch looks exactly like "
        "one of the three benign cases until you check.",
        "",
    ]
    index += coverage_table(scenario_dir, "\n".join(all_prompts))
    index.append("")

    (out_dir / "README.md").write_text("\n".join(index), encoding="utf-8")

    print(f"Wrote {len(written)} sign-off document(s) to {out_dir}")
    for item in missing:
        print(f"  missing: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
