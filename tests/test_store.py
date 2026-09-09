"""Tests for custody of declared persistent state (`scenario_lab/store.py`).

The mechanism exists because a measured 4.5% of proposed measures never
reached the portfolio and 0.6% of entries vanished from it with no stated
cause, in a scenario where the actor re-emitted the portfolio every turn. The
tests that matter most here are therefore not the parser tests but the custody
ones: that a turn which says nothing about a record leaves it exactly as it
was, and that no path exists by which an actor's silence removes anything.

Every command shape below is one an actor plausibly writes -- decorated with
backticks and asterisks, a turn written as prose, a heading at the wrong
level. The parser's job is to accept those; the store's job is to reject
anything that would put a value somewhere the schema says the actor does not
own.
"""

from __future__ import annotations

import json

import pytest

from scenario_lab.store import (
    Store,
    StoreSchemaError,
    StoreView,
    check_store_references,
    find_store_references,
    parse_store_changes,
    parse_store_schema,
    render_store_file,
    self_test,
)

SCHEMA = {
    "measures": {
        "scope": "actor",
        "columns": {
            "id": {"owner": "system", "type": "text"},
            "name": {"owner": "actor", "type": "text", "required": True},
            "category": {"owner": "actor", "type": "integer"},
            "size": {"owner": "actor", "type": "enum", "values": ["large", "small"]},
            "started_turn": {"owner": "system", "type": "turn"},
            "finish_turn": {"owner": "actor", "type": "turn", "required": True},
            "cost_per_turn": {
                "owner": "derived",
                "type": "integer",
                "from": "size",
                "map": {"large": 3, "small": 2},
            },
            "status": {
                "owner": "derived",
                "type": "text",
                "from": "finish_turn",
                "when_reached": "finished",
                "else": "running",
            },
        },
    }
}


@pytest.fixture
def store() -> Store:
    return Store(parse_store_schema(SCHEMA))


def apply(store: Store, turn: int, text: str, actor: str = "eu") -> list:
    """Run one turn's declared section the way the orchestrator does."""
    store.begin_turn(turn)
    commands, _malformed, _present = parse_store_changes(text)
    return [store.apply(command, actor, turn) for command in commands]


def add_two(store: Store) -> None:
    apply(
        store,
        1,
        "## Store changes\n"
        "- add measures: name = InvestAI Gigafactories; category = 4; size = large; finish_turn = 7\n"
        "- add measures: name = Incident Response Corps; category = 6; size = small; finish_turn = 3\n",
    )


# ---------------------------------------------------------------------------
# The defect this exists to remove
# ---------------------------------------------------------------------------


def test_silence_carries_records_forward(store: Store):
    """The whole point. A turn that says nothing changes nothing."""
    add_two(store)
    for turn in range(2, 10):
        apply(store, turn, "## Actions\n\nWe did some things.\n")
    assert len(store.live_records("measures")) == 2


def test_an_actor_cannot_drop_a_record_by_omission(store: Store):
    """There is no path from 'not mentioned' to 'gone'."""
    add_two(store)
    apply(
        store,
        2,
        "## Store changes\n"
        "- update measures M1: finish_turn = 8\n",
    )
    live = {r.id for r in store.live_records("measures")}
    assert live == {"M1", "M2"}


def test_removal_requires_an_explicit_command(store: Store):
    add_two(store)
    outcomes = apply(store, 2, "## Store changes\n- delete measures M2\n")
    assert outcomes[0].verdict == "applied"
    assert {r.id for r in store.live_records("measures")} == {"M1"}


def test_missing_section_is_reported_not_inferred(store: Store):
    """A missing section is detectable; a missing inline command never was."""
    _commands, _malformed, present = parse_store_changes("## Portfolio\n\n- something\n")
    assert present is False
    _commands, _malformed, present = parse_store_changes("## Store changes\n\nNo changes.\n")
    assert present is True


# ---------------------------------------------------------------------------
# Provenance is enforced, not requested
# ---------------------------------------------------------------------------


def test_system_column_cannot_be_written(store: Store):
    add_two(store)
    outcome = apply(store, 2, "## Store changes\n- update measures M1: started_turn = 5\n")[0]
    assert outcome.verdict == "rejected"
    assert "stamped by the framework" in outcome.reason
    assert store.live_records("measures")[0].fields["started_turn"] == 1


def test_derived_column_cannot_be_written(store: Store):
    add_two(store)
    outcome = apply(store, 2, "## Store changes\n- update measures M1: cost_per_turn = 1\n")[0]
    assert outcome.verdict == "rejected"
    assert "computed from" in outcome.reason


