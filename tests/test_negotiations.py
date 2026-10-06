"""Negotiation rounds: parsing, delivery policy, and the actors-phase flow."""

import json
from pathlib import Path

from scenario_lab.loader import load_scenario
from scenario_lab.llm import MockLLMClient
from scenario_lab.negotiations import (
    deliver,
    parse_message_block,
    participants_for_round,
    render_inbox,
)
from scenario_lab.orchestrator import Orchestrator
from scenario_lab.output import OutputManager

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_parse_valid_block():
    entries, malformed = parse_message_block(
        '## Messages\n```json\n{"messages": [{"to": "b", "text": "Hello."}]}\n```\n',
        round=1,
        sender="a",
    )
    assert entries == [{"to": "b", "text": "Hello."}]
    assert malformed == []


def test_parse_silence_is_not_a_fault():
    for body in ("", "No messages.", "## Actions\nDoing things."):
        entries, malformed = parse_message_block(body, 1, "a")
        assert entries == [] and malformed == []


def test_parse_bad_entry_does_not_kill_good_ones():
    entries, malformed = parse_message_block(
        '## Messages\n{"messages": [{"to": "b", "text": "Hi"}, {"text": "lost"}, "nope"]}',
        1,
        "a",
    )
    assert entries == [{"to": "b", "text": "Hi"}]
    assert len(malformed) == 2


def test_deliver_policy():
    delivered, rejected = deliver(
        [{"to": "B", "text": "Hi"}, {"to": "ghost", "text": "Boo"}, {"to": "a", "text": "Me"}],
        sender="a",
        round=1,
        actor_ids=["a", "b"],
        contacts={},
    )
    assert [(m.recipient, m.text) for m in delivered] == [("b", "Hi")]
    assert sorted(r.recipient for r in rejected) == ["a", "ghost"]


def test_deliver_contacts_restriction():
    delivered, rejected = deliver(
        [{"to": "c", "text": "Hi"}],
        sender="a",
        round=1,
        actor_ids=["a", "b", "c"],
        contacts={"a": ["b"]},
    )
    assert delivered == []
    assert len(rejected) == 1 and "only write" in rejected[0].reason


def test_participants_for_round():
    actors = ["a", "b"]
    assert participants_for_round(actors, 1, 2, {}) == ["a", "b"]
    assert participants_for_round(actors, 2, 2, {"b": 1}) == ["a"]
    assert participants_for_round(actors, 1, 2, {"b": 0}) == ["a"]
    # Extension rounds seat everyone not explicitly capped.
    assert participants_for_round(actors, 3, 3, {}) == ["a", "b"]
    assert participants_for_round(actors, 3, 3, {"a": 2}) == ["b"]


def test_render_inbox_empty():
    assert render_inbox([]) == ""


def _negotiation_scenario(tmp_path, **overrides):
    fake_dir = tmp_path / "sweden-ai-2030"
    fake_dir.mkdir(exist_ok=True)
    for name in ("scenario.yaml", "metrics.md"):
        link = fake_dir / name
        if not link.exists():
            link.symlink_to(REPO_ROOT / "scenarios/sweden-ai-2030" / name)
    scenario = load_scenario("scenarios/sweden-ai-2030")
    cfg = scenario.config.negotiations
    cfg.enabled = True
    cfg.rounds = overrides.get("rounds", 1)
    cfg.max_rounds = overrides.get("max_rounds", 1)
    cfg.contacts = overrides.get("contacts", {})
    manager = OutputManager(scenario, fake_dir)
    run_dir = manager.start_run()
    return scenario, manager, run_dir


def _negotiation_client():
    return MockLLMClient(
        {
            # Negotiation rounds first: the round prompt also contains the
            # action marker text, so this key must match first.
            "private negotiations": (
                "## Messages\n```json\n"
                '{"messages": [{"to": "PLACEHOLDER", "text": "Let us coordinate."}]}\n'
                "```\n"
            ),
            "which actions you want to take during the turn": (
                "## Actions\n\nWe act."
            ),
        }
    )


