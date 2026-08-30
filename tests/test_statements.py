"""Tests for actor statement ledgers and change proposals.

The behaviour under test is mostly about what does *not* happen: silence
leaves the ledger alone, and a reversal without grounds does not land.
"""

import pytest

from scenario_lab.models import Actor, Statement
from scenario_lab.statements import (
    ProposalOutcome,
    StatementProposal,
    apply_proposal,
    check_structure,
    effective_tier,
    parse_ledger_file,
    parse_statement_changes,
    render_ledger,
    render_statements_file,
    requires_trigger,
)


def make_actor() -> Actor:
    return Actor(
        id="c",
        name="Centre Party",
        short_description="",
        long_description="",
        initial_statements=[
            Statement("no_sd", "commitment", "We will not support an SD-dependent government."),
            Statement("price_it", "position", "Convert our position into concessions."),
            Statement("we_are_centre", "identity", "We are the constructive centre."),
        ],
    )


# --- Silence means persistence ------------------------------------------------

def test_no_section_means_no_changes():
    assert parse_statement_changes("## Actions\n\nWe negotiate.") == []


@pytest.mark.parametrize("body", ["No statement changes.", "None", "no changes"])
def test_explicit_none_means_no_changes(body):
    output = f"## Statement changes\n\n{body}\n\n## Actions\n\nWe wait."
    assert parse_statement_changes(output) == []


def test_ledger_survives_a_turn_with_no_proposals():
    actor = make_actor()
    before = render_ledger(actor)
    for proposal in parse_statement_changes("## Actions\n\nNothing happened."):
        apply_proposal(actor, proposal)
    assert render_ledger(actor) == before


# --- Parsing ------------------------------------------------------------------

def test_parses_each_proposal_kind():
    output = """## Statement changes

- modify `no_sd` (commitment): We will tolerate an SD-dependent government.
  - Trigger: The third prime-ministerial vote failed.
  - Grounds: A fourth failure forces an extraordinary election.
- reclassify `we_are_centre` to commitment
  - Trigger: Coalition talks collapsed.
- add `open_to_m` (position): Explore a tax deal.
  - Grounds: They opened the channel.
- retire `price_it`
  - Trigger: There is nothing left to price.

## Actions
"""
    proposals = parse_statement_changes(output)
    assert [p.kind for p in proposals] == ["modify", "reclassify", "add", "retire"]
    assert proposals[0].trigger == "The third prime-ministerial vote failed."
    assert proposals[0].grounds.startswith("A fourth failure")
    assert proposals[2].tier == "position"


def test_parsing_stops_at_the_next_section():
    output = """## Statement changes

- add `a_thing` (position): Something.

## Actions

- modify `no_sd` (commitment): This is prose in the actions section.
"""
    assert [p.statement_id for p in parse_statement_changes(output)] == ["a_thing"]


# --- Which changes need grounds ----------------------------------------------

def test_reversing_a_commitment_needs_a_trigger():
    actor = make_actor()
    proposal = StatementProposal("modify", "no_sd", text="We might support one after all.")
    assert requires_trigger(proposal, actor) is True
    assert "must name a Trigger" in (check_structure(proposal, actor) or "")


def test_adjusting_a_position_does_not():
    actor = make_actor()
    proposal = StatementProposal("modify", "price_it", text="Convert it into rural investment.")
    assert requires_trigger(proposal, actor) is False
    assert check_structure(proposal, actor) is None


def test_staking_yourself_to_something_new_needs_no_trigger():
    """Adding or upgrading binds the actor rather than releasing it."""
    actor = make_actor()
    added = StatementProposal("add", "new_line", tier="commitment", text="We now promise this.")
    assert requires_trigger(added, actor) is False
    assert check_structure(added, actor) is None

    upgrade = StatementProposal("reclassify", "price_it", tier="identity")
    assert effective_tier(upgrade, actor) is None
    assert requires_trigger(upgrade, actor) is False


def test_downgrading_needs_grounds_at_the_current_tier():
    actor = make_actor()
    downgrade = StatementProposal("reclassify", "we_are_centre", tier="position")
    assert effective_tier(downgrade, actor) == "identity"
    assert requires_trigger(downgrade, actor) is True


def test_a_modify_bundling_a_downgrade_is_gated_by_the_existing_tier():
    """`modify `id` (position)` on a commitment is a reversal plus a downgrade.

    The gate must read what the statement currently IS, not the tier named in
    the proposal -- otherwise every gated change could be laundered through a
    bundled tier drop.
    """
    actor = make_actor()
    proposal = StatementProposal(
        "modify", "no_sd", tier="position", text="We might support one after all."
    )
    assert effective_tier(proposal, actor) == "commitment"
    assert requires_trigger(proposal, actor) is True
    assert "must name a Trigger" in (check_structure(proposal, actor) or "")

    proposal.trigger = "The third prime-ministerial vote failed this turn."
    assert check_structure(proposal, actor) is None
    apply_proposal(actor, proposal)
    moved = actor.statement("no_sd")
    assert moved.tier == "position"
    assert moved.text == "We might support one after all."