def test_unknown_column_is_a_rejection_not_an_addition(store: Store):
    outcome = apply(
        store, 1, "## Store changes\n- add measures: name = X; finish_turn = 3; colour = blue\n"
    )[0]
    assert outcome.verdict == "rejected"
    assert "no column 'colour'" in outcome.reason
    assert store.live_records("measures") == []


def test_required_columns_are_required(store: Store):
    outcome = apply(store, 1, "## Store changes\n- add measures: name = X\n")[0]
    assert outcome.verdict == "rejected"
    assert "finish_turn" in outcome.reason


def test_ids_are_assigned_by_python(store: Store):
    add_two(store)
    assert [r.id for r in store.live_records("measures")] == ["M1", "M2"]
    # And an id is never reused after a deletion, so a stale reference in a
    # later turn cannot silently address a different record.
    apply(store, 2, "## Store changes\n- delete measures M1\n")
    apply(store, 3, "## Store changes\n- add measures: name = Y; size = small; finish_turn = 9\n")
    assert [r.id for r in store.live_records("measures")] == ["M2", "M3"]


def test_the_actor_never_keys_on_names(store: Store):
    """Names are not keys, so a paraphrase cannot address a record at all.

    `check_portfolio_drift.py` needs a stopword list and a fuzzy word matcher because
    the Game Master renames measures between turns ("EU AI Incident Response
    Corps", "European AI Incident Response Corps"). A command addressed by
    name does not parse, so no paraphrase can ever reach the wrong record.
    """
    add_two(store)
    commands, malformed, _ = parse_store_changes(
        "## Store changes\n- update measures InvestAI Gigafactories: finish_turn = 9\n"
    )
    assert commands == []
    assert malformed == ["update measures InvestAI Gigafactories: finish_turn = 9"]
    assert store.live_records("measures")[0].fields["finish_turn"] == 7


# ---------------------------------------------------------------------------
# Forgiving on write, strict in store
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "written,expected",
    [
        ("large", "large"),
        ("Large", "large"),
        ("`large`", "large"),
        ("**large**", "large"),
        ("  LARGE  ", "large"),
    ],
)
def test_enum_decoration_is_normalised(store: Store, written: str, expected: str):
    apply(
        store,
        1,
        f"## Store changes\n- add measures: name = X; size = {written}; finish_turn = 4\n",
    )
    assert store.live_records("measures")[0].fields["size"] == expected


@pytest.mark.parametrize(
    "written,expected", [("7", 7), ("turn 7", 7), ("**7**", 7), ("Turn 7.", 7)]
)
def test_turn_is_read_out_of_prose(store: Store, written: str, expected: int):
    apply(store, 1, f"## Store changes\n- add measures: name = X; finish_turn = {written}\n")
    assert store.live_records("measures")[0].fields["finish_turn"] == expected


def test_unnormalisable_value_is_rejected_loudly(store: Store):
    outcome = apply(
        store, 1, "## Store changes\n- add measures: name = X; size = enormous; finish_turn = 4\n"
    )[0]
    assert outcome.verdict == "rejected"
    assert "must be one of large, small" in outcome.reason


# ---------------------------------------------------------------------------
# Parsing shapes an actor actually writes
# ---------------------------------------------------------------------------


def test_heading_level_is_not_load_bearing():
    for hashes in ("#", "##", "###", "####"):
        commands, _, present = parse_store_changes(
            f"{hashes} Store changes (required this turn)\n"
            "- add measures: name = X; finish_turn = 3\n"
        )
        assert present is True
        assert len(commands) == 1


def test_section_ends_at_the_next_heading_of_the_same_level():
    commands, _, _ = parse_store_changes(
        "## Store changes\n"
        "- add measures: name = X; finish_turn = 3\n"
        "\n"
        "## Priority\n"
        "- add measures: name = NOT A COMMAND; finish_turn = 4\n"
    )
    assert len(commands) == 1


def test_grounds_attach_to_the_preceding_command():
    commands, _, _ = parse_store_changes(
        "## Store changes\n"
        "- add measures: name = X; finish_turn = 3\n"
        "  - Grounds: the cyber incident in turn 2\n"
    )
    assert commands[0].grounds == "the cyber incident in turn 2"


def test_code_span_wrapper_is_stripped():
    """Models copy the backticks the prompt wrapped the form in."""
    commands, malformed, _ = parse_store_changes(
        "## Store changes\n- ``add measures: name = X; finish_turn = 3``\n"
    )
    assert malformed == []
    assert len(commands) == 1


