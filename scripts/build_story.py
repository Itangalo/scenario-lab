"""Build the interactive reader for the europe-2032 branched story.

One self-contained HTML page: prose, the instrument readings behind it, and the
reader's choices. Data is embedded, so it needs no server. `story/tree/` is the
source; only nodes whose front matter says `status: written` are included, and
the page stops wherever the writing has got to.

The arm the reader is on — Acceleration, Verification-bound or Plateau — must
never be discoverable. Node names carry it in their first character, so every
node is addressed by an opaque digest and no branch id reaches the markup.

Usage:
    python scripts/build_story.py scenarios/europe-2032
    python scripts/build_story.py scenarios/europe-2032 --out /tmp/story.html
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

SALT = "europe-2032-reader"


def opaque(name: str) -> str:
    return "n" + hashlib.sha1((SALT + name).encode()).hexdigest()[:10]


def strip_front_matter(text: str) -> tuple[dict[str, str], str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta: dict[str, str] = {}
    if not m:
        return meta, text
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, text[m.end():]


def blocks(text: str) -> list[tuple[str, str]]:
    """(kind, html) per block: the small subset the prose actually uses."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    out: list[tuple[str, str]] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.strip()
        if not block:
            continue
        if re.fullmatch(r"(?:-{3,}|\*{3,}|_{3,})", block):
            out.append(("hr", "<hr>"))
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", block)
        if heading:
            level = len(heading.group(1))
            out.append(("h", f"<h{level + 1}>{inline(heading.group(2))}</h{level + 1}>"))
            continue
        lines = block.split("\n")
        if all(line.lstrip().startswith(">") for line in lines):
            out.append(("q", quote(lines)))
            continue
        if all(BULLET.match(line) for line in lines):
            items = "".join(f"<li>{inline(BULLET.sub('', line))}</li>" for line in lines)
            out.append(("ul", f"<ul>{items}</ul>"))
            continue
        out.append(("p", f"<p>{inline(block)}</p>"))
    return out


BULLET = re.compile(r"^\s*[-*]\s+")
SENDER = re.compile(r"^\*\*([^*:]+):\*\*\s*")
# The story follows one person; her own messages sit on the other side of the
# thread, the way they would on her phone.
PROTAGONIST = "Sofia"


def quote(lines: list[str]) -> str:
    """Clippings and text messages, both written as `>` blocks. A block whose
    first line opens with a bold name and a colon is a text thread; anything
    else is a run of dated clippings. Empty `>` lines separate the beats: one
    clipping, or one sender's consecutive messages."""
    body = [re.sub(r"^\s*>\s?", "", line) for line in lines]
    groups: list[list[str]] = [[]]
    for line in body:
        if line.strip():
            groups[-1].append(line.strip())
        elif groups[-1]:
            groups.append([])
    groups = [g for g in groups if g]
    if groups and SENDER.match(groups[0][0]):
        beats = []
        for group in groups:
            m = SENDER.match(group[0])
            who = m.group(1).strip() if m else ""
            cls = "beat me" if who == PROTAGONIST else "beat"
            msgs = "".join(f"<p>{inline(SENDER.sub('', line))}</p>" for line in group)
            beats.append(f'<div class="{cls}"><span class="who">{html.escape(who)}</span>{msgs}</div>')
        return f'<blockquote class="chat">{"".join(beats)}</blockquote>'
    beats = ["<div class=\"beat\">" + "".join(f"<p>{inline(line)}</p>" for line in group) + "</div>"
             for group in groups]
    return f'<blockquote class="clip">{"".join(beats)}</blockquote>'


def markdown(text: str) -> str:
    return "\n".join(html_ for _, html_ in blocks(text))


MEMO_HEADING = "Note to the President"


def split_turn(text: str) -> dict[str, str]:
    """Lift the headline out of a turn so the chapter header can carry the
    date alongside it, the way `split_choice` lifts one off a choice page.

    Sofia's note to the President is a document inside the story, not more
    narration, so it is set as one: everything from its heading to the next
    heading goes into a memo box, with the dateline and the President's
    reply in the margin picked out."""
    parts = blocks(text)
    title, body = "", []
    memo: list[str] | None = None
    for kind, html_ in parts:
        if not title and kind == "h":
            title = re.sub(r"</?h\d>", "", html_)
            continue
        if kind == "h":
            if memo is not None:
                body.append('<div class="memo">' + "".join(memo) + "</div>")
                memo = None
            label = re.sub(r"</?h\d>", "", html_)
            if label == MEMO_HEADING:
                memo = [f'<p class="memo-label">{label}</p>']
                continue
        if memo is not None:
            if kind == "p" and html_.startswith("<p><em>From "):
                html_ = '<p class="memo-from">' + html_[3:]
            elif kind == "p" and html_.startswith("<p><em>In the margin"):
                html_ = '<p class="memo-margin">' + html_[3:]
            memo.append(html_)
            continue
        body.append(html_)
    if memo is not None:
        body.append('<div class="memo">' + "".join(memo) + "</div>")
    return {"title": title, "html": "\n".join(body)}


MONTHS = {"H1": "January\u2013June", "H2": "July\u2013December"}


def months(period: str) -> str:
    """`H1 2027` reads as a convention the page never explains; a reader wants
    the months. Presentation only — the underlying field is untouched."""
    m = re.match(r"(H[12])\s+(\d{4})", period or "")
    return f"{MONTHS[m.group(1)]} {m.group(2)}" if m else (period or "")


def split_choice(text: str) -> dict[str, str]:
    """A choice card is a headline, the measure it commits to, a lead
    paragraph, the rest behind an expander, and the draw counts."""
    parts = blocks(text)
    title = next((h for k, h in parts if k == "h"), "")
    paras = [h for k, h in parts if k == "p"]
    meta = ""
    if paras and paras[0].startswith("<p><strong>"):
        meta = paras.pop(0)
    signal = ""
    if paras and re.fullmatch(r"<p><em>.*</em></p>", paras[-1], re.S):
        signal = paras.pop()
    lead_sentence = ""
    if paras:
        # `paras` is already escaped; unescape before escaping again, or an
        # apostrophe reaches the page as a literal `&#x27;`.
        plain = html.unescape(re.sub(r"<[^>]+>", "", paras[0]))
        m = re.match(r"(.+?[.!?])(?:\s|$)", plain, re.S)
        lead_sentence = html.escape(m.group(1).strip()) if m else html.escape(plain[:180])
    return {"title": title, "meta": meta, "lead": lead_sentence,
            "rest": "\n".join(paras), "signal": signal}


def inline(text: str) -> str:
    text = html.escape(text)
    # Links before emphasis: the preamble and postamble are authored by hand and
    # will contain them, and a raw [label](url) on the page is a visible defect.
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                  r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", text)
    return text.replace("\n", " ")


