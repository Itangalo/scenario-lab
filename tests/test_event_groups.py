"""Mutually exclusive event families.

The failure these tests pin down is the one that motivated the mechanism: an
outcome that must happen did not, because a "certain" event's probability was
averaged across samples the model sometimes omitted it from, and the rule for
choosing between outcomes was applied from prose against a history the Game
Master could not see.
"""

import pytest

from scenario_lab.event_groups import (
    EventGroup,
    HistorySelector,
    parse_event_groups,
    resolve_group,
    select_from_history,
)


def group(**kwargs) -> EventGroup:
    base = dict(
        id="election",
        members=("consolidation", "alliance", "retrenchment"),
        resolution="exactly_one",
        due_turns=(5,),
        default="consolidation",
    )
    base.update(kwargs)
    return EventGroup(**base)


class TestParsing:
    def test_minimal_group(self):
        groups, errors = parse_event_groups(
            [{"id": "g", "members": ["a", "b"], "resolution": "at_most_one"}]
        )
        assert not errors
        assert groups[0].members == ("a", "b")
        assert groups[0].is_due(1) and groups[0].is_due(9)

    def test_exactly_one_requires_due_turns_and_default(self):
        _, errors = parse_event_groups(
            [{"id": "g", "members": ["a", "b"], "resolution": "exactly_one"}]
        )
        assert any("due_turns" in e for e in errors)

        _, errors = parse_event_groups(
            [
                {
                    "id": "g",
                    "members": ["a", "b"],
                    "resolution": "exactly_one",
                    "due_turns": [5],
                }
            ]
        )
        assert any("default" in e for e in errors)

    def test_rejects_single_member_and_unknown_resolution(self):
        _, errors = parse_event_groups([{"id": "g", "members": ["a"]}])
        assert any("at least two members" in e for e in errors)

        _, errors = parse_event_groups(
            [{"id": "g", "members": ["a", "b"], "resolution": "some_of"}]
        )
        assert any("invalid resolution" in e for e in errors)

    def test_default_must_be_a_member(self):
        _, errors = parse_event_groups(
            [
                {
                    "id": "g",
                    "members": ["a", "b"],
                    "resolution": "exactly_one",
                    "due_turns": [2],
                    "default": "c",
                }
            ]
        )
        assert any("not one of its members" in e for e in errors)

    def test_select_by_maps_only_to_members(self):
        _, errors = parse_event_groups(
            [
                {
                    "id": "g",
                    "members": ["a", "b"],
                    "select_by": {"map": {"src": "elsewhere"}},
                }
            ]
        )
        assert any("non-members" in e for e in errors)


class TestExactlyOne:
    def test_one_member_always_fires_even_with_no_weights(self):
        """The case that broke: nobody listed the event, so nothing happened."""
        outcome = resolve_group(group(), weights={}, roll=0.99)
        assert outcome.chosen == "consolidation"
        assert outcome.basis == "default"

    def test_weights_decide_which(self):
        weights = {"consolidation": 0.2, "alliance": 0.2, "retrenchment": 0.6}
        # Normalised cut points: 0.2, 0.4, 1.0
        assert resolve_group(group(), weights, roll=0.1).chosen == "consolidation"
        assert resolve_group(group(), weights, roll=0.3).chosen == "alliance"
        assert resolve_group(group(), weights, roll=0.7).chosen == "retrenchment"

    def test_exactly_one_fires_across_the_whole_roll_range(self):
        weights = {"consolidation": 0.1, "alliance": 0.1, "retrenchment": 0.1}
        chosen = {
            resolve_group(group(), weights, roll=r / 100).chosen for r in range(100)
        }
        assert None not in chosen
        assert chosen <= set(group().members)

    def test_due_turns_gate_the_group(self):
        g = group(due_turns=(5,))
        assert g.is_due(5)
        assert not g.is_due(4)


class TestAtMostOne:
    def test_summed_weight_decides_whether(self):
        g = group(resolution="at_most_one", due_turns=(), default=None)
        weights = {"consolidation": 0.1, "alliance": 0.1}
        assert resolve_group(g, weights, roll=0.9).chosen is None
        assert resolve_group(g, weights, roll=0.05).chosen is not None

    def test_never_more_than_one(self):
        g = group(resolution="at_most_one", due_turns=(), default=None)
        weights = {"consolidation": 0.4, "alliance": 0.4, "retrenchment": 0.4}
        for r in range(100):
            outcome = resolve_group(g, weights, roll=r / 100)
            assert outcome.chosen is None or outcome.chosen in g.members