@pytest.mark.parametrize(
    "line",
    [
        "No other changes.",
        "No further changes",
        "No additional changes.",
        "No more changes.",
        "No changes.",
    ],
)
def test_a_trailing_no_op_line_is_not_a_fault(line: str):
    """Actors write these after their commands, and they are not commands.

    The fault channel only means something while everything in it is a fault:
    a real run flagged `No other changes.` as an unparsed command twice, which
    is exactly the noise that trains a reader to skip the warnings.
    """
    commands, malformed, _ = parse_store_changes(
        f"## Store changes\n- add measures: name = X; size = small; finish_turn = 4\n- {line}\n"
    )
    assert len(commands) == 1
    assert malformed == []


def test_a_no_op_line_does_not_swallow_a_real_command():
    commands, malformed, _ = parse_store_changes(
        "## Store changes\n- No changes to measures except: add measures: name = X; finish_turn = 4\n"
    )
    assert malformed  # not silently discarded


def test_numbered_lists_are_lists_too():
    """Actors write "1. add measures: ..." often enough to matter."""
    for prefix in ("1.", "2)", "10."):
        commands, malformed, _ = parse_store_changes(
            f"## Store changes\n{prefix} add measures: name = X; finish_turn = 3\n"
        )
        assert malformed == []
        assert len(commands) == 1


@pytest.mark.parametrize(
    "line,expected",
    [
        ("delete measures M1", ""),
        ("delete measures M1 because the levy was rejected", "the levy was rejected"),
        ("delete measures M1 — the levy was rejected", "the levy was rejected"),
        ("delete measures M1: the levy was rejected", "the levy was rejected"),
    ],
)
def test_a_delete_may_carry_its_reason_inline(line: str, expected: str):
    """A delete must give grounds, so it is written this way as often as not."""
    commands, malformed, _ = parse_store_changes(f"## Store changes\n- {line}\n")
    assert malformed == []
    assert commands[0].kind == "delete"
    assert commands[0].record_id == "M1"
    assert commands[0].grounds == expected


@pytest.mark.parametrize("value", ["-3", "0"])
def test_a_turn_column_rejects_a_non_turn(store: Store, value: str):
    """Turns are 1-indexed, and a non-positive one satisfies every
    `when_reached` comparison there is."""
    outcome = apply(
        store, 1, f"## Store changes\n- add measures: name = X; finish_turn = {value}\n"
    )[0]
    assert outcome.verdict == "rejected"
    assert "turn number of 1 or more" in outcome.reason


def test_a_stored_value_is_never_executed_as_a_template(store: Store):
    """Values are inserted by Jinja, not re-rendered by it.

    The repository already runs a sandboxed environment because of a real
    template-injection issue, and rendering the rules against the store adds a
    path from actor-written text into a template context. It is a value path,
    and this pins it as one.
    """
    from jinja2.sandbox import SandboxedEnvironment

    apply(
        store,
        1,
        "## Store changes\n- add measures: name = {{ 7*7 }}; size = small; finish_turn = 4\n",
    )
    env = SandboxedEnvironment()
    rules = env.from_string("{{ store.rows('measures') }}").render(store=StoreView(store, "eu"))
    prompt = env.from_string("{{ metric_rules }}").render(metric_rules=rules)
    assert "{{ 7*7 }}" in prompt
    assert "49" not in prompt


def test_unparsable_line_is_recorded_rather_than_dropped():
    commands, malformed, _ = parse_store_changes(
        "## Store changes\n"
        "- add measures: name = X; finish_turn = 3\n"
        "- we will also do something vague\n"
    )
    assert len(commands) == 1
    assert malformed == ["we will also do something vague"]


def test_semicolons_separate_but_commas_do_not():
    """A measure name contains commas far more often than semicolons."""
    commands, _, _ = parse_store_changes(
        "## Store changes\n"
        "- add measures: name = Compute, chips, and energy package; finish_turn = 5\n"
    )
    assert commands[0].assignments["name"] == "Compute, chips, and energy package"


# ---------------------------------------------------------------------------
# Derivation and the read surface
# ---------------------------------------------------------------------------


def test_derived_map(store: Store):
    add_two(store)
    view = StoreView(store, "eu")
    assert view.sum("measures", "cost_per_turn") == 5


def test_derived_status_follows_the_turn(store: Store):
    add_two(store)
    view = StoreView(store, "eu")

    store.current_turn = 2
    assert view.sum("measures", "cost_per_turn", status="running") == 5
    # M2 finishes on turn 3: at turn 3 it is finished and stops costing.
    store.current_turn = 3
    assert view.sum("measures", "cost_per_turn", status="running") == 3
    assert view.count("measures", status="finished") == 1


