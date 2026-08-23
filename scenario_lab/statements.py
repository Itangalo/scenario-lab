"""Parsing and application of actor statement-change proposals.

Actors never restate their statements. The ledger is carried forward verbatim
by the orchestrator, and only an explicit, structured ``## Statement changes``
section alters it. This module owns the grammar of that section and the
structural checks on it.

Two things are deliberately *not* here:

- Any judgement about whether a proposal's grounds are good enough. That is a
  merit judgement; it varies between referees and would put variance into
  results. It is charged for in the world instead, by the Game Master.
- Any per-turn cap, budget or cooldown. Rule evolution failed under exactly
  such a cap, which behaved as a quota rather than a ceiling.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .models import STATEMENT_TIERS, Actor, Statement

# Tiers whose reversal must name a triggering development. Adding or upgrading
# is self-binding rather than a reversal, so it needs no trigger -- an actor
# staking itself to something new is free to do so, and pays later.
GATED_TIERS = ("commitment", "identity")

NO_CHANGES_MARKERS = ("no statement changes", "none", "no changes")

_SECTION_RE = re.compile(r"^##\s+Statement changes\s*$", re.IGNORECASE | re.MULTILINE)
_NEXT_SECTION_RE = re.compile(r"^##\s+", re.MULTILINE)

_MODIFY_RE = re.compile(
    r"^modify\s+`(?P<id>[a-z0-9_]+)`"
    r"(?:\s*\((?P<tier>position|commitment|identity)\))?\s*:\s*(?P<text>.+)$",
    re.IGNORECASE,
)
_ADD_RE = re.compile(
    r"^add\s+`(?P<id>[a-z0-9_]+)`\s*\((?P<tier>position|commitment|identity)\)"
    r"\s*:\s*(?P<text>.+)$",
    re.IGNORECASE,
)
_RECLASSIFY_RE = re.compile(
    r"^reclassify\s+`(?P<id>[a-z0-9_]+)`\s+to\s+(?P<tier>position|commitment|identity)\s*$",
    re.IGNORECASE,
)
_RETIRE_RE = re.compile(r"^retire\s+`(?P<id>[a-z0-9_]+)`\s*$", re.IGNORECASE)

_FIELD_RE = re.compile(r"^(?P<key>trigger|grounds)\s*:\s*(?P<value>.+)$", re.IGNORECASE)

TIER_ORDER = {"position": 0, "commitment": 1, "identity": 2}


@dataclass
class StatementProposal:
    """One proposed change to an actor's ledger."""

    kind: str  # "modify" | "add" | "reclassify" | "retire"
    statement_id: str
    tier: Optional[str] = None
    text: Optional[str] = None
    trigger: str = ""
    grounds: str = ""
    raw: str = ""


@dataclass
class ProposalOutcome:
    """What happened to one proposal, for the changelog."""

    proposal: StatementProposal
    verdict: str  # "applied" | "rejected-structural" | "rejected-relevance"
    reason: str = ""
    evidence: str = ""


def parse_statement_changes(output: str) -> list[StatementProposal]:
    """Extract proposals from an actor's response.

    An absent section, or an explicit "No statement changes.", yields an empty
    list. That is the expected answer in most turns and is not an error.
    """
    match = _SECTION_RE.search(output)
    if not match:
        return []

    body = output[match.end():]
    next_section = _NEXT_SECTION_RE.search(body)
    if next_section:
        body = body[: next_section.start()]

    if body.strip().lower().rstrip(".") in NO_CHANGES_MARKERS:
        return []

    proposals: list[StatementProposal] = []
    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        indented = line.startswith(("  ", "\t"))
        item = re.sub(r"^[-*]\s+", "", stripped)
        if not item:
            continue

        field_match = _FIELD_RE.match(item)
        if field_match and proposals:
            key = field_match.group("key").lower()
            value = field_match.group("value").strip()
            if key == "trigger":
                proposals[-1].trigger = value
            else:
                proposals[-1].grounds = value
            continue

        if indented and proposals and not _looks_like_proposal(item):
            # Wrapped continuation of the previous field.
            continue

        parsed = _parse_proposal_line(item)
        if parsed:
            proposals.append(parsed)

    return proposals


def _looks_like_proposal(item: str) -> bool:
    return any(
        pattern.match(item)
        for pattern in (_MODIFY_RE, _ADD_RE, _RECLASSIFY_RE, _RETIRE_RE)
    )


def _parse_proposal_line(item: str) -> Optional[StatementProposal]:
    match = _MODIFY_RE.match(item)
    if match:
        return StatementProposal(
            kind="modify",
            statement_id=match.group("id"),
            tier=(match.group("tier") or "").lower() or None,
            text=match.group("text").strip(),
            raw=item,
        )

    match = _ADD_RE.match(item)
    if match:
        return StatementProposal(
            kind="add",
            statement_id=match.group("id"),
            tier=match.group("tier").lower(),
            text=match.group("text").strip(),
            raw=item,
        )

    match = _RECLASSIFY_RE.match(item)
    if match:
        return StatementProposal(
            kind="reclassify",
            statement_id=match.group("id"),
            tier=match.group("tier").lower(),
            raw=item,
        )

    match = _RETIRE_RE.match(item)
    if match:
        return StatementProposal(kind="retire", statement_id=match.group("id"), raw=item)

    return None