def load_nodes(tree_dir: Path) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for node_dir in sorted(tree_dir.iterdir()):
        if not node_dir.is_dir():
            continue
        data_path = node_dir / "data.json"
        if not data_path.is_file():
            continue
        prose_path = node_dir / ("choice.md" if (node_dir / "choice.md").is_file()
                                 else "narrative.md")
        if not prose_path.is_file():
            continue
        meta, body = strip_front_matter(prose_path.read_text(encoding="utf-8"))
        if meta.get("status") != "written":
            continue
        is_choice = prose_path.name == "choice.md"
        nodes[node_dir.name] = {
            "data": json.loads(data_path.read_text(encoding="utf-8")),
            "html": markdown(body),
            "parts": split_choice(body) if is_choice else split_turn(body),
            "is_choice": is_choice,
        }
    return nodes


def sim_data(data: dict[str, Any]) -> dict[str, Any]:
    """What "Simulation data" opens for a half-year: the run's own record,
    outside the story. Measure descriptions are left out – they are the
    actor's shorthand, metric ids and all – and nothing here names the arm.
    Finished measures pile up in the portfolio for good, so only the ones
    finishing this half-year are listed."""
    turn = data.get("turn")
    measures = []
    for p in data.get("portfolio") or []:
        status = p.get("status")
        if status == "new":
            label = "started this half-year"
        elif status == "running":
            due = p.get("finish_period")
            label = f"running, due to finish in {due}" if due else "running"
        elif status == "finished" and p.get("finish") == turn:
            label = "finished this half-year"
        else:
            continue
        measures.append({"name": html.escape(p.get("name", "")), "status": label})
    for c in data.get("cancelled") or []:
        name = c if isinstance(c, str) else (c.get("name") or "")
        if name:
            measures.append({"name": html.escape(name), "status": "cancelled"})
    priority = re.sub(r"^M\d+\s+|\s*\(M\d+\)\s*$", "", data.get("priority") or "")
    return {
        "measures": measures,
        "priority": html.escape(priority),
        "commitment": html.escape(data.get("commitment") or ""),
    }