def test_aggregates(store: Store):
    add_two(store)
    view = StoreView(store, "eu")
    assert view.count("measures") == 2
    assert view.min("measures", "cost_per_turn") == 2
    assert view.max("measures", "cost_per_turn") == 3
    assert view.mean("measures", "cost_per_turn") == 2.5


def test_empty_aggregates_do_not_invent_a_number(store: Store):
    """An empty mean is undefined; rendering 0 would look authoritative."""
    view = StoreView(store, "eu")
    assert view.sum("measures", "cost_per_turn") == 0
    assert view.count("measures") == 0
    assert view.mean("measures", "cost_per_turn") == "(none)"
    assert view.min("measures", "cost_per_turn") == "(none)"
    assert view.rows("measures") == "(none)"


def test_rows_render_every_column_including_derived(store: Store):
    add_two(store)
    store.current_turn = 1
    rows = StoreView(store, "eu").rows("measures")
    assert "M1" in rows and "InvestAI Gigafactories" in rows
    assert "cost_per_turn" in rows and "status" in rows
    assert rows.count("\n") == 3  # header, rule, two records


def test_query_surface_stays_closed(store: Store):
    view = StoreView(store, "eu")
    with pytest.raises(StoreSchemaError):
        view.sum("measures", "cost_per_turn", size="large", status="running")
    with pytest.raises(StoreSchemaError):
        view.sum("measures", "nope")
    with pytest.raises(StoreSchemaError):
        view.sum("nope", "cost_per_turn")


def test_views_are_scoped_per_actor(store: Store):
    add_two(store)
    # A later turn, because a turn is one transaction: re-entering turn 1 would
    # restore the pre-turn snapshot and discard what the first actor wrote.
    apply(store, 2, "## Store changes\n- add measures: name = Z; size = large; finish_turn = 6\n",
          actor="other")
    assert StoreView(store, "eu").count("measures") == 2
    assert StoreView(store, "other").count("measures") == 1
    assert StoreView(store).count("measures") == 3


def test_an_actor_cannot_address_another_actors_record(store: Store):
    add_two(store)
    store.begin_turn(2)
    commands, _, _ = parse_store_changes("## Store changes\n- delete measures M1\n")
    assert store.apply(commands[0], "other", 2).verdict == "rejected"
    assert len(store.live_records("measures")) == 2


# ---------------------------------------------------------------------------
# Atomicity under the referee loop
# ---------------------------------------------------------------------------


def test_rerunning_a_turn_replaces_rather_than_appends(store: Store):
    """`constitutional_enforcement.max_attempts` permits a turn to run again."""
    add_two(store)
    text = "## Store changes\n- add measures: name = Third; size = small; finish_turn = 9\n"
    apply(store, 2, text)
    assert len(store.live_records("measures")) == 3
    apply(store, 2, text)
    assert len(store.live_records("measures")) == 3


def test_a_partial_re_emission_does_not_leave_half_of_each_attempt(store: Store):
    add_two(store)
    apply(
        store,
        2,
        "## Store changes\n"
        "- add measures: name = A; size = small; finish_turn = 9\n"
        "- add measures: name = B; size = small; finish_turn = 9\n",
    )
    assert len(store.live_records("measures")) == 4
    apply(store, 2, "## Store changes\n- add measures: name = A; size = small; finish_turn = 9\n")
    names = {r.fields["name"] for r in store.live_records("measures")}
    assert "B" not in names
    assert len(store.live_records("measures")) == 3


# ---------------------------------------------------------------------------
# Schema strictness
# ---------------------------------------------------------------------------


def test_no_store_block_is_no_store():
    assert not parse_store_schema(None)
    assert not parse_store_schema({})


@pytest.mark.parametrize(
    "bad",
    [
        {"measures": {"scope": "actor", "colums": {}}},
        {"measures": {"scope": "world", "columns": {"id": {"owner": "system"}}}},
        {"measures": {"columns": {"id": {"owner": "system"}, "n": {"owner": "nobody"}}}},
        {"measures": {"columns": {"id": {"owner": "system"}, "n": {"owner": "actor", "type": "date"}}}},
        {"measures": {"columns": {"id": {"owner": "system"}, "e": {"owner": "actor", "type": "enum"}}}},
        {"measures": {"columns": {"n": {"owner": "actor"}}}},
        {"measures": {"columns": {"id": {"owner": "system"}}}},
        {"Measures": {"columns": {"id": {"owner": "system"}, "n": {"owner": "actor"}}}},
    ],
)
def test_malformed_schema_is_rejected_at_load(bad):
    with pytest.raises(StoreSchemaError):
        parse_store_schema(bad)


