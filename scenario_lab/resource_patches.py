"""Variant resource patches: partial overrides of base-scenario resources.

A variant may declare ``patches:`` in its YAML – a list of
``{resource: <name>, path: <file>}`` entries applied in order after the base
scenario's resources load. Patch files reuse the same markdown grammar as the
resource they modify; matching is by stable key (event ``**ID:**``, rule
number), and only the fields a section states are overridden:

- **Events**: present fields (``Condition``, ``Probability``, ``Description``,
  ``Can repeat``, ``Eligible``) replace the base event's; a section whose ID
  matches nothing is a *new* event when it carries ID + Probability +
  Description, otherwise an error with the nearest existing IDs named;
  ``**Remove:** yes`` deletes the event.
- **Metric rules**: a numbered item replaces the rule with that number
  wholesale; numbers beyond the current maximum append.

Unknown IDs failing loudly is deliberate: the failure mode to avoid is a typo'd
key silently turning an override into an addition.
"""

from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Union

from .models import Event


PATCHABLE_RESOURCES = ("events", "metric_rules")

_EVENT_FIELD_KEYS = {
    "condition": "condition",
    "probability": "probability",
    "description": "description",
    "can_repeat": "can_repeat",
    "eligible": "eligible",
}

_RULE_START_RE = re.compile(r"^(\d+)\.\s(.*)$")


def _nearest(ids: list[str], target: str) -> str:
    matches = difflib.get_close_matches(target, ids, n=3, cutoff=0.5)
    return f" (nearest existing: {', '.join(matches)})" if matches else ""


def _split_sections(text: str) -> list[tuple[str | None, list[str]]]:
    """Split markdown into (header, body-lines) sections at '## ' boundaries."""
    sections: list[tuple[str | None, list[str]]] = [(None, [])]
    for line in text.split("\n"):
        if line.strip().startswith("## "):
            sections.append((line.strip()[3:].strip(), []))
        else:
            sections[-1][1].append(line)
    return sections


def _parse_fields(lines: list[str]) -> dict[str, str]:
    """Parse '**Key:** value' lines into normalized field -> value."""
    fields: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("**") or ":" not in stripped:
            continue
        label, _, value = stripped[2:].partition(":**")
        key = label.strip().lower().replace(" ", "_").rstrip(":")
        fields[key] = value.strip()
    return fields


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

def parse_event_patch(path: Path) -> list[dict]:
    """Parse an events patch file into partial entries.

    Returns a list of ``{"id": ..., "remove": bool, "updates": {...}}`` in file
    order. Sections without an ID are ignored (prose preamble), mirroring how
    the base loader skips headings before the first event.
    """
    entries: list[dict] = []
    for header, lines in _split_sections(path.read_text(encoding="utf-8")):
        if header is None:
            continue
        fields = _parse_fields(lines)
        entry_id = fields.pop("id", None)
        if not entry_id:
            continue
        remove = fields.pop("remove", "").strip().lower() in ("yes", "true")
        updates = {k: v for k, v in fields.items() if k in _EVENT_FIELD_KEYS}
        unknown = sorted(set(fields) - set(_EVENT_FIELD_KEYS))
        if unknown:
            raise ValueError(
                f"{path}: event patch '{entry_id}' has unknown field(s) {unknown}; "
                f"allowed: {sorted(_EVENT_FIELD_KEYS)} plus Remove/ID"
            )
        entries.append({"id": entry_id, "remove": remove, "updates": updates})
    return entries