def effective_tier(proposal: StatementProposal, actor: Actor) -> Optional[str]:
    """The tier whose rules govern this proposal.

    Reversals are governed by what the statement currently is. Adding a new
    statement, or upgrading an existing one, is self-binding rather than a
    reversal: the actor is staking itself to something, which it may always do
    and will pay for later.
    """
    existing = actor.statement(proposal.statement_id)

    if proposal.kind == "add":
        return None
    if proposal.kind == "reclassify":
        if existing is None or proposal.tier is None:
            return None
        if TIER_ORDER[proposal.tier] > TIER_ORDER[existing.tier]:
            return None  # upgrade: self-binding
        return existing.tier
    if existing is None:
        return None
    return existing.tier


def requires_trigger(proposal: StatementProposal, actor: Actor) -> bool:
    """Whether this proposal must name a triggering development."""
    tier = effective_tier(proposal, actor)
    return tier in GATED_TIERS


def check_structure(proposal: StatementProposal, actor: Actor) -> Optional[str]:
    """Formatting-only validation. Returns a rejection reason, or None to pass.

    Deliberately shallow, in line with the project's parser philosophy: unknown
    ids are skipped the way unknown event ids are, rather than raising.
    """
    existing = actor.statement(proposal.statement_id)

    if proposal.kind == "add":
        if existing is not None:
            return f"statement id '{proposal.statement_id}' already exists"
        if not proposal.text:
            return "added statement has no text"
        if proposal.tier not in STATEMENT_TIERS:
            return f"invalid tier '{proposal.tier}'"
    else:
        if existing is None:
            return f"no statement with id '{proposal.statement_id}'"

    if proposal.kind == "modify":
        if not proposal.text:
            return "modified statement has no text"
        if existing is not None and proposal.text.strip() == existing.text.strip():
            return "modified text is identical to the current text"
        if proposal.tier is not None and proposal.tier not in STATEMENT_TIERS:
            return f"invalid tier '{proposal.tier}'"

    if proposal.kind == "reclassify":
        if proposal.tier not in STATEMENT_TIERS:
            return f"invalid tier '{proposal.tier}'"
        if existing is not None and proposal.tier == existing.tier:
            return f"already at tier '{proposal.tier}'"

    if requires_trigger(proposal, actor) and not proposal.trigger.strip():
        tier = effective_tier(proposal, actor)
        return f"a {tier}-tier change must name a Trigger"

    return None


def apply_proposal(actor: Actor, proposal: StatementProposal) -> None:
    """Apply an accepted proposal to the actor's live ledger."""
    if proposal.kind == "add":
        actor.statements.append(
            Statement(id=proposal.statement_id, tier=proposal.tier, text=proposal.text)
        )
        return

    existing = actor.statement(proposal.statement_id)
    if existing is None:
        return

    if proposal.kind == "retire":
        actor.statements = [s for s in actor.statements if s.id != proposal.statement_id]
    elif proposal.kind == "modify":
        existing.text = proposal.text
        if proposal.tier is not None:
            existing.tier = proposal.tier
    elif proposal.kind == "reclassify":
        existing.tier = proposal.tier


def render_ledger(actor: Actor) -> str:
    """Render an actor's ledger for injection into its prompt."""
    if not actor.statements:
        return "(none)"
    return "\n".join(
        f"- `{s.id}` ({s.tier}): {s.text}" for s in actor.statements
    )


def render_statements_file(actor: Actor, turn: int, outcomes: list[ProposalOutcome]) -> str:
    """Render the per-turn statements artifact.

    The full ledger is written every turn, changed or not, so a diff between
    consecutive turns is empty unless a change was accepted. Silent drift is
    structurally impossible to hide.
    """
    lines = [
        f"# Statements: {actor.name} (turn {turn})",
        "",
        "## Ledger",
        "",
        render_ledger(actor),
        "",
        "## Changes this turn",
        "",
    ]

    if not outcomes:
        lines.append("No statement changes.")
    else:
        for outcome in outcomes:
            proposal = outcome.proposal
            lines.append(f"- **{proposal.kind}** `{proposal.statement_id}` — {outcome.verdict}")
            if proposal.tier:
                lines.append(f"  - Tier: {proposal.tier}")
            if proposal.text:
                lines.append(f"  - Text: {proposal.text}")
            if proposal.trigger:
                lines.append(f"  - Trigger: {proposal.trigger}")
            if proposal.grounds:
                lines.append(f"  - Grounds: {proposal.grounds}")
            if outcome.evidence:
                lines.append(f"  - Evidence quoted: {outcome.evidence}")
            if outcome.reason:
                lines.append(f"  - Reason: {outcome.reason}")

    return "\n".join(lines) + "\n"


def parse_ledger_file(content: str) -> list[Statement]:
    """Read a ledger back out of a persisted statements file.

    Only the ``## Ledger`` section is read; the changelog below it is a record
    for humans and for analysis, not state.
    """
    lines = content.split("\n")
    statements: list[Statement] = []
    in_ledger = False

    for line in lines:
        stripped = line.strip()
        lowered = stripped.lower()
        if lowered.startswith("## ledger"):
            in_ledger = True
            continue
        if in_ledger and stripped.startswith("## "):
            break
        if not in_ledger or not stripped:
            continue

        item = re.sub(r"^[-*]\s+", "", stripped)
        match = _LEDGER_LINE_RE.match(item)
        if match:
            statements.append(
                Statement(
                    id=match.group("id"),
                    tier=match.group("tier"),
                    text=match.group("text").strip(),
                )
            )

    return statements


_LEDGER_LINE_RE = re.compile(
    r"^`(?P<id>[a-z0-9_]+)`\s*\((?P<tier>position|commitment|identity)\)\s*:\s*(?P<text>.+)$"
)