# --- Structural rejections ----------------------------------------------------

def test_unknown_id_is_rejected_not_raised():
    actor = make_actor()
    proposal = StatementProposal("retire", "does_not_exist")
    assert "no statement with id" in (check_structure(proposal, actor) or "")


def test_duplicate_add_is_rejected():
    actor = make_actor()
    proposal = StatementProposal("add", "no_sd", tier="position", text="Again.")
    assert "already exists" in (check_structure(proposal, actor) or "")


def test_a_modify_that_changes_nothing_is_rejected():
    actor = make_actor()
    proposal = StatementProposal(
        "modify", "price_it", text="Convert our position into concessions."
    )
    assert "identical" in (check_structure(proposal, actor) or "")


def test_invalid_tier_is_rejected():
    actor = make_actor()
    proposal = StatementProposal("reclassify", "price_it", tier="sacred")
    assert "invalid tier" in (check_structure(proposal, actor) or "")


# --- Application --------------------------------------------------------------

def test_apply_modify_reclassify_add_and_retire():
    actor = make_actor()
    apply_proposal(actor, StatementProposal(
        "modify", "no_sd", text="New text.", trigger="t"))
    apply_proposal(actor, StatementProposal("reclassify", "price_it", tier="commitment"))
    apply_proposal(actor, StatementProposal(
        "add", "fresh", tier="position", text="Fresh."))
    apply_proposal(actor, StatementProposal("retire", "we_are_centre", trigger="t"))

    ledger = {s.id: s for s in actor.statements}
    assert ledger["no_sd"].text == "New text."
    assert ledger["price_it"].tier == "commitment"
    assert ledger["fresh"].text == "Fresh."
    assert "we_are_centre" not in ledger


def test_an_invalid_tier_cannot_reach_the_model():
    with pytest.raises(ValueError, match="expected one of"):
        Statement("x", "sacred", "text")


# --- Persistence round trip ---------------------------------------------------

def test_ledger_round_trips_through_the_statements_file():
    actor = make_actor()
    rendered = render_statements_file(actor, 3, [])
    loaded = parse_ledger_file(rendered)
    assert [(s.id, s.tier, s.text) for s in loaded] == [
        (s.id, s.tier, s.text) for s in actor.statements
    ]


def test_statements_file_records_rejections_as_visibly_as_acceptances():
    actor = make_actor()
    outcomes = [
        ProposalOutcome(
            StatementProposal("modify", "no_sd", text="Reversed.", trigger="A vote failed."),
            "applied",
            evidence="the third vote failed",
        ),
        ProposalOutcome(
            StatementProposal("retire", "we_are_centre", trigger="It rained."),
            "rejected-relevance",
            "the weather does not bear on what the party is",
        ),
    ]
    rendered = render_statements_file(actor, 4, outcomes)
    assert "applied" in rendered
    assert "rejected-relevance" in rendered
    assert "the weather does not bear" in rendered


def test_a_quiet_turn_still_writes_the_whole_ledger():
    """So a diff between consecutive turns is empty rather than absent."""
    actor = make_actor()
    rendered = render_statements_file(actor, 5, [])
    assert "No statement changes." in rendered
    assert "no_sd" in rendered


def test_a_proposal_written_as_a_code_span_is_still_read():
    """The prompt states the required form wrapped in double backticks, so models
    copy the wrapper; before this was stripped, every such proposal parsed as
    nothing at all and the actor silently lost the statement."""
    output = (
        "## Statement changes\n"
        "``add `standing_commitment` (commitment): Secure the capacity to act "
        "independently.``\n"
    )
    proposals = parse_statement_changes(output)
    assert [(p.kind, p.statement_id, p.tier) for p in proposals] == [
        ("add", "standing_commitment", "commitment")
    ]
    assert proposals[0].text == "Secure the capacity to act independently."


def test_a_bare_proposal_is_unaffected_by_code_span_stripping():
    """The unwrapped form is what the older pinned road files use."""
    output = (
        "## Statement changes\n"
        "add `standing_commitment` (commitment): Secure the capacity to act "
        "independently.\n"
    )
    assert len(parse_statement_changes(output)) == 1


def test_a_single_backtick_pair_is_left_alone():
    """`retire `x`` ends in a backtick of its own, so one pair stays ambiguous."""
    output = "## Statement changes\nretire `we_are_centre`\n"
    proposals = parse_statement_changes(output)
    assert [(p.kind, p.statement_id) for p in proposals] == [("retire", "we_are_centre")]