def test_derivation_is_one_step_deep():
    with pytest.raises(StoreSchemaError) as err:
        parse_store_schema(
            {
                "m": {
                    "columns": {
                        "id": {"owner": "system"},
                        "size": {"owner": "actor", "type": "enum", "values": ["a"]},
                        "one": {"owner": "derived", "from": "size", "map": {"a": 1}},
                        "two": {"owner": "derived", "from": "one", "map": {"1": 2}},
                    }
                }
            }
        )
    assert "itself derived" in str(err.value)


def test_a_map_must_cover_every_enum_value():
    with pytest.raises(StoreSchemaError) as err:
        parse_store_schema(
            {
                "m": {
                    "columns": {
                        "id": {"owner": "system"},
                        "size": {"owner": "actor", "type": "enum", "values": ["large", "small"]},
                        "cost": {"owner": "derived", "from": "size", "map": {"large": 3}},
                    }
                }
            }
        )
    assert "small" in str(err.value)


def test_table_prefixes_are_unique():
    schema = parse_store_schema(
        {
            "measures": {"columns": {"id": {"owner": "system"}, "n": {"owner": "actor"}}},
            "mandates": {"columns": {"id": {"owner": "system"}, "n": {"owner": "actor"}}},
        }
    )
    prefixes = {t.id_prefix for t in schema.tables.values()}
    assert len(prefixes) == 2


# ---------------------------------------------------------------------------
# Template references
# ---------------------------------------------------------------------------


def test_valid_reference_passes():
    schema = parse_store_schema(SCHEMA)
    errors, _ = check_store_references(
        schema,
        "Rows:\n{{ store.rows('measures') }}\n"
        "Charge {{ store.sum('measures', 'cost_per_turn', status='running') }}.",
        "metric-rules.md",
    )
    assert errors == []


@pytest.mark.parametrize(
    "text",
    [
        "{{ store.sum('measures', 'costs') }}",
        "{{ store.sum('meausres', 'cost_per_turn') }}",
        "{{ store.median('measures', 'cost_per_turn') }}",
        "{{ store.sum('measures', 'cost_per_turn', nope='x') }}",
        "{{ store.sum('measures') }}",
    ],
)
def test_broken_reference_is_an_error(text: str):
    """An undefined Jinja variable renders as empty text and zeroes the term."""
    errors, _ = check_store_references(parse_store_schema(SCHEMA), text, "metric-rules.md")
    assert errors


def test_reference_without_a_declared_store_is_an_error():
    errors, _ = check_store_references(
        parse_store_schema(None), "{{ store.sum('measures', 'x') }}", "metric-rules.md"
    )
    assert errors


def test_total_without_rows_warns():
    _errors, warnings = check_store_references(
        parse_store_schema(SCHEMA),
        "Charge {{ store.sum('measures', 'cost_per_turn') }}.",
        "metric-rules.md",
    )
    assert len(warnings) == 1
    assert "itemised rows" in warnings[0]


def test_actor_scoped_call_is_found():
    references = find_store_references("{{ store.actor('eu').sum('measures', 'cost_per_turn') }}")
    assert len(references) == 1
    assert references[0].table == "measures"
    assert references[0].column == "cost_per_turn"


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def test_round_trip_through_json(store: Store):
    add_two(store)
    apply(store, 2, "## Store changes\n- delete measures M2\n")
    store.current_turn = 2

    restored = Store(parse_store_schema(SCHEMA))
    restored.restore(json.loads(json.dumps(store.to_dict())))
    restored.current_turn = 2

    assert [r.id for r in restored.live_records("measures")] == ["M1"]
    assert restored.counters == store.counters
    assert StoreView(restored, "eu").rows("measures") == StoreView(store, "eu").rows("measures")


def test_artifact_shows_records_and_the_changelog(store: Store):
    outcomes = apply(
        store,
        1,
        "## Store changes\n"
        "- add measures: name = X; size = small; finish_turn = 4\n"
        "  - Grounds: because\n"
        "- update measures M9: finish_turn = 5\n",
    )
    text = render_store_file(store, "eu", "European Union", 1, outcomes, [], True)
    assert "# Store: European Union (turn 1)" in text
    assert "## measures" in text
    assert "**applied** `M1`" in text
    assert "Grounds: because" in text
    assert "**rejected**" in text


def test_artifact_names_a_missing_section_as_a_fault(store: Store):
    text = render_store_file(store, "eu", "European Union", 4, [], [], False)
    assert "No `## Store changes` section" in text
    assert "is a fault" in text


def test_self_test_passes():
    """The `--self-test` the design asks for from the first commit."""
    assert self_test() == 0
