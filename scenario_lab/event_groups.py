"""Mutually exclusive event families: "exactly one of these happens".

Some outcomes are a choice among alternatives rather than a set of independent
coin flips. An election returns one administration, a succession produces one
successor, a blockade either happens or is negotiated away. Modelling those as
separate events with independent dice cannot express the constraint: two of
them can fire in the same turn, or none can, and neither is a possible world.

Scenarios have worked around this by writing one event whose *description*
carries every outcome plus a rule for choosing between them, leaving the choice
to the Game Master's prose. That fails in two ways this module removes. The
"certain" event is not certain, because multi-sample probability elicitation
averages a probability the model sometimes omits. And the rule for choosing is
applied from prose against a history the Game Master cannot see in structured
form, so it defaults.

A group makes the constraint the orchestrator's business, where the dice
already live, and leaves judgment where it belongs: the events step still
prices each member, and those prices become the *relative* weights. Python only
enforces the structure. The outcome then lands in the run's event record as its
own event id, so later gates, resume, and cross-run analysis can read it
without parsing narrative.

Two resolutions:

- ``exactly_one`` — one member fires whenever the group is due. Requires
  ``due_turns`` (when it resolves) and ``default`` (which member wins when the
  events step gave every member a weight of zero).
- ``at_most_one`` — the family is mutually exclusive but not guaranteed. The
  summed weight decides whether anything fires; the individual weights decide
  which.

A group may instead select deterministically from the run's own history with
``select_by``, for outcomes that are a *consequence* of earlier events rather
than a fresh draw. No dice are involved in that case.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

RESOLUTIONS = ("exactly_one", "at_most_one")


@dataclass(frozen=True)
class HistorySelector:
    """Deterministic selection from the run's own event record.

    ``mapping`` maps a source event id to the member it elects. The most
    recently fired source event decides; where several fired in the same turn,
    the earliest entry in ``precedence`` wins. Nothing fired means no
    selection, and the group falls back to its default.
    """

    mapping: dict[str, str] = field(default_factory=dict)
    precedence: tuple[str, ...] = ()


@dataclass(frozen=True)
class EventGroup:
    """A mutually exclusive family of events."""

    id: str
    members: tuple[str, ...]
    resolution: str = "at_most_one"
    due_turns: tuple[int, ...] = ()
    default: Optional[str] = None
    select_by: Optional[HistorySelector] = None

    def is_due(self, turn: int) -> bool:
        """Whether the group resolves this turn.

        A group with no ``due_turns`` is due whenever the events step lists at
        least one member, which the caller establishes; one that names turns
        resolves only in those.
        """
        return not self.due_turns or turn in self.due_turns


@dataclass(frozen=True)
class GroupResolution:
    """The outcome of resolving one group in one turn."""

    group_id: str
    chosen: Optional[str]
    basis: str  # "forced" | "history" | "weighted" | "default" | "none"
    detail: str = ""


def parse_event_groups(raw) -> tuple[list[EventGroup], list[str]]:
    """Parse the ``event_groups`` YAML block. Returns (groups, errors)."""
    if raw is None:
        return [], []
    if not isinstance(raw, list):
        return [], ["event_groups must be a list"]

    groups: list[EventGroup] = []
    errors: list[str] = []

    for index, entry in enumerate(raw):
        label = f"event_groups[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be a mapping")
            continue

        group_id = str(entry.get("id") or "").strip()
        if not group_id:
            errors.append(f"{label} is missing 'id'")
            continue

        members_raw = entry.get("members")
        if isinstance(members_raw, str):
            members_raw = [members_raw]
        if not isinstance(members_raw, list) or len(members_raw) < 2:
            errors.append(f"event group '{group_id}' needs at least two members")
            continue
        members = tuple(str(m).strip() for m in members_raw if str(m).strip())
        if len(set(members)) != len(members):
            errors.append(f"event group '{group_id}' lists a member twice")
            continue

        resolution = str(entry.get("resolution") or "at_most_one").strip()
        if resolution not in RESOLUTIONS:
            errors.append(
                f"event group '{group_id}' has invalid resolution '{resolution}' "
                f"(expected one of {', '.join(RESOLUTIONS)})"
            )
            continue

        due_raw = entry.get("due_turns") or []
        if isinstance(due_raw, int):
            due_raw = [due_raw]
        try:
            due_turns = tuple(int(t) for t in due_raw)
        except (TypeError, ValueError):
            errors.append(f"event group '{group_id}' has non-integer due_turns")
            continue

        default = entry.get("default")
        default = str(default).strip() if default else None
        if default and default not in members:
            errors.append(
                f"event group '{group_id}' default '{default}' is not one of its members"
            )
            continue

        selector = None
        select_raw = entry.get("select_by")
        if select_raw is not None:
            if not isinstance(select_raw, dict):
                errors.append(f"event group '{group_id}' select_by must be a mapping")
                continue
            kind = str(select_raw.get("kind") or "most_recent_event").strip()
            if kind != "most_recent_event":
                errors.append(
                    f"event group '{group_id}' has unsupported select_by kind '{kind}'"
                )
                continue
            mapping_raw = select_raw.get("map") or {}
            if not isinstance(mapping_raw, dict) or not mapping_raw:
                errors.append(f"event group '{group_id}' select_by needs a non-empty map")
                continue
            mapping = {str(k).strip(): str(v).strip() for k, v in mapping_raw.items()}
            unknown = sorted(v for v in mapping.values() if v not in members)
            if unknown:
                errors.append(
                    f"event group '{group_id}' select_by maps to non-members: "
                    f"{', '.join(unknown)}"
                )
                continue
            precedence_raw = select_raw.get("precedence") or list(mapping.keys())
            precedence = tuple(str(p).strip() for p in precedence_raw)
            missing = sorted(set(mapping) - set(precedence))
            if missing:
                errors.append(
                    f"event group '{group_id}' select_by precedence omits: "
                    f"{', '.join(missing)}"
                )
                continue
            selector = HistorySelector(mapping=mapping, precedence=precedence)

        if resolution == "exactly_one":
            if not due_turns:
                errors.append(
                    f"event group '{group_id}' is exactly_one and must name due_turns, "
                    f"otherwise there is no turn in which it is guaranteed to resolve"
                )
                continue
            if not default:
                errors.append(
                    f"event group '{group_id}' is exactly_one and must name a default "
                    f"member, which decides when every weight is zero"
                )
                continue

        groups.append(
            EventGroup(
                id=group_id,
                members=members,
                resolution=resolution,
                due_turns=due_turns,
                default=default,
                select_by=selector,
            )
        )

    return groups, errors


def select_from_history(
    selector: HistorySelector, event_log: list[dict], before_turn: Optional[int] = None
) -> Optional[str]:
    """The member elected by the most recent mapped event in the record.

    ``event_log`` is the run's turn-stamped record of what actually fired.
    Entries from ``before_turn`` onward are ignored, so a group resolving in
    turn N reads only what happened before it. Ties inside one turn are broken
    by ``precedence``.
    """
    best_turn = None
    fired_in_best: list[str] = []

    for entry in event_log:
        source = entry.get("id")
        if source not in selector.mapping:
            continue
        turn = entry.get("turn")
        if not isinstance(turn, int):
            continue
        if before_turn is not None and turn >= before_turn:
            continue
        if best_turn is None or turn > best_turn:
            best_turn, fired_in_best = turn, [source]
        elif turn == best_turn and source not in fired_in_best:
            fired_in_best.append(source)

    if not fired_in_best:
        return None

    for candidate in selector.precedence:
        if candidate in fired_in_best:
            return selector.mapping[candidate]
    return selector.mapping[fired_in_best[0]]


def _weighted_pick(members: tuple[str, ...], weights: dict[str, float], position: float):
    """First member whose cumulative normalised weight passes ``position``."""
    total = sum(max(0.0, weights.get(m, 0.0)) for m in members)
    if total <= 0:
        return None
    cumulative = 0.0
    for member in members:
        cumulative += max(0.0, weights.get(member, 0.0)) / total
        if position < cumulative:
            return member
    return members[-1]


def resolve_group(
    group: EventGroup,
    weights: dict[str, float],
    roll: float,
    event_log: Optional[list[dict]] = None,
    turn: Optional[int] = None,
    forced: tuple[str, ...] = (),
) -> GroupResolution:
    """Decide which member of a group fires, if any.

    ``weights`` are the probabilities the events step returned for the members
    it listed; a member the model omitted, or one suppressed by a branch
    counterfactual, is simply absent or zero. ``roll`` is a single seeded draw
    for the whole group, so one group consumes one die whatever its size.
    """
    for member in group.members:
        if member in forced:
            return GroupResolution(group.id, member, "forced", "forced by event override")

    if group.select_by is not None:
        chosen = select_from_history(group.select_by, event_log or [], before_turn=turn)
        if chosen is not None:
            return GroupResolution(group.id, chosen, "history", "elected by the event record")
        if group.resolution == "exactly_one":
            return GroupResolution(
                group.id, group.default, "default", "no mapped event in the record"
            )
        return GroupResolution(group.id, None, "none", "no mapped event in the record")

    total = sum(max(0.0, weights.get(m, 0.0)) for m in group.members)

    if group.resolution == "exactly_one":
        if total <= 0:
            return GroupResolution(
                group.id, group.default, "default", "every member weighted zero"
            )
        chosen = _weighted_pick(group.members, weights, roll)
        return GroupResolution(group.id, chosen, "weighted", f"summed weight {total:.3f}")

    # at_most_one: the summed weight decides whether, the shares decide which.
    capped = min(total, 1.0)
    if roll >= capped:
        return GroupResolution(
            group.id, None, "none", f"roll {roll:.3f} >= summed weight {capped:.3f}"
        )
    position = roll / capped if capped > 0 else 0.0
    chosen = _weighted_pick(group.members, weights, position)
    return GroupResolution(group.id, chosen, "weighted", f"summed weight {capped:.3f}")