class TestHistorySelection:
    selector = HistorySelector(
        mapping={
            "campaign_backlash": "retrenchment",
            "campaign_atlanticist": "alliance",
            "campaign_security_hawk": "consolidation",
        },
        precedence=("campaign_backlash", "campaign_atlanticist", "campaign_security_hawk"),
    )

    def test_most_recent_wins(self):
        log = [
            {"turn": 3, "id": "campaign_security_hawk"},
            {"turn": 4, "id": "campaign_backlash"},
        ]
        assert select_from_history(self.selector, log) == "retrenchment"

    def test_precedence_breaks_a_tie_inside_one_turn(self):
        log = [
            {"turn": 4, "id": "campaign_security_hawk"},
            {"turn": 4, "id": "campaign_backlash"},
        ]
        assert select_from_history(self.selector, log) == "retrenchment"

    def test_nothing_mapped_selects_nothing(self):
        assert select_from_history(self.selector, [{"turn": 2, "id": "bio_incident"}]) is None

    def test_current_turn_is_excluded(self):
        log = [{"turn": 5, "id": "campaign_backlash"}]
        assert select_from_history(self.selector, log, before_turn=5) is None

    def test_group_falls_back_to_default_when_no_current_fired(self):
        """The observed bug: backlash fired, yet every run recorded the default."""
        g = group(select_by=self.selector)
        outcome = resolve_group(g, weights={}, roll=0.5, event_log=[], turn=5)
        assert outcome.chosen == "consolidation"
        assert outcome.basis == "default"

    def test_group_follows_the_record_when_a_current_fired(self):
        g = group(select_by=self.selector)
        log = [{"turn": 4, "id": "campaign_backlash"}]
        outcome = resolve_group(g, weights={}, roll=0.5, event_log=log, turn=5)
        assert outcome.chosen == "retrenchment"
        assert outcome.basis == "history"

    def test_history_ignores_the_dice(self):
        g = group(select_by=self.selector)
        log = [{"turn": 4, "id": "campaign_atlanticist"}]
        chosen = {
            resolve_group(g, {}, roll=r / 10, event_log=log, turn=5).chosen
            for r in range(10)
        }
        assert chosen == {"alliance"}


class TestForcing:
    def test_a_forced_member_wins_the_group(self):
        outcome = resolve_group(
            group(), weights={"consolidation": 1.0}, roll=0.0, forced=("alliance",)
        )
        assert outcome.chosen == "alliance"
        assert outcome.basis == "forced"


class TestValidation:
    def test_unknown_member_is_an_error(self, tmp_path):
        from scenario_lab.models import Event, Scenario, ScenarioConfig
        from scenario_lab.validator import validate_event_groups

        scenario = Scenario.__new__(Scenario)
        scenario.events = [Event(id="alliance", description="", condition="", probability="10%")]
        scenario.config = ScenarioConfig(
            name="t",
            description="",
            start_date="2026",
            time_scale="1 year per turn",
            max_turns=5,
            actor_ids=["a"],
            event_groups=[group()],
        )
        errors, _ = validate_event_groups(scenario)
        assert any("consolidation" in e and "not an event" in e for e in errors)

    def test_due_turn_beyond_the_run_is_an_error(self):
        from scenario_lab.models import Event, Scenario, ScenarioConfig
        from scenario_lab.validator import validate_event_groups

        scenario = Scenario.__new__(Scenario)
        scenario.events = [
            Event(id=m, description="", condition="", probability="10%") for m in group().members
        ]
        scenario.config = ScenarioConfig(
            name="t",
            description="",
            start_date="2026",
            time_scale="1 year per turn",
            max_turns=3,
            actor_ids=["a"],
            event_groups=[group()],
        )
        errors, _ = validate_event_groups(scenario)
        assert any("outside the run" in e for e in errors)


class TestGroupMembersNeverRollAlone:
    """A member listed outside its group's due turns must not fire on its own.

    The group is the only thing that may trigger a member. Letting an
    off-schedule candidate fall through to an individual roll would mean an
    election could be held in 2027 because the model listed it.
    """

    def test_member_outside_due_turns_is_skipped(self, tmp_path):
        from scenario_lab.models import Event, Scenario, ScenarioConfig
        from scenario_lab.orchestrator import Orchestrator

        scenario = Scenario.__new__(Scenario)
        scenario.events = [
            Event(id=m, description="", condition="", probability="50%")
            for m in group().members
        ]
        scenario.config = ScenarioConfig(
            name="t",
            description="",
            start_date="2026",
            time_scale="1 year per turn",
            max_turns=6,
            actor_ids=["a"],
            event_groups=[group()],
        )
        scenario.occurred_events = set()
        scenario.event_log = []

        orchestrator = Orchestrator.__new__(Orchestrator)
        orchestrator.scenario = scenario
        orchestrator.random_seed = 1
        orchestrator.output_manager = None

        groups = list(scenario.config.event_groups)
        assert not groups[0].is_due(3)

        triggered, evaluations = [], []
        orchestrator._resolve_event_groups(3, groups, {}, {}, set(), triggered, evaluations)
        assert triggered == []