def build_payload(nodes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name, node in nodes.items():
        data, nid = node["data"], opaque(name)
        entry: dict[str, Any] = {
            "kind": "choice" if node["is_choice"] else "turn",
            "html": node["html"],
        }
        if node["is_choice"]:
            entry.update(node["parts"])
            entry["period"] = data.get("period_prose", "")
            targets = data.get("next_node") or []
            if isinstance(targets, str):
                targets = [targets]
            live = [opaque(t) if t in nodes else None for t in targets]
            entry["nextByArm"] = live if len(live) > 1 else None
            entry["next"] = live[0] if len(live) == 1 else None
        else:
            entry["turn"] = data.get("turn")
            entry["title"] = node["parts"].get("title", "")
            entry["html"] = node["parts"].get("html", entry["html"])
            entry["period"] = months(data.get("period", ""))
            entry["periodProse"] = data.get("period_prose", "")
            entry["metrics"] = [
                {"label": m["label"], "value": m["value"], "delta": m["delta"]}
                for m in (data.get("metrics") or {}).values()
            ]
            entry["events"] = [
                {"title": html.escape(e["title"]),
                 "description": re.sub(r"`([^`]+)`", r"<code>\1</code>", inline(e["description"]))}
                for e in (data.get("events") or [])
            ]
            entry["sim"] = sim_data(data)
            nxt = data.get("next_node")
            entry["next"] = opaque(nxt) if nxt and nxt in nodes else None
            choices = data.get("next_choice") or []
            live_choices = [opaque(c) for c in choices if c in nodes]
            entry["choices"] = live_choices or None
        payload[nid] = entry
    return payload


HEAD = """<title>Europe 2032</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,600&family=Spectral:wght@300;400;600&family=IBM+Plex+Mono:wght@400;500&family=Caveat:wght@500&display=swap">
<style>
:root {
  --ground: #eef1f2;
  --surface: #ffffff;
  --ink: #12181a;
  --muted: #57646a;
  --faint: #8a979c;
  --rule: #d5dcde;
  --track: #dfe6e8;
  --accent: #0f5d6b;
  --accent-soft: #e3eff0;
  --up: #2f6b4f;
  --down: #a8412f;
  --measure: 34rem;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ground: #0e1416; --surface: #151d20; --ink: #e7edee; --muted: #97a6ab;
    --faint: #6c7c81; --rule: #243135; --track: #1f2c30; --accent: #5cb8b2;
    --accent-soft: #16302f; --up: #6fbb92; --down: #d98771;
  }
}
:root[data-theme="dark"] {
  --ground: #0e1416; --surface: #151d20; --ink: #e7edee; --muted: #97a6ab;
  --faint: #6c7c81; --rule: #243135; --track: #1f2c30; --accent: #5cb8b2;
  --accent-soft: #16302f; --up: #6fbb92; --down: #d98771;
}
* { box-sizing: border-box; }
/* `.layout` sets `display: grid`, which would beat the user-agent rule for
   `hidden` and leave the inactive tab panel on screen. */
[hidden] { display: none !important; }
body {
  margin: 0; background: var(--ground); color: var(--ink);
  font-family: Spectral, Georgia, "Times New Roman", serif;
  font-size: 19px; line-height: 1.62; -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 72rem; margin: 0 auto; padding: 0 1.5rem 5rem; }
header.masthead {
  border-bottom: 1px solid var(--rule);
  padding: 2.25rem 0 1.1rem; display: flex; flex-wrap: wrap;
  align-items: baseline; gap: 0.6rem 1.25rem;
}
/* The tellings of the same material, side by side under the masthead. */
.tabs { display: flex; flex-wrap: wrap; gap: 0.35rem; padding-top: 0.9rem; margin-bottom: 2.5rem; }
.tab {
  font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  font-size: 0.68rem; letter-spacing: 0.08em; text-transform: uppercase;
  background: transparent; color: var(--muted);
  border: 1px solid transparent; border-radius: 2px;
  padding: 0.5rem 0.9rem; cursor: pointer;
}
.tab:hover { color: var(--accent); }
.tab[aria-selected="true"] {
  color: var(--accent); background: var(--surface); border-color: var(--rule);
}
.tab:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
/* The alternative telling is linear, so there is no half-year to report and
   no panel to report it in. It keeps the reading column and nothing else. */
.altview:focus { outline: none; }
.altview article h2 { margin-top: 0; }
.altview article h3 {
  color: var(--accent); font-size: 1.15rem; margin: 2.6rem 0 0.7rem;
}
.altview article hr {
  border: 0; border-top: 1px solid var(--rule); margin: 3.5rem 0;
}
body:not([data-view="story"]) .restart.floating { display: none; }
.masthead h1 {
  font-family: Newsreader, Georgia, serif; font-weight: 600;
  font-size: 1.5rem; letter-spacing: -0.01em; margin: 0;
}
.mono, .sub, .cap, .dial b, button, .events summary {
  font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}
.sub { font-size: 0.72rem; letter-spacing: 0.09em; text-transform: uppercase; color: var(--faint); }
.restart {
  font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  font-size: 0.68rem; letter-spacing: 0.07em; text-transform: uppercase;
  background: transparent; color: var(--muted); border: 1px solid var(--rule);
  border-radius: 2px; padding: 0.5rem 0.8rem; cursor: pointer; width: 100%;
}
.restart:hover { color: var(--accent); border-color: var(--accent); }
/* Wide screens read it in the sticky panel; narrow screens stack the panel
   below the prose, where it would scroll away, so a fixed one takes over. */
.restart.floating { display: none; }
@media (max-width: 62rem) {
  aside .restart { display: none; }
  .restart.floating {
    display: block; position: fixed; right: 1rem; bottom: 1rem; width: auto;
    z-index: 5; background: var(--surface); box-shadow: 0 2px 10px rgba(0,0,0,0.12);
  }
}

/* Starting over re-rolls which of the three worlds you are in, so the page
   comes apart rather than simply swapping. Only what is on screen performs:
   the reader cannot see the rest, and splitting a whole long column into
   characters would stall the click. Transform and opacity only — a blur per
   character across a screenful of prose is what would actually jank. */
.dissolving { pointer-events: none; }
/* Characters are inline-block so they can be transformed, which would let a
   line break fall between any two of them and re-wrap the paragraph the moment
   it shatters. Keeping each word in a nowrap box preserves the original line
   breaks; spaces stay ordinary text nodes so wrapping behaves normally. */
.wd { display: inline-block; white-space: nowrap; }
.ch { display: inline-block; }
@keyframes letter {
  20% { opacity: 1; }
  to { opacity: 0; transform: translateY(-38px) rotate(var(--tilt)); }
}
.fade-block { animation: dissolve 900ms ease-in forwards; }
@keyframes dissolve {
  to { opacity: 0; transform: translateY(-16px); filter: blur(5px); }
}
/* The world that replaces it should arrive, not blink into existence. */
/* Beats the per-chapter `rise` further down, which is shorter and would
   otherwise win on source order and snap the story in under the preamble. */
#stream.arriving > * { animation: arrive 900ms ease-out backwards; }
#stream.arriving > *:nth-child(2) { animation-delay: 180ms; }
@keyframes arrive {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: none; }
}
@media (prefers-reduced-motion: reduce) {
  .ch, .fade-block, #stream.arriving > * { animation: none !important; }
}
.rail { display: flex; gap: 3px; align-items: center; justify-content: center; padding-top: 0.25rem; }
.rail i { display: block; width: 14px; height: 3px; border-radius: 1px; background: var(--track); }
.rail i.done { background: var(--accent); opacity: 0.45; }
.rail i.now { background: var(--accent); height: 8px; opacity: 1; }
.layout { display: grid; grid-template-columns: minmax(0, 1fr) 17.5rem; gap: 3.5rem; align-items: start; }
aside { position: sticky; top: 1.5rem; display: flex; flex-direction: column; gap: 1.25rem; }
.chapter { padding-bottom: 3.5rem; }
.chapter + .chapter { border-top: 1px solid var(--rule); padding-top: 3rem; }
.note.preamble { margin-bottom: 3.5rem; }
.note.preamble h2 {
  font-family: Newsreader, Georgia, serif; font-weight: 600; font-size: 1.15rem;
  color: var(--ink); margin: 0 0 0.9rem;
}
.note.preamble p { margin: 0 0 0.9rem; }
.note.preamble p:last-child { margin-bottom: 0; }
.note.end { margin: 2rem 0 0; }
.note.end h2, .note.draft h2 {
  font-family: Newsreader, Georgia, serif; font-weight: 600; font-size: 1.15rem;
  color: var(--ink); margin: 0 0 0.9rem;
}
.note.end p { margin: 0 0 0.9rem; }
.note.end p:last-child { margin-bottom: 0; }
.note.draft {
  margin: 2rem 0 0; background: transparent; border-style: dashed;
  font-size: 0.9rem;
}
.chapter-title .when { color: var(--accent); font-weight: 400; }
article { max-width: var(--measure); }
article h2 {
  font-family: Newsreader, Georgia, serif; font-weight: 600; font-size: 2rem;
  line-height: 1.18; letter-spacing: -0.015em; text-wrap: balance; margin: 0 0 1.5rem;
}
article h3 {
  font-family: Newsreader, Georgia, serif; font-weight: 600; font-size: 1.1rem;
  margin: 2.2rem 0 0.6rem; color: var(--muted);
}
article p { margin: 0 0 1.15rem; }
article p:last-child { margin-bottom: 0; }
article em { color: var(--muted); }
article ul { margin: 0 0 1.15rem; padding-left: 1.25rem; }
article li { margin: 0 0 0.45rem; }
/* Dated clippings: the events that need only a clause, set like a wire. */
article blockquote { margin: 1.7rem 0; }
article blockquote.clip {
  border-left: 3px solid var(--accent); padding: 0.15rem 0 0.15rem 1rem;
  font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  font-size: 0.8rem; line-height: 1.55; color: var(--muted);
}
article blockquote.clip .beat + .beat { margin-top: 0.85rem; }
article blockquote.clip p, article blockquote.chat p { margin: 0; }
article blockquote.clip strong { color: var(--ink); font-weight: 500; }
/* Text threads: one bubble per sender's run of messages; Sofia on the right. */
article blockquote.chat {
  display: flex; flex-direction: column; gap: 0.5rem;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 0.86rem; line-height: 1.45;
}
article blockquote.chat .beat {
  align-self: flex-start; max-width: 82%;
  background: var(--surface); border: 1px solid var(--rule); border-radius: 14px;
  padding: 0.45rem 0.85rem 0.55rem;
}
article blockquote.chat .beat.me { align-self: flex-end; background: var(--accent-soft); }
article blockquote.chat .who {
  display: block; font-size: 0.66rem; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--faint); margin-bottom: 0.15rem;
}
/* Sofia's note to the President: a document laid into the story, set as
   paper rather than narrated, with the President's reply in hand. */
article .memo {
  margin: 2.6rem 0 0; padding: 1.4rem 1.5rem 1.5rem;
  background: var(--surface); border: 1px solid var(--rule);
  border-top: 3px solid var(--accent); border-radius: 2px;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 0.9rem; line-height: 1.55;
}
article .memo p { margin: 0 0 0.8rem; }
article .memo ul { margin: -0.3rem 0 1rem; }
article .memo li { margin: 0 0 0.35rem; }
article .memo .memo-label {
  font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  font-size: 0.68rem; letter-spacing: 0.11em; text-transform: uppercase;
  color: var(--accent); margin: 0 0 0.35rem;
}
article .memo .memo-from {
  font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  font-size: 0.72rem; line-height: 1.5; color: var(--faint);
  padding-bottom: 0.9rem; border-bottom: 1px solid var(--rule); margin-bottom: 1.1rem;
}
article .memo .memo-from em { font-style: normal; color: inherit; }
article .memo .memo-margin {
  margin: 1.4rem 0 0; padding-top: 0.9rem; border-top: 1px dashed var(--rule);
  font-family: Caveat, "Bradley Hand", "Segoe Print", cursive;
  font-size: 1.4rem; line-height: 1.3; color: var(--accent);
}
article .memo .memo-margin em {
  display: block; margin-bottom: 0.25rem;
  font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  font-size: 0.62rem; line-height: 1.4; letter-spacing: 0.1em; text-transform: uppercase;
  font-style: normal; color: var(--faint);
}
.panel { background: var(--surface); border: 1px solid var(--rule); border-radius: 2px; padding: 1.1rem 1.1rem 1.25rem; }
.cap { font-size: 0.65rem; letter-spacing: 0.11em; text-transform: uppercase; color: var(--faint); margin: 0 0 1rem; }
.dials { display: grid; grid-template-columns: 1fr 1fr; gap: 1.1rem 0.5rem; }
.dial { display: flex; flex-direction: column; align-items: center; gap: 0.35rem; }
.dial svg { display: block; }
.dial .track { stroke: var(--track); }
.dial .fill { stroke: var(--accent); transition: stroke-dasharray 0.45s cubic-bezier(0.4, 0, 0.2, 1); }
@media (prefers-reduced-motion: reduce) { .dial .fill { transition: none; } }
.dial b {
  font-size: 0.6rem; font-weight: 400; letter-spacing: 0.04em; color: var(--muted);
  text-align: center; line-height: 1.3;
}
.dial b i { font-style: normal; margin-left: 0.15rem; }
.dial b i.up { color: var(--up); }
.dial b i.down { color: var(--down); }
/* The arcs carry a reading but never say what the reading is of. Each dial
   explains itself on hover and on keyboard focus; the text is authored in
   story/dial-tips.md, not here. */
.dial { position: relative; }
.dial:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; border-radius: 3px; }
.dial .tip {
  position: absolute; bottom: calc(100% + 8px); left: 50%;
  transform: translateX(-50%) translateY(3px);
  width: max-content; max-width: 12.5rem;
  background: var(--ink); color: var(--ground);
  font-family: Spectral, Georgia, serif; font-size: 0.78rem; line-height: 1.45;
  letter-spacing: 0; text-align: left; text-transform: none;
  padding: 0.5rem 0.65rem; border-radius: 2px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
  opacity: 0; visibility: hidden; pointer-events: none;
  transition: opacity 140ms ease, transform 140ms ease;
  z-index: 20;
}
.dial:hover .tip, .dial:focus-visible .tip {
  opacity: 1; visibility: visible; transform: translateX(-50%) translateY(0);
}
@media (prefers-reduced-motion: reduce) { .dial .tip { transition: none; } }
/* Under the dials: the way out of the story and into the record behind it. */
.simlinks { display: flex; flex-direction: column; gap: 0.4rem; }
.simbtn {
  font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  font-size: 0.68rem; letter-spacing: 0.07em; text-transform: uppercase; text-align: left;
  background: var(--surface); color: var(--accent); border: 1px solid var(--rule);
  border-radius: 2px; padding: 0.6rem 0.85rem; cursor: pointer; width: 100%;
}
.simbtn:hover { border-color: var(--accent); }
.simbtn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
/* The popup scrolls inside itself; the page behind it stays where it was. */
dialog.pop {
  width: min(40rem, calc(100vw - 2rem)); max-height: min(82vh, 46rem);
  padding: 0; border: 1px solid var(--rule); border-radius: 3px;
  background: var(--surface); color: var(--ink);
  box-shadow: 0 14px 44px rgba(0, 0, 0, 0.28);
}
dialog.pop[open] { display: flex; flex-direction: column; }
dialog.pop::backdrop { background: rgba(10, 16, 18, 0.5); }
.pop-head {
  display: flex; align-items: baseline; justify-content: space-between; gap: 1rem;
  padding: 0.95rem 1.25rem 0.85rem; border-bottom: 1px solid var(--rule); flex: none;
}
.pop-head h2 {
  font-family: Newsreader, Georgia, serif; font-weight: 600; font-size: 1.2rem;
  line-height: 1.25; margin: 0;
}
.pop-head .when {
  color: var(--accent); font-weight: 400; font-size: 0.85em; margin-left: 0.35rem;
}
.pop-close {
  font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  font-size: 0.66rem; letter-spacing: 0.08em; text-transform: uppercase;
  background: transparent; color: var(--muted); border: 0; padding: 0.3rem 0; cursor: pointer;
}
.pop-close:hover { color: var(--accent); }
.pop-body {
  overflow-y: auto; overscroll-behavior: contain;
  padding: 1.1rem 1.25rem 1.5rem; font-size: 0.92rem; line-height: 1.55;
}
.pop-body p { margin: 0 0 0.85rem; }
.pop-body p:last-child { margin-bottom: 0; }
.pop-body a { color: var(--accent); }
.pop-body h3 {
  font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace; font-weight: 400;
  font-size: 0.66rem; letter-spacing: 0.11em; text-transform: uppercase;
  color: var(--faint); margin: 1.5rem 0 0.55rem;
}
.pop-body .pop-note { color: var(--muted); font-size: 0.85rem; }
.pop-body table {
  width: 100%; border-collapse: collapse;
  font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace; font-size: 0.78rem;
}
.pop-body td { padding: 0.35rem 0; border-top: 1px solid var(--rule); }
.pop-body td.num { text-align: right; width: 4.5rem; }
.pop-body .up { color: var(--up); }
.pop-body .down { color: var(--down); }
.pop-body .flat { color: var(--faint); }
.pop-body ul.measures { margin: 0; padding-left: 1.1rem; }
.pop-body ul.measures li { margin: 0 0 0.4rem; }
.pop-body .status { display: block; color: var(--muted); font-size: 0.82rem; }
.pop-body code { font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace; font-size: 0.85em; }
.events { display: flex; flex-direction: column; gap: 0.4rem; }
.events details { border-top: 1px solid var(--rule); }
.events details:first-child { border-top: 0; }
.events summary { cursor: pointer; padding: 0.5rem 0; font-size: 0.72rem; letter-spacing: 0.03em; color: var(--ink); }
.events summary::marker { color: var(--faint); }
.events p { margin: 0 0 0.7rem; font-size: 0.85rem; line-height: 1.5; color: var(--muted); }
.events .none { font-size: 0.85rem; color: var(--faint); margin: 0; }
.choices { margin-top: 2.75rem; display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }
.choice {
  background: var(--surface); border: 1px solid var(--rule); border-top: 3px solid var(--accent);
  padding: 1.4rem 1.4rem 1.5rem; display: flex; flex-direction: column;
}
.choice h2 { font-size: 1.3rem; margin: 0 0 0.9rem; }
.choice p { margin: 0 0 0.9rem; font-size: 0.95rem; line-height: 1.55; }
.choice p.lead { font-size: 1rem; }
.choice details p { font-size: 0.92rem; color: var(--muted); }
.choice .meta { color: var(--muted); font-size: 0.85rem; }
.choice details { margin-bottom: 0.9rem; }
.choice details summary {
  cursor: pointer; font-size: 0.72rem; letter-spacing: 0.07em; text-transform: uppercase;
  color: var(--accent); font-family: "IBM Plex Mono", ui-monospace, monospace;
}
.choice .signal { font-size: 0.85rem; color: var(--faint); margin-top: auto; padding-top: 0.5rem; }
.choice.taken { border-top-color: var(--up); }
.choice.untaken { opacity: 0.5; }
button.pick {
  font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 0.72rem;
  letter-spacing: 0.08em; text-transform: uppercase; background: var(--accent);
  color: var(--surface); border: 0; border-radius: 2px; padding: 0.65rem 1.2rem;
  margin-top: 1rem; cursor: pointer; align-self: flex-start;
}
button.pick:disabled { background: var(--track); color: var(--faint); cursor: default; }
button.pick:hover:not(:disabled) { filter: brightness(1.1); }
button:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
.advance { margin-top: 2.5rem; }
.note {
  background: var(--accent-soft); border: 1px solid var(--rule); padding: 1.15rem 1.4rem;
  margin-bottom: 2.5rem; font-size: 0.95rem; line-height: 1.55; color: var(--muted);
  max-width: var(--measure);
}
.note strong { color: var(--ink); font-weight: 600; }
.note a { color: var(--accent); text-decoration: underline; text-underline-offset: 2px; }
.note a:hover { text-decoration-thickness: 2px; }
@media (prefers-reduced-motion: no-preference) {
  .chapter.enter { animation: rise 0.35s ease-out; }
  @keyframes rise { from { opacity: 0.45; transform: translateY(3px); } to { opacity: 1; transform: none; } }
}
@media (max-width: 62rem) {
  .layout { grid-template-columns: 1fr; gap: 2.5rem; }
  aside { position: static; flex-direction: row; flex-wrap: wrap; }
  aside .panel { flex: 1 1 16rem; }
  .dials { grid-template-columns: repeat(4, 1fr); }
}
@media (max-width: 44rem) {
  body { font-size: 18px; }
  .choices { grid-template-columns: 1fr; }
  .dials { grid-template-columns: repeat(3, 1fr); }
}
</style>
"""

BODY = """
<div class="wrap">
  <header class="masthead">
    <h1>Europe 2032</h1>
    <span class="sub">A simulated decision &middot; 2026&ndash;2032</span>
  </header>
  <div class="tabs" role="tablist" aria-label="Tellings of the same material">
    <button class="tab" type="button" id="tab-story" role="tab" data-view="story"
            aria-controls="view-story" aria-selected="true" tabindex="0">The story</button>
__TABS__
  </div>
  <button class="js-restart restart floating" type="button">Start over</button>
  <div class="layout" id="view-story" role="tabpanel" aria-labelledby="tab-story">
    <main id="stream"></main>
    <aside>
      <button class="js-restart restart" type="button">Start over</button>
      <section class="panel">
        <p class="cap"><span id="panel-period">Where things stand</span></p>
        <div class="dials" id="dials"></div>
      </section>
      <div class="simlinks">
        <button class="simbtn js-sim" type="button">Simulation data</button>
        <button class="simbtn js-about" type="button">About the simulation</button>
      </div>
      <div class="rail" id="rail" aria-hidden="true"></div>
    </aside>
  </div>
  <dialog class="pop" id="pop" aria-labelledby="pop-title">
    <div class="pop-head">
      <h2 id="pop-title"></h2>
      <button class="pop-close js-pop-close" type="button" aria-label="Close">Close</button>
    </div>
    <div class="pop-body" id="pop-body"></div>
  </dialog>
__ALTPANELS__
  __SITEFOOTER__
</div>
<script>
const NODES = __DATA__;
const START = __START__;
const PREAMBLE = __PREAMBLE__;
const POSTAMBLE = __POSTAMBLE__;
const LAST_TURN = 13;
const TIPS = __TIPS__;
const BANDS = ["very low", "low", "moderate", "high", "very high"];
const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const R = 24, CIRC = 2 * Math.PI * R, ARC = CIRC * 0.72;

let arm = 0, chain = [], picked = {}, active = null;

function metricOrder() {
  for (const id in NODES) {
    const m = NODES[id].metrics;
    if (m && m.length) return m.map(x => x.label);
  }
  return [];
}
const LABELS = metricOrder();

function buildDials() {
  document.getElementById("dials").innerHTML = LABELS.map((label, i) =>
    '<div class="dial" tabindex="0" aria-describedby="tip' + i + '">' +
      '<svg viewBox="0 0 60 60" width="56" height="56" role="img" id="a' + i + '" aria-label="' + label + '">' +
        '<g transform="rotate(129 30 30)">' +
          '<circle class="track" cx="30" cy="30" r="' + R + '" fill="none" stroke-width="5" stroke-linecap="round" ' +
            'stroke-dasharray="' + ARC.toFixed(1) + ' ' + CIRC.toFixed(1) + '"></circle>' +
          '<circle class="fill" id="f' + i + '" cx="30" cy="30" r="' + R + '" fill="none" stroke-width="5" ' +
            'stroke-linecap="round" stroke-dasharray="0 ' + CIRC.toFixed(1) + '"></circle>' +
        '</g></svg>' +
      '<b>' + label + '<i id="t' + i + '"></i></b>' +
      '<span class="tip" role="tooltip" id="tip' + i + '">' +
        (TIPS[label] || "") + '</span>' +
    '</div>').join("");
}

function setPanel(entry) {
  const metrics = entry.metrics || [];
  metrics.forEach((m, i) => {
    const frac = Math.max(0, Math.min(100, m.value)) / 100;
    const fill = document.getElementById("f" + i);
    if (fill) fill.setAttribute("stroke-dasharray", (ARC * frac).toFixed(1) + " " + CIRC.toFixed(1));
    const svg = document.getElementById("a" + i);
    if (svg) svg.setAttribute("aria-label", m.label + ": " + BANDS[Math.min(4, Math.floor(frac * 5))]);
    const tick = document.getElementById("t" + i);
    if (tick) {
      const moved = typeof m.delta === "number" && m.delta !== 0;
      tick.className = moved ? (m.delta > 0 ? "up" : "down") : "";
      tick.textContent = moved ? (m.delta > 0 ? "\u25b4" : "\u25be") : "";
    }
  });
  document.getElementById("panel-period").textContent = entry.period || "Where things stand";
  let ticks = "";
  for (let n = 1; n <= 13; n++) {
    ticks += '<i class="' + (n === entry.turn ? "now" : (n < entry.turn ? "done" : "")) + '"></i>';
  }
  document.getElementById("rail").innerHTML = ticks;
}

// The simulation data and the afterword open in one popup that scrolls inside
// itself, so the reader's place in the story never moves.
const pop = document.getElementById("pop");

function openPop(title, body) {
  document.getElementById("pop-title").innerHTML = title;
  const box = document.getElementById("pop-body");
  box.innerHTML = body;
  box.scrollTop = 0;
  if (!pop.open) pop.showModal();
}

function fmt(v) { return (Math.round(v * 10) / 10).toString(); }

function simHTML(entry) {
  const s = entry.sim || {};
  const evs = entry.events || [];
  let h = '<p class="pop-note">The simulation’s own record of ' + (entry.periodProse || "this half-year") +
    ', which the story is written from. Scales run from 0 to 100.</p>';
  h += '<h3>Events</h3>' + (evs.length
    ? '<div class="events">' + evs.map(e =>
        '<details><summary>' + e.title + '</summary><p>' + e.description + '</p></details>').join("") + '</div>'
    : '<p class="none">None. Nothing outside the Union’s own decisions moved.</p>');
  const ms = entry.metrics || [];
  if (ms.length) {
    h += '<h3>Where things stand</h3><table>' + ms.map(m => {
      const d = typeof m.delta === "number" && m.delta !== 0
        ? '<span class="' + (m.delta > 0 ? "up" : "down") + '">' + (m.delta > 0 ? "▴ +" : "▾ ") + fmt(m.delta) + '</span>'
        : '<span class="flat">–</span>';
      return '<tr><td>' + m.label + '</td><td class="num">' + fmt(m.value) + '</td><td class="num">' + d + '</td></tr>';
    }).join("") + '</table>';
  }
  if (s.measures && s.measures.length) {
    h += '<h3>The Union’s measures</h3><ul class="measures">' + s.measures.map(m =>
      '<li>' + m.name + ' <span class="status">' + m.status + '</span></li>').join("") + '</ul>';
  }
  if (s.priority) h += '<h3>Priority this half-year</h3><p>' + s.priority + '</p>';
  if (s.commitment) h += '<h3>Two-year commitment</h3><p>' + s.commitment + '</p>';
  return h;
}

function aboutHTML() {
  const m = POSTAMBLE.match(/<h2>(.*?)<\/h2>/);
  return { title: m ? m[1] : "About the simulation", body: POSTAMBLE.replace(/<h2>.*?<\/h2>/, "") };
}

function choiceCard(id, state) {
  const c = NODES[id];
  const cls = state === "taken" ? " taken" : (state === "untaken" ? " untaken" : "");
  const label = state === "taken" ? "Chosen" : (state === "untaken" ? "Not taken" : "Choose this");
  return '<section class="choice' + cls + '">' + c.title +
    (c.meta ? '<div class="meta">' + c.meta + '</div>' : "") +
    (c.lead ? '<p class="lead">' + c.lead + '</p>' : "") +
    '<details><summary>Read the full case</summary>' + c.rest + '</details>' +
    (c.signal ? '<div class="signal">' + c.signal + '</div>' : "") +
    '<button class="pick" type="button" data-go="' + id + '"' +
      (state ? " disabled" : "") + '>' + label + '</button></section>';
}

function endingHTML(unfinished) {
  const notice = unfinished
    ? '<div class="note draft"><strong>This is as far as the writing has got.</strong> ' +
      'The simulation runs on to the end of 2032 and to twenty-four different endings; the prose is ' +
      'written through the second decision. Comment on any passage that drags, ' +
      'or that you had to read twice.</div>'
    : "";
  const closing = POSTAMBLE ? '<div class="note end">' + POSTAMBLE + '</div>' : "";
  return notice + closing;
}

function controlsFor(id) {
  const entry = NODES[id];
  if (entry.choices && entry.choices.length) {
    return '<div class="choices" data-for="' + id + '">' +
      entry.choices.map(cid => choiceCard(cid, picked[id] ? (cid === picked[id] ? "taken" : "untaken") : null)).join("") +
      '</div>';
  }
  if (entry.next) {
    return '<div class="advance" data-for="' + id + '">' +
      '<button class="pick" type="button" data-go="' + entry.next + '">Show the next six months</button></div>';
  }
  return endingHTML(entry.turn !== LAST_TURN);
}

function appendChapter(id, entering) {
  chain.push(id);
  const entry = NODES[id];
  const section = document.createElement("section");
  section.className = entering ? "chapter enter" : "chapter";
  section.dataset.node = id;
  const head = entry.title
    ? '<h2 class="chapter-title"><span class="when">' + entry.period + ':</span> ' + entry.title + '</h2>'
    : '<h2 class="chapter-title"><span class="when">' + entry.period + '</span></h2>';
  section.innerHTML = '<article>' + head + entry.html + '</article>' +
                      '<div class="controls">' + controlsFor(id) + '</div>';
  document.getElementById("stream").appendChild(section);
  return section;
}

const TEXT_BLOCKS = "h2, h3, p, li, summary, .signal, .meta";
const LETTER_MS = 1200;  // how long one character takes to leave
const SPREAD_MS = 1200;  // how long the wave takes to cross everything visible
const CHAR_CAP = 3200;   // beyond this, blocks fade rather than shatter

function shatter(el, from, total, reverse) {
  // Split text nodes only, so the markup inside a heading — the dateline span,
  // an emphasis — survives intact.
  const walk = node => {
    if (node.nodeType === 3) {
      const frag = document.createDocumentFragment();
      for (const token of node.textContent.split(/(\s+)/)) {
        if (!token) continue;
        if (/^\s+$/.test(token)) { frag.appendChild(document.createTextNode(token)); continue; }
        const word = document.createElement("span");
        word.className = "wd";
        for (const ch of token) {
          const s = document.createElement("span");
          s.className = "ch";
          s.textContent = ch;
          word.appendChild(s);
        }
        frag.appendChild(word);
      }
      node.replaceWith(frag);
    } else if (node.nodeType === 1) {
      Array.from(node.childNodes).forEach(walk);
    }
  };
  Array.from(el.childNodes).forEach(walk);
  const chars = el.querySelectorAll(".ch");
  const n = chars.length;
  chars.forEach((s, i) => {
    // Delay is a fraction of the whole wave, not a fixed step, so the effect
    // takes the same time whether one paragraph is showing or five. Within a
    // block the order runs backwards, so the last line goes before the first
    // and the whole thing reads as rising rather than falling.
    const order = reverse ? (n - 1 - i) : i;
    const at = (from + order) / Math.max(1, total);
    s.style.setProperty("--tilt", (Math.random() * 18 - 9).toFixed(1) + "deg");
    s.style.animation = "letter " + LETTER_MS + "ms cubic-bezier(0.4, 0, 0.6, 1) forwards";
    s.style.animationDelay = (at * SPREAD_MS + Math.random() * 60).toFixed(0) + "ms";
  });
  return chars.length;
}

function onScreen(el) {
  const r = el.getBoundingClientRect();
  return r.height > 0 && r.bottom > 0 && r.top < window.innerHeight;
}

function startOver() {
  const stream = document.getElementById("stream");
  if (REDUCED || !stream.children.length) { reset(); return; }
  // Whatever the reader is actually looking at is what comes apart. Everything
  // above and below is off screen and needs no animation at all.
  const visible = Array.from(stream.querySelectorAll(TEXT_BLOCKS))
    .filter(el => onScreen(el) && !el.querySelector(TEXT_BLOCKS));
  if (!visible.length) { reset(); return; }

  // Measure everything before touching anything: rects taken after the first
  // split would be measuring the mutated layout.
  const measured = visible.map(el => ({ el, rect: el.getBoundingClientRect() }));
  // Bottom of the screen first, so the page lifts away upward.
  measured.sort((a, b) => b.rect.top - a.rect.top);
  // Pin the height each block already had. If it does still re-wrap, the extra
  // line overflows harmlessly instead of pushing everything below it down.
  measured.forEach(m => { m.el.style.height = m.rect.height + "px"; });
  const rising = measured.map(m => m.el);

  const total = rising.reduce((n, el) => n + el.textContent.length, 0);
  stream.classList.add("dissolving");
  let seen = 0;
  rising.forEach(el => {
    if (seen > CHAR_CAP) {
      el.classList.add("fade-block");
      el.style.animationDelay = ((seen / Math.max(1, total)) * SPREAD_MS).toFixed(0) + "ms";
      return;
    }
    seen += shatter(el, seen, Math.min(total, CHAR_CAP), true);
  });

  setTimeout(() => {
    stream.classList.remove("dissolving");
    reset(true);
  }, LETTER_MS + SPREAD_MS + 120);
}

function reset(arriving) {
  arm = Math.floor(Math.random() * 3);
  chain = [];
  picked = {};
  active = null;
  const stream = document.getElementById("stream");
  stream.classList.remove("dissolving");
  stream.innerHTML = PREAMBLE ? '<div class="note preamble">' + PREAMBLE + '</div>' : "";
  appendChapter(START);
  setPanel(NODES[START]);
  active = START;
  window.scrollTo({ top: 0, behavior: "instant" });
  if (arriving && !REDUCED) {
    stream.classList.add("arriving");
    setTimeout(() => stream.classList.remove("arriving"), 1200);
  }
}

function trackActive() {
  const marker = window.innerHeight * 0.32;
  let found = null;
  document.querySelectorAll(".chapter").forEach(el => {
    if (el.getBoundingClientRect().top <= marker) found = el.dataset.node;
  });
  if (found && found !== active) {
    active = found;
    setPanel(NODES[found]);
  }
}

let queued = false;
window.addEventListener("scroll", () => {
  if (queued) return;
  queued = true;
  requestAnimationFrame(() => { queued = false; trackActive(); });
}, { passive: true });

document.addEventListener("click", e => {
  if (e.target.closest(".js-sim")) {
    const entry = NODES[active];
    if (entry) openPop('Simulation data <span class="when">' + entry.period + '</span>', simHTML(entry));
    return;
  }
  if (e.target.closest(".js-about")) {
    const a = aboutHTML();
    openPop(a.title, a.body);
    return;
  }
  // A click on the backdrop lands on the dialog element itself.
  if (e.target.closest(".js-pop-close") || e.target === pop) {
    pop.close();
    return;
  }
  const btn = e.target.closest("[data-go]");
  if (btn && !btn.disabled) {
    const id = btn.dataset.go, entry = NODES[id];
    const holder = btn.closest("[data-for]");
    const from = holder ? holder.dataset.for : null;
    let target = id;
    if (entry && entry.kind === "choice") {
      if (from) picked[from] = id;
      target = entry.nextByArm ? entry.nextByArm[arm] : entry.next;
      if (holder) holder.outerHTML = controlsFor(from);
      if (!target || !NODES[target]) {
        document.querySelector('[data-node="' + from + '"] .controls')
          .insertAdjacentHTML("beforeend", endingHTML(true));
        return;
      }
    } else if (holder) {
      holder.remove();
    }
    const section = appendChapter(target, true);
    section.scrollIntoView({ behavior: REDUCED ? "auto" : "smooth", block: "start" });
    return;
  }
  if (e.target.closest(".js-restart")) startOver();
});

// Tabs. Switching views only toggles which panel is shown — the interactive
// story keeps its chapters, its choices and the reader's scroll position, so
// coming back lands where they left. A view's name is also its URL fragment,
// so any tab can be linked to directly; the fragment is the only thing this
// page uses the hash for.
const TABS = Array.from(document.querySelectorAll('[role="tab"]'));
const SCROLL_AT = Object.fromEntries(TABS.map(t => [t.dataset.view, 0]));
let view = "story";

function showView(next, fromHash) {
  if (!SCROLL_AT.hasOwnProperty(next)) return;
  if (next !== view) {
    SCROLL_AT[view] = window.scrollY;
    view = next;
    TABS.forEach(t => {
      const on = t.dataset.view === next;
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
      const panel = document.getElementById(t.getAttribute("aria-controls"));
      if (panel) panel.hidden = !on;
    });
    document.body.dataset.view = next;
    window.scrollTo({ top: SCROLL_AT[next], behavior: "instant" });
  }
  if (fromHash) return;
  // replaceState, not pushState: a reader flicking between tellings should not
  // have to press back once per click to leave the page.
  const url = next === "story"
    ? location.pathname + location.search
    : location.pathname + location.search + "#" + next;
  history.replaceState(null, "", url);
}

TABS.forEach((tab, i) => {
  tab.addEventListener("click", () => showView(tab.dataset.view));
  tab.addEventListener("keydown", e => {
    let j = null;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") j = (i + 1) % TABS.length;
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") j = (i - 1 + TABS.length) % TABS.length;
    else if (e.key === "Home") j = 0;
    else if (e.key === "End") j = TABS.length - 1;
    if (j === null) return;
    e.preventDefault();
    showView(TABS[j].dataset.view);
    TABS[j].focus();
  });
});
document.body.dataset.view = "story";

// An unknown or absent fragment leaves the reader in the interactive story.
window.addEventListener("hashchange", () => showView(location.hash.slice(1), true));
showView(location.hash.slice(1), true);

buildDials();
reset();
</script>
"""


def dial_tips(path: Path) -> dict[str, str]:
    """Reader-facing dial explanations, keyed by the metric label.

    Authored in `story/dial-tips.md` rather than here, like the preamble and
    postamble: it is prose a reader sees, so it is edited as prose. A heading
    that matches no metric label simply never renders.
    """
    out: dict[str, str] = {}
    text = path.read_text(encoding="utf-8")
    for block in re.split(r"^##\s+", text, flags=re.M)[1:]:
        head, _, rest = block.partition("\n")
        paragraph = rest.strip().split("\n\n")[0].strip()
        if paragraph:
            out[head.strip()] = re.sub(r"\s+", " ", paragraph)
    return out


def alt_reading(path: Path) -> str:
    """The alternative telling, with the internal notes around it left behind.

    Each file under `experiments/` is a working document: it opens with framing
    written for the team and closes with an assessment section, and neither is
    for a reader. Only the two read-throughs between them are published, so the
    extraction is anchored on those two landmarks rather than on line numbers
    the drafting will move. Every telling in `ALT_TELLINGS` is read this way.
    """
    text = path.read_text(encoding="utf-8")
    start = re.search(r"^#\s+Path one\b.*$", text, re.M)
    if not start:
        return ""
    end = re.search(r"^##\s+Notes for assessment\b.*$", text, re.M)
    body = text[start.start():end.start() if end else len(text)].rstrip()
    body = re.sub(r"\n\s*(?:-{3,}|\*{3,}|_{3,})\s*$", "", body)
    return markdown(body)


# The alternative tellings, in tab order. A telling whose source file is absent
# simply does not get a tab, so the page still builds from a partial checkout.
# `view` is the tab's URL fragment as well as its id, so #straight-through and
# #tight are the deep links.
#
# Retired 2026-09-11: the three experimental tellings are deleted with their
# sources (in git history). The published page is the story alone.
ALT_TELLINGS: list[dict[str, str]] = []


def alt_panels(experiments: Path) -> tuple[str, str]:
    """Tab buttons and reader panels for every alternative telling that exists."""
    tabs: list[str] = []
    panels: list[str] = []
    for telling in ALT_TELLINGS:
        source = experiments / telling["source"]
        body = alt_reading(source) if source.is_file() else ""
        if not body:
            continue
        view = telling["view"]
        intro_path = experiments / telling["intro"]
        intro = markdown(intro_path.read_text(encoding="utf-8")) \
            if intro_path.is_file() else ""
        tabs.append(
            f'    <button class="tab" type="button" id="tab-{view}" role="tab"'
            f' data-view="{view}"\n'
            f'            aria-controls="view-{view}" aria-selected="false"'
            f' tabindex="-1">{html.escape(telling["label"])}</button>')
        panels.append(
            f'  <div class="altview" id="view-{view}" role="tabpanel"'
            f' aria-labelledby="tab-{view}" tabindex="0" hidden>\n'
            f'    <div class="note preamble">{intro}</div>\n'
            f'    <article>{body}</article>\n'
            f'  </div>')
    return "\n".join(tabs), "\n".join(panels)


SITE_FOOTER = """<footer class="site">
    <a href="https://falkai.org/">Falk AI</a>
    <span><a href="https://github.com/Itangalo/scenario-lab">Scenario Lab</a> &middot; draft</span>
  </footer>"""

SITE_FOOTER_CSS = """
/* Standalone only: the page sits on a site, and needs a way back to it. */
footer.site {
  display: flex; flex-wrap: wrap; gap: 0.6rem 1.25rem; align-items: baseline;
  margin-top: 4rem; padding-top: 1.25rem; border-top: 1px solid var(--rule);
  font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--faint);
}
footer.site a { color: var(--accent); text-decoration: none; }
footer.site a:hover { text-decoration: underline; text-underline-offset: 3px; }
"""


def standalone(head: str, body: str) -> str:
    """Wrap the page as an ordinary web page for falkai.org.

    The artifact host supplies the document skeleton, so the page normally
    starts at <title>. On a site it has to carry its own, and follow the site's
    conventions: the `... · Falk AI` title, the shared favicons, a link home.

    It stays noindex on purpose. This is an unfinished draft that stops in 2029
    and is meant to move to its own domain; indexing it now buys a search result
    that will rot. One line to remove when that changes.
    """
    head = head.replace("<title>Europe 2032</title>\n", "", 1)
    head = head.replace("</style>", SITE_FOOTER_CSS + "</style>", 1)
    body = body.replace("__SITEFOOTER__", SITE_FOOTER, 1)
    description = ("An interactive scenario: you take the European Union through "
                   "2026\u20132032 without knowing which AI trajectory you are on. "
                   "Built from several hundred simulation runs.")
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>Europe 2032 &middot; Falk AI</title>\n"
        f'<meta name="description" content="{description}">\n'
        '<meta name="robots" content="noindex, follow">\n'
        '<meta property="og:type" content="article">\n'
        '<meta property="og:site_name" content="Falk AI">\n'
        '<meta property="og:title" content="Europe 2032">\n'
        f'<meta property="og:description" content="{description}">\n'
        '<meta property="og:url" content="https://falkai.org/europe-2032/">\n'
        '<meta name="twitter:card" content="summary">\n'
        '<link rel="icon" href="/favicon.ico">\n'
        '<link rel="apple-touch-icon" href="/favicon-180.png">\n'
        f"{head}"
        "</head>\n<body>\n"
        f"{body}"
        "</body>\n</html>\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenario", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--standalone", action="store_true",
                    help="emit a full web page for falkai.org, not artifact content")
    args = ap.parse_args()

    story_dir = args.scenario / "story"
    tree_dir = story_dir / "tree"
    nodes = load_nodes(tree_dir)
    preamble_path = story_dir / "preamble.md"
    preamble = markdown(preamble_path.read_text(encoding="utf-8")) \
        if preamble_path.is_file() else ""
    tips_path = story_dir / "dial-tips.md"
    tips = dial_tips(tips_path) if tips_path.is_file() else {}
    postamble_path = story_dir / "postamble.md"
    postamble = markdown(postamble_path.read_text(encoding="utf-8")) \
        if postamble_path.is_file() else ""
    alt_tabs, alt_views = alt_panels(story_dir / "experiments")
    payload = build_payload(nodes)
    start = opaque("turn-01")
    if start not in payload:
        raise SystemExit("turn-01 is not written; nothing to build")

    body = BODY.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    body = body.replace("__START__", json.dumps(start))
    body = body.replace("__PREAMBLE__", json.dumps(preamble))
    body = body.replace("__POSTAMBLE__", json.dumps(postamble))
    body = body.replace("__TIPS__", json.dumps(tips, ensure_ascii=False))
    body = body.replace("__TABS__", alt_tabs, 1)
    body = body.replace("__ALTPANELS__", alt_views, 1)
    out = args.out or (args.scenario / "story.html")
    page = standalone(HEAD, body) if args.standalone else HEAD + body.replace(
        "__SITEFOOTER__", "", 1)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")

    turns = sum(1 for e in payload.values() if e["kind"] == "turn")
    choices = sum(1 for e in payload.values() if e["kind"] == "choice")
    leak = re.findall(r"\b[AVP][12]{1,3}\b", page)
    print(f"wrote {out} — {turns} turns, {choices} choice pages, "
          f"{out.stat().st_size // 1024} KB")
    print(f"branch ids in output: {len(leak)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