def apply_event_patches(events: list[Event], path: Path) -> list[Event]:
    """Apply one events patch file to a parsed event list, returning a new list."""
    by_id = {e.id: e for e in events}
    result = list(events)

    for entry in parse_event_patch(path):
        event_id = entry["id"]
        existing = by_id.get(event_id)

        if entry["remove"]:
            if existing is None:
                raise ValueError(
                    f"{path}: cannot remove unknown event '{event_id}'"
                    f"{_nearest(sorted(by_id), event_id)}"
                )
            result = [e for e in result if e.id != event_id]
            continue

        updates = entry["updates"]
        if existing is None:
            # Addition: must carry the fields a standalone event needs.
            missing = [f for f in ("description", "probability") if f not in updates]
            if missing:
                raise ValueError(
                    f"{path}: event patch '{event_id}' matches no existing event and "
                    f"is missing required field(s) {missing} for a new event"
                    f"{_nearest(sorted(by_id), event_id)}"
                )
            new_event = Event(
                id=event_id,
                description=updates.get("description", ""),
                condition=updates.get("condition", ""),
                probability=updates.get("probability", "0"),
                can_repeat=updates.get("can_repeat", "no").lower() in ("yes", "true"),
                eligible=updates.get("eligible", ""),
            )
            result.append(new_event)
            by_id[event_id] = new_event
            continue

        # Override: replace only stated fields.
        if "can_repeat" in updates:
            updates = dict(updates)
            updates["can_repeat"] = (
                "yes" if updates["can_repeat"].lower() in ("yes", "true") else "no"
            )
        for key in _EVENT_FIELD_KEYS:
            if key in updates:
                setattr(existing, key, updates[key])

    return result


# ---------------------------------------------------------------------------
# Metric rules
# ---------------------------------------------------------------------------

def _split_rules(text: str) -> tuple[list[str], list[tuple[int, list[str]]]]:
    """Split metric rules markdown into (preamble-lines, [(number, lines)])."""
    preamble: list[str] = []
    items: list[tuple[int, list[str]]] = []
    current: tuple[int, list[str]] | None = None
    for line in text.split("\n"):
        match = _RULE_START_RE.match(line)
        if match and not line.startswith(" "):
            current = (int(match.group(1)), [line])
            items.append(current)
        elif current is not None:
            current[1].append(line)
        else:
            preamble.append(line)
    return preamble, items


def render_rules(preamble: list[str], items: list[tuple[int, list[str]]]) -> str:
    parts = ["\n".join(preamble).rstrip()]
    for _, lines in items:
        parts.append("\n".join(lines).rstrip())
    return "\n\n".join(parts) + "\n"


def apply_metric_rule_patches(rules_text: str, path: Path) -> str:
    """Apply a metric-rules patch file: numbered items replace or append."""
    preamble, items = _split_rules(rules_text)
    by_number = {number: index for index, (number, _) in enumerate(items)}

    patch_text = path.read_text(encoding="utf-8")
    _, patch_items = _split_rules(patch_text)
    if not patch_items:
        raise ValueError(f"{path}: no numbered rule entries found in metric-rules patch")

    max_existing = max(by_number) if by_number else 0
    for number, lines in patch_items:
        replacement = "\n".join(lines).rstrip()
        if number in by_number:
            items[by_number[number]] = (number, replacement.split("\n"))
        elif number <= max_existing:
            raise ValueError(
                f"{path}: rule patch targets rule {number}, but that number is not "
                f"present in the base rules (existing: {sorted(by_number)})"
            )
        else:
            items.append((number, replacement.split("\n")))
            by_number[number] = len(items) - 1

    return render_rules(preamble, items)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def apply_resource_patch(
    resource: str,
    events: Union[list[Event], None],
    rules_text: Union[str, None],
    path: Path,
) -> tuple[list[Event] | None, str | None]:
    """Apply one patch file to the given resource, returning updated values.

    Exactly one of ``events`` / ``rules_text`` is expected per resource kind.
    Raises ValueError for unknown resources so a typo'd YAML key fails loudly.
    """
    if resource == "events":
        if events is None:
            raise ValueError(f"{path}: events patch but no events loaded")
        return apply_event_patches(events, path), rules_text
    if resource == "metric_rules":
        if rules_text is None:
            raise ValueError(f"{path}: metric_rules patch but no rules loaded")
        return events, apply_metric_rule_patches(rules_text, path)
    raise ValueError(
        f"{path}: unknown patchable resource '{resource}'; "
        f"allowed: {list(PATCHABLE_RESOURCES)}"
    )