def test_negotiation_round_reaches_recipient(tmp_path):
    scenario, manager, run_dir = _negotiation_scenario(tmp_path)
    actor_ids = list(scenario.actors.keys())
    sender, recipient = actor_ids[0], actor_ids[1]

    client = _negotiation_client()
    # Route every negotiation reply to the second actor.
    client.responses["private negotiations"] = (
        "## Messages\n```json\n"
        '{"messages": [{"to": "%s", "text": "Let us coordinate."}]} \n```\n' % recipient
    )
    orchestrator = Orchestrator(scenario, client, manager)
    inboxes, outboxes, delivered = orchestrator._run_negotiations(1, [])

    received = [(m.sender, m.recipient) for m in inboxes[recipient]]
    assert (sender, recipient) in received or any(
        m.recipient == recipient for m in inboxes[recipient]
    )
    assert any(m.recipient == recipient for m in delivered)
    messages = json.loads((run_dir / "turn-01" / "2-negotiations" / "messages.json").read_text())
    assert any(m["to"] == recipient for m in messages)

    # The recipient's action prompt carries the note; the sender's carries
    # its own offer; the Game Master record names both sides.
    orchestrator._run_actors_step(1, [], inboxes, outboxes)
    action_prompts = [
        user for system, user in client.calls if "which actions" in (system + user).lower()
    ]
    recipient_calls = [p for p in action_prompts if "Let us coordinate" in p]
    assert recipient_calls, "recipient never saw the note in its action prompt"
    assert any(
        "You wrote to" in p and "Let us coordinate" in p for p in action_prompts
    ), "sender never saw its own offer"
    from scenario_lab.negotiations import render_record

    record = render_record(delivered)
    assert sender in record and recipient in record


def test_round_prompts_carry_no_action_format():
    """A message round must not ask for actions in either prompt."""
    from scenario_lab.prompts import PromptBuilder

    scenario = load_scenario("scenarios/sweden-ai-2030")
    actor_id = next(iter(scenario.actors))
    builder = PromptBuilder(scenario)
    system, user = builder.build_actor_prompt(
        actor_id, 1, [], negotiation_instructions="Round 1.", negotiation_round=True
    )
    assert "Heading level 2: Messages" in system
    assert "Heading level 2: Messages" in user
    assert "Heading level 2: Actions" not in system
    assert "Heading level 2: Actions" not in user

    system, user = builder.build_actor_prompt(actor_id, 1, [])
    assert "Heading level 2: Actions" in system
    assert "Heading level 2: Actions" in user
    assert "Heading level 2: Messages" not in system
    assert "Heading level 2: Messages" not in user


def _message_client(text, recipient):
    client = _negotiation_client()
    client.responses["private negotiations"] = (
        "## Messages\n```json\n"
        '{"messages": [{"to": "%s", "text": "%s"}]} \n```\n' % (recipient, text)
    )
    return client


def test_negotiation_rerun_replaces_aborted_attempt(tmp_path):
    """Rerunning the actors phase must not merge two attempts' notes."""
    scenario, manager, run_dir = _negotiation_scenario(tmp_path, rounds=2, max_rounds=2)
    actor_ids = list(scenario.actors.keys())
    recipient = actor_ids[1]
    orchestrator = Orchestrator(scenario, _message_client("First.", recipient), manager)
    orchestrator._run_negotiations(1, [])
    nego_dir = run_dir / "turn-01" / "2-negotiations"
    assert nego_dir.is_dir()

    orchestrator2 = Orchestrator(scenario, _message_client("Second.", recipient), manager)
    orchestrator2._run_negotiations(1, [])
    messages = json.loads((nego_dir / "messages.json").read_text())
    assert messages
    assert all(m["text"] == "Second." for m in messages)
    rounds = sorted(nego_dir.glob("round-*.md"))
    assert len(rounds) == 2


def test_metrics_prompt_carries_negotiation_record():
    """The Game Master sees every private note; silence renders nothing."""
    from scenario_lab.prompts import PromptBuilder

    scenario = load_scenario("scenarios/sweden-ai-2030")
    scenario.custom_user_prompts.pop("metrics_update", None)
    builder = PromptBuilder(scenario)
    _, user = builder.build_metrics_prompt(
        1, {}, [], "a → b (round 1): Let us coordinate."
    )
    assert "a → b (round 1): Let us coordinate." in user
    _, silent = builder.build_metrics_prompt(1, {}, [])
    assert "Private notes" not in silent


def test_negotiations_disabled_by_default(tmp_path):
    scenario = load_scenario("scenarios/sweden-ai-2030")
    assert scenario.config.negotiations.enabled is False


def test_validate_negotiations_contacts():
    from scenario_lab.validator import validate_negotiations

    scenario = load_scenario("scenarios/sweden-ai-2030")
    scenario.config.negotiations.enabled = True
    scenario.config.negotiations.contacts = {"ghost": ["government"]}
    errors, warnings = validate_negotiations(scenario)
    assert any("ghost" in e for e in errors)
    assert any("extra llm calls" in w.lower() or "extra" in w.lower() for w in warnings)


def test_validate_negotiations_stale_template():
    from scenario_lab.validator import validate_negotiations

    scenario = load_scenario("scenarios/sweden-ai-2030")
    scenario.config.negotiations.enabled = True
    scenario.custom_user_prompts["actor"] = "Act. {{world_state}}"
    _, warnings = validate_negotiations(scenario)
    assert any("negotiation_messages" in w for w in warnings)
