"""Private negotiation rounds between actors (v5 actors phase).

Actors exchange short notes that only the recipients see, before describing
their actions. Python owns delivery lists and persistence only: who may write
to whom, per-actor round participation, parsing, and the artifacts. Content
is never judged -- a note means whatever its recipient makes of it, including
quoting it to a third actor. Leaking is possible by design, not by accident.

Write form mirrors the store: one JSON block under a ``## Messages`` header.
An absent section (or ``No messages.``) means silence, which is the common
case and not a fault -- unlike store writes, where silence would hide loss.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional


MESSAGES_HEADER_RE = re.compile(r"^##\s+messages\s*$", re.IGNORECASE | re.MULTILINE)
NO_MESSAGES_MARKERS = ("no messages", "none", "nothing", "no private messages")


@dataclass
class NegotiationMessage:
    """One delivered private note."""

    round: int
    sender: str
    recipient: str
    text: str


@dataclass
class RejectedMessage:
    """A note that was written but not delivered, and why."""

    round: int
    sender: str
    recipient: str
    reason: str


def _messages_section(output: str) -> Optional[str]:
    """The text under the ``## Messages`` header, if the response has one."""
    match = MESSAGES_HEADER_RE.search(output)
    if not match:
        return None
    rest = output[match.end():]
    next_header = re.search(r"^##\s+\S", rest, re.MULTILINE)
    return rest[: next_header.start()] if next_header else rest


def parse_message_block(output: str, round: int, sender: str) -> tuple[list[dict], list[str]]:
    """Parse one actor's ``## Messages`` section into candidate entries.

    Returns ``(entries, malformed)`` where entries hold ``to``/``text`` and
    malformed holds human-readable reasons. One bad entry never kills the
    rest -- the same per-entry rule the store and the events step follow.
    Silence (absent section or a no-messages marker) parses to nothing.
    """
    section = _messages_section(output)
    if section is None:
        return [], []
    stripped = section.strip()
    if not stripped or stripped.strip("`*_").strip().lower() in NO_MESSAGES_MARKERS:
        return [], []

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", section, re.DOTALL)
    raw = fenced.group(1) if fenced else stripped
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        brace = re.search(r"\{.*\}", section, re.DOTALL)
        if not brace:
            return [], ["no readable {\"messages\": [...]} block under '## Messages'"]
        try:
            payload = json.loads(brace.group(0))
        except json.JSONDecodeError:
            return [], ["no readable {\"messages\": [...]} block under '## Messages'"]

    items = payload.get("messages") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return [], ["'## Messages' block must hold {\"messages\": [...]}"]
    entries: list[dict] = []
    malformed: list[str] = []
    for index, item in enumerate(items):
        where = f"message {index + 1} from {sender}"
        if not isinstance(item, dict):
            malformed.append(f"{where}: not an object, dropped")
            continue
        to = item.get("to")
        text = item.get("text")
        if not isinstance(to, str) or not to.strip():
            malformed.append(f"{where}: missing recipient, dropped")
            continue
        if not isinstance(text, str) or not text.strip():
            malformed.append(f"{where}: empty text, dropped")
            continue
        entries.append({"to": to.strip(), "text": text.strip()})
    return entries, malformed


def deliver(
    entries: list[dict],
    sender: str,
    round: int,
    actor_ids: list[str],
    contacts: dict[str, list[str]],
) -> tuple[list[NegotiationMessage], list[RejectedMessage]]:
    """Apply the delivery policy to parsed entries.

    Unknown recipients and self-sends are rejected (a typo must not become a
    broadcast, and talking to yourself is not a negotiation). Where the
    scenario restricts contacts, a note outside the sender's list is rejected
    with the reason recorded. Matching is case-insensitive on ids.
    """
    known = {actor_id.lower(): actor_id for actor_id in actor_ids}
    allowed = contacts.get(sender)
    allowed_ids = {a.lower() for a in allowed} if allowed is not None else None
    delivered: list[NegotiationMessage] = []
    rejected: list[RejectedMessage] = []
    for entry in entries:
        wanted = entry["to"].lower()
        recipient = known.get(wanted)
        if recipient is None:
            rejected.append(RejectedMessage(round, sender, entry["to"], "unknown actor"))
            continue
        if recipient == sender:
            rejected.append(RejectedMessage(round, sender, entry["to"], "cannot message yourself"))
            continue
        if allowed_ids is not None and recipient.lower() not in allowed_ids:
            rejected.append(
                RejectedMessage(
                    round, sender, entry["to"],
                    f"{sender} may only write to {', '.join(sorted(allowed))}",
                )
            )
            continue
        delivered.append(NegotiationMessage(round, sender, recipient, entry["text"]))
    return delivered, rejected


def render_inbox(messages: list[NegotiationMessage]) -> str:
    """What one actor sees: each note with its sender and round."""
    if not messages:
        return ""
    return "\n".join(
        f"Message from {message.sender} (round {message.round}): {message.text}"
        for message in messages
    )


def render_record(delivered: list[NegotiationMessage]) -> str:
    """The Game Master record: every private note, sender to recipient.

    Notes are private between actors but never from the Game Master, which
    judges action success: it needs the agreements to hold actors to and the
    leaks to price. One line per note; empty when nothing was exchanged.
    """
    if not delivered:
        return ""
    return "\n".join(
        f"{message.sender} → {message.recipient} "
        f"(round {message.round}): {message.text}"
        for message in delivered
    )


def render_sent(
    delivered: list[NegotiationMessage], rejected: list[RejectedMessage]
) -> str:
    """What one sender sees of its own outbox: sent notes and rejections.

    A sender that never sees its own offer cannot act on the reply to it,
    and a note that died in delivery must say so -- silence would read as
    "they ignored me" and poison the next round.
    """
    lines = [
        f"You wrote to {message.recipient} (round {message.round}): {message.text}"
        for message in delivered
    ]
    lines.extend(
        f"Your note to {item.recipient} was not delivered: {item.reason}"
        for item in rejected
    )
    return "\n".join(lines)


def participants_for_round(
    actor_ids: list[str],
    round: int,
    limit: int,
    actor_rounds: dict[str, int],
) -> list[str]:
    """Actors joining this round, in declaration order.

    An actor joins rounds 1..k where k is its ``actor_rounds`` entry or the
    round ``limit`` (the scenario's ``max_rounds`` -- extension rounds seat
    everyone not explicitly capped, and die on silence anyway). An actor
    that sits out still sees the final actions like any other turn.
    """
    return [
        actor_id
        for actor_id in actor_ids
        if actor_rounds.get(actor_id, limit) >= round >= 1
    ]
