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


def block(*entries: dict) -> str:
    """One ``## Store changes`` section carrying a JSON write block."""
    return "## Store changes\n\n" + jsonblock(*entries)


def jsonblock(*entries: dict) -> str:
    """Just the fenced JSON write block, for sections built by hand."""
    return "```json\n" + json.dumps({"store": list(entries)}) + "\n```\n"


def add_entry(table: str = "measures", grounds: str = "", **fields) -> dict:
    entry: dict = {"op": "add", "table": table, "fields": dict(fields)}
    if grounds:
        entry["grounds"] = grounds
    return entry


def update_entry(record_id: str, table: str = "measures", **fields) -> dict:
    return {"op": "update", "table": table, "id": record_id, "fields": dict(fields)}


def delete_entry(record_id: str, table: str = "measures", grounds: str = "") -> dict:
    return {"op": "delete", "table": table, "id": record_id, "grounds": grounds}


def add_two(store: Store) -> None:
    apply(
        store,
        1,
        block(
            add_entry(
                name="InvestAI Gigafactories", category=4, size="large", finish_turn=7
            ),
            add_entry(
                name="Incident Response Corps", category=6, size="small", finish_turn=3
            ),
        ),
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
    apply(store, 2, block(update_entry("M1", finish_turn=8)))
    live = {r.id for r in store.live_records("measures")}
    assert live == {"M1", "M2"}


def test_deletes_name_one_record_each(store: Store):
    """JSON carries one id per entry, so the old two-id delete has no syntax.

    Under the markdown grammar "delete measures M7, M8" deleted M7 and kept
    M8 silently -- the second id absorbed into the reason clause, this
    module's own failure mode reintroduced in its own parser. One entry names
    one record now, and that class of bug has nowhere to live.
    """
    add_two(store)
    outcomes = apply(store, 2, block(delete_entry("M1"), delete_entry("M2")))
    assert [o.verdict for o in outcomes] == ["applied", "applied"]
    assert store.live_records("measures") == []


def test_a_delete_carries_its_grounds(store: Store):
    add_two(store)
    outcomes = apply(
        store, 2, block(delete_entry("M1", grounds="both stalled"), delete_entry("M2", grounds="both stalled"))
    )
    assert [o.record_id for o in outcomes] == ["M1", "M2"]
    assert all(o.grounds == "both stalled" for o in outcomes)


def test_a_duplicate_name_is_noted_and_not_refused(store: Store):
    """Names are not keys, so this is auditing, not gatekeeping.

    A verification run carried the same initiative twice for two turns at full
    cost, because the actor believed its first attempt had not gone through.
    Rejecting would be wrong -- a scenario may legitimately want two measures
    of similar name -- but a reader should see it.
    """
    apply(store, 1, block(add_entry(name="Twice", size="small", finish_turn=9)))
    outcome = apply(
        store, 2, block(add_entry(name="twice", size="large", finish_turn=9))
    )[0]
    assert outcome.verdict == "applied"
    assert "duplicates the name of M1" in outcome.note
    assert len(store.live_records("measures")) == 2

    text = render_store_file(store, "eu", "EU", 2, [outcome], [], True)
    assert "Note: duplicates the name of M1" in text


def test_removal_requires_an_explicit_command(store: Store):
    add_two(store)
    outcomes = apply(store, 2, block(delete_entry("M2")))
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


def test_a_system_column_cannot_be_written(store: Store):
    add_two(store)
    outcome = apply(store, 2, block(update_entry("M1", started_turn=5)))[0]
    assert outcome.verdict == "rejected"
    assert store.live_records("measures")[0].fields["started_turn"] == 1


def test_a_derived_column_cannot_be_written(store: Store):
    add_two(store)
    outcome = apply(store, 2, block(update_entry("M1", cost_per_turn=1)))[0]
    assert outcome.verdict == "rejected"
    assert store.value(store.live_records("measures")[0], "cost_per_turn") == 3


def test_an_unwritable_column_costs_the_value_not_the_command(store: Store):
    """The actor copies the columns it is shown, and it is shown all of them.

    An eight-turn verification run lost six measures because each `add`
    carried `cost_per_turn = 3` beside the fields the actor owns -- the right
    value, which the framework computes anyway, rejected along with the whole
    measure. An unknown column stays a rejection, because a typo must never
    become an addition; a known but unwritable one is the actor telling us
    what we already know.
    """
    outcome = apply(
        store,
        1,
        block(
            add_entry(
                name="Kept", size="large", finish_turn=9,
                cost_per_turn=99, started_turn=4,
            )
        ),
    )[0]
    assert outcome.verdict == "applied"
    assert "computed from 'size'" in outcome.note
    assert "stamped by the framework" in outcome.note

    record = store.live_records("measures")[0]
    assert record.fields["name"] == "Kept"
    assert store.value(record, "cost_per_turn") == 3   # not 99
    assert record.fields["started_turn"] == 1          # not 4


def test_an_unknown_column_is_still_a_rejection(store: Store):
    """The two cases are different and must stay different."""
    outcome = apply(
        store, 1,
        block(add_entry(name="X", finish_turn=3, colour="blue")),
    )[0]
    assert outcome.verdict == "rejected"
    assert store.live_records("measures") == []


def test_unknown_column_is_a_rejection_not_an_addition(store: Store):
    outcome = apply(
        store, 1, block(add_entry(name="X", finish_turn=3, colour="blue"))
    )[0]
    assert outcome.verdict == "rejected"
    assert "no column 'colour'" in outcome.reason
    assert store.live_records("measures") == []


def test_required_columns_are_required(store: Store):
    outcome = apply(store, 1, block(add_entry(name="X")))[0]
    assert outcome.verdict == "rejected"
    assert "finish_turn" in outcome.reason


def test_ids_are_assigned_by_python(store: Store):
    add_two(store)
    assert [r.id for r in store.live_records("measures")] == ["M1", "M2"]
    # And an id is never reused after a deletion, so a stale reference in a
    # later turn cannot silently address a different record.
    apply(store, 2, block(delete_entry("M1")))
    apply(store, 3, block(add_entry(name="Y", size="small", finish_turn=9)))
    assert [r.id for r in store.live_records("measures")] == ["M2", "M3"]


def test_the_writer_never_keys_on_names(store: Store):
    """Names are not keys, so a paraphrase cannot address a record at all.

    `check_portfolio_drift.py` needs a stopword list and a fuzzy word matcher because
    the Game Master renames measures between turns ("EU AI Incident Response
    Corps", "European AI Incident Response Corps"). An entry without an id does
    not parse into an update, so no paraphrase can ever reach the wrong record.
    """
    add_two(store)
    commands, malformed, _ = parse_store_changes(
        block({"op": "update", "table": "measures", "fields": {"finish_turn": 9}})
    )
    assert commands == []
    assert len(malformed) == 1
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
    apply(store, 1, block(add_entry(name="X", size=written, finish_turn=4)))
    assert store.live_records("measures")[0].fields["size"] == expected


@pytest.mark.parametrize(
    "written,expected", [("7", 7), ("turn 7", 7), ("**7**", 7), ("Turn 7.", 7)]
)
def test_turn_is_read_out_of_prose(store: Store, written: str, expected: int):
    apply(store, 1, block(add_entry(name="X", finish_turn=written)))
    assert store.live_records("measures")[0].fields["finish_turn"] == expected


def test_unnormalisable_value_is_rejected_loudly(store: Store):
    outcome = apply(
        store, 1, block(add_entry(name="X", size="enormous", finish_turn=4))
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
            + jsonblock(add_entry(name="X", finish_turn=3))
        )
        assert present is True
        assert len(commands) == 1


def test_section_ends_at_the_next_heading_of_the_same_level():
    commands, _, _ = parse_store_changes(
        "## Store changes\n"
        + jsonblock(add_entry(name="X", finish_turn=3))
        + "\n## Priority\n"
        + jsonblock(add_entry(name="NOT AN ENTRY", finish_turn=4))
    )
    assert len(commands) == 1


def test_grounds_ride_inside_the_entry():
    commands, _, _ = parse_store_changes(
        block(add_entry(name="X", finish_turn=3, grounds="the cyber incident in turn 2"))
    )
    assert commands[0].grounds == "the cyber incident in turn 2"


def test_unfenced_json_is_still_read():
    """A bare object is accepted; the fence is a courtesy, not the contract."""
    commands, malformed, _ = parse_store_changes(
        "## Store changes\n" + json.dumps({"store": [add_entry(name="X", finish_turn=3)]}) + "\n"
    )
    assert malformed == []
    assert len(commands) == 1


def test_one_bad_entry_rejects_only_itself(store: Store):
    """Per-entry rejection, not per-block: a turn's good writes survive one typo."""
    outcomes = apply(
        store,
        1,
        block(
            add_entry(name="Good", size="small", finish_turn=4),
            {"op": "add", "table": "measures", "fields": {"name": "Bad"}},
            add_entry(name="Also good", size="small", finish_turn=5),
        ),
    )
    assert [o.verdict for o in outcomes] == ["applied", "rejected", "applied"]
    assert {r.fields["name"] for r in store.live_records("measures")} == {"Good", "Also good"}


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
def test_trailing_prose_after_the_block_is_not_a_fault(line: str):
    """Writers add these after their block, and they are not entries.

    The fault channel only means something while everything in it is a fault:
    a real run once flagged `No other changes.` as an unparsed command twice,
    which is exactly the noise that trains a reader to skip the warnings.
    """
    commands, malformed, _ = parse_store_changes(
        "## Store changes\n"
        + jsonblock(add_entry(name="X", size="small", finish_turn=4))
        + line
        + "\n"
    )
    assert len(commands) == 1
    assert malformed == []


def test_prose_without_a_block_is_malformed_not_silent():
    commands, malformed, present = parse_store_changes(
        "## Store changes\nNo changes to measures except some vague intent.\n"
    )
    assert present is True
    assert commands == []
    assert malformed  # not silently discarded


def test_every_entry_in_one_block_applies():
    commands, malformed, _ = parse_store_changes(
        block(add_entry(name="X", finish_turn=3), add_entry(name="Y", finish_turn=4))
    )
    assert malformed == []
    assert len(commands) == 2


@pytest.mark.parametrize(
    "grounds",
    ["", "the levy was rejected"],
)
def test_a_delete_carries_its_grounds_in_the_entry(grounds: str):
    """A delete must give grounds, so the entry carries them as often as not."""
    commands, malformed, _ = parse_store_changes(
        block(delete_entry("M1", grounds=grounds))
    )
    assert malformed == []
    assert commands[0].kind == "delete"
    assert commands[0].record_id == "M1"
    assert commands[0].grounds == grounds


@pytest.mark.parametrize("value", [-3, 0])
def test_a_turn_column_rejects_a_non_turn(store: Store, value: int):
    """Turns are 1-indexed, and a non-positive one satisfies every
    `when_reached` comparison there is."""
    outcome = apply(store, 1, block(add_entry(name="X", finish_turn=value)))[0]
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
        block(add_entry(name="{{ 7*7 }}", size="small", finish_turn=4)),
    )
    env = SandboxedEnvironment()
    rules = env.from_string("{{ store.rows('measures') }}").render(store=StoreView(store, "eu"))
    prompt = env.from_string("{{ metric_rules }}").render(metric_rules=rules)
    assert "{{ 7*7 }}" in prompt
    assert "49" not in prompt


def test_unparsable_block_is_recorded_rather_than_dropped():
    commands, malformed, _ = parse_store_changes(
        "## Store changes\n```json\n{not json at all\n```\n"
    )
    assert commands == []
    assert len(malformed) == 1


def test_commas_need_no_escaping_in_json_values():
    """A measure name contains commas; JSON strings hold them as-is."""
    commands, _, _ = parse_store_changes(
        block(add_entry(name="Compute, chips, and energy package", finish_turn=5))
    )
    assert commands[0].assignments["name"] == "Compute, chips, and energy package"


# ---------------------------------------------------------------------------
# Ranges: clamp-and-record by default, error on request
# ---------------------------------------------------------------------------


RANGE_SCHEMA = {
    "gauges": {
        "scope": "actor",
        "columns": {
            "id": {"owner": "system", "type": "text"},
            "name": {"owner": "actor", "type": "text", "required": True},
            "level": {"owner": "actor", "type": "integer", "range": [0, 10]},
            "strict": {"owner": "actor", "type": "integer", "range": {"min": 0, "max": 10},
                       "on_out_of_range": "error"},
        },
    }
}


def test_range_clamps_and_records(store: Store):
    """A silent clamp is quiet wrongness; a clamp with a trace is not."""
    schema = parse_store_schema(RANGE_SCHEMA)
    ranged = Store(schema)
    ranged.begin_turn(1)
    commands, malformed, _ = parse_store_changes(
        block({"op": "add", "table": "gauges",
               "fields": {"name": "G", "level": 99, "strict": 3}})
    )
    assert malformed == []
    outcome = ranged.apply(commands[0], "eu", 1)
    assert outcome.verdict == "applied"
    assert ranged.live_records("gauges")[0].fields["level"] == 10
    assert "clamped from 99 to 10" in outcome.note


def test_range_error_rejects(store: Store):
    schema = parse_store_schema(RANGE_SCHEMA)
    ranged = Store(schema)
    ranged.begin_turn(1)
    commands, _, _ = parse_store_changes(
        block({"op": "add", "table": "gauges",
               "fields": {"name": "G", "level": 3, "strict": 11}})
    )
    outcome = ranged.apply(commands[0], "eu", 1)
    assert outcome.verdict == "rejected"
    assert "outside range [0, 10]" in outcome.reason
    assert ranged.live_records("gauges") == []


def test_range_forms_and_misforms():
    good_list = {"g": {"columns": {
        "id": {"owner": "system"}, "n": {"owner": "actor", "type": "integer", "range": [0, 5]}}}}
    good_map = {"g": {"columns": {
        "id": {"owner": "system"}, "n": {"owner": "actor", "type": "number",
                                        "range": {"min": -1, "max": 1}}}}}
    parse_store_schema(good_list)
    parse_store_schema(good_map)
    for bad in (
        {"g": {"columns": {
            "id": {"owner": "system"}, "n": {"owner": "actor", "type": "integer",
                                            "range": [5, 0]}}}},
        {"g": {"columns": {
            "id": {"owner": "system"}, "n": {"owner": "actor", "type": "text", "range": [0, 5]}}}},
        {"g": {"columns": {
            "id": {"owner": "system"}, "n": {"owner": "actor", "type": "integer",
                                            "on_out_of_range": "warn"}}}},
    ):
        with pytest.raises(StoreSchemaError):
            parse_store_schema(bad)


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
    assert str(rows).count("\n") == 3  # header, rule, two records


def test_rows_with_column_selection_renders_narrow_table(store: Store):
    """Column selection fixes the token and attention cost of wide rows."""
    add_two(store)
    store.current_turn = 1
    view = StoreView(store, "eu")
    narrow = str(view.rows("measures", ["id", "name", "cost_per_turn"], status="running"))
    assert "M1" in narrow and "InvestAI Gigafactories" in narrow
    assert "cost_per_turn" in narrow
    assert "targeted_effect" not in narrow and "status" not in narrow
    wide = str(view.rows("measures", status="running"))
    assert "status" in wide


def test_selector_reducers_need_exactly_one_column(store: Store):
    """rows('t', ['a', 'b']).sum has no defensible answer: a validation error."""
    from scenario_lab.store import StoreSchemaError as _SSE

    add_two(store)
    view = StoreView(store, "eu")
    assert view.rows("measures", ["cost_per_turn"]).sum == 5
    assert view.rows("measures", status="running").count == 2
    with pytest.raises(_SSE):
        _ = view.rows("measures", ["cost_per_turn", "category"]).sum
    with pytest.raises(_SSE):
        _ = view.rows("measures").sum
    with pytest.raises(StoreSchemaError):
        _ = view.rows("measures", ["nope"]).sum


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
    apply(store, 2, block(add_entry(name="Z", size="large", finish_turn=6)),
          actor="other")
    assert StoreView(store, "eu").count("measures") == 2
    assert StoreView(store, "other").count("measures") == 1
    assert StoreView(store).count("measures") == 3


def test_an_actor_cannot_address_another_actors_record(store: Store):
    add_two(store)
    store.begin_turn(2)
    commands, _, _ = parse_store_changes(block(delete_entry("M1")))
    assert store.apply(commands[0], "other", 2).verdict == "rejected"
    assert len(store.live_records("measures")) == 2


# ---------------------------------------------------------------------------
# Atomicity under the referee loop
# ---------------------------------------------------------------------------


def test_rerunning_a_turn_replaces_rather_than_appends(store: Store):
    """`constitutional_enforcement.max_attempts` permits a turn to run again."""
    add_two(store)
    text = block(add_entry(name="Third", size="small", finish_turn=9))
    apply(store, 2, text)
    assert len(store.live_records("measures")) == 3
    apply(store, 2, text)
    assert len(store.live_records("measures")) == 3


def test_a_partial_re_emission_does_not_leave_half_of_each_attempt(store: Store):
    add_two(store)
    apply(
        store,
        2,
        block(
            add_entry(name="A", size="small", finish_turn=9),
            add_entry(name="B", size="small", finish_turn=9),
        ),
    )
    assert len(store.live_records("measures")) == 4
    apply(store, 2, block(add_entry(name="A", size="small", finish_turn=9)))
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
        {"measures": {"scope": "orbit", "columns": {"id": {"owner": "system"}}}},
        {"measures": {"scope": "world", "columns": {"id": {"owner": "system"}}}},
        {
            "measures": {
                "scope": "actor",
                "columns": {
                    "id": {"owner": "system"},
                    "n": {"owner": "actor"},
                    "w": {"owner": "world"},
                },
            }
        },
        {
            "measures": {
                "scope": "world",
                "columns": {
                    "id": {"owner": "system"},
                    "w": {"owner": "world"},
                    "n": {"owner": "actor"},
                },
            }
        },
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


WORLD_SCHEMA = {
    "pacts": {
        "scope": "world",
        "columns": {
            "id": {"owner": "system", "type": "text"},
            "name": {"owner": "world", "type": "text", "required": True},
            "seats": {"owner": "world", "type": "integer"},
            "standing": {
                "owner": "derived", "type": "text",
                "from": "seats", "map": {"5": "strong"},
            },
        },
    }
}


def test_world_tables_belong_to_the_run_not_an_actor():
    """A world table is read by every step and written by the Game Master step."""
    schema = parse_store_schema(WORLD_SCHEMA)
    store = Store(schema)
    store.begin_turn(1)
    commands, malformed, present = parse_store_changes(
        block(add_entry("pacts", name="River Pact", seats=5))
    )
    assert present is True and malformed == []
    # An actor's write to a world table is rejected, not half-applied.
    assert store.apply(commands[0], "eu", 1).verdict == "rejected"
    outcome = store.apply(commands[0], "world", 1, writer_kind="world")
    assert outcome.verdict == "applied"
    # ... while the Game Master cannot reach actor tables.
    actor_schema = parse_store_schema(SCHEMA)
    actor_store = Store(actor_schema)
    actor_store.begin_turn(1)
    actor_commands, _, _ = parse_store_changes(
        block(add_entry(name="X", size="small", finish_turn=4))
    )
    assert (
        actor_store.apply(actor_commands[0], "world", 1, writer_kind="world").verdict
        == "rejected"
    )
    # World records read the same whoever asks: no actor filter applies.
    assert len(store.live_records("pacts", "eu")) == 1
    assert len(store.live_records("pacts", "other")) == 1
    assert StoreView(store, "eu").rows("pacts", ["name"]).count == 1


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


def test_new_schema_keys_survive_inheritance_round_trip():
    """Variants inherit the schema through YAML, so every key must round-trip."""
    from scenario_lab.loader import _store_schema_to_yaml

    schema = parse_store_schema(
        {
            "gauges": {
                "scope": "world",
                "reporting_required": True,
                "columns": {
                    "id": {"owner": "system", "type": "text"},
                    "level": {"owner": "world", "type": "integer",
                              "reporting_required": True,
                              "range": {"min": 0, "max": 100},
                              "on_out_of_range": "error"},
                },
            }
        }
    )
    revived = parse_store_schema(_store_schema_to_yaml(schema))
    table = revived.tables["gauges"]
    assert table.scope == "world"
    assert table.reporting_required is True
    column = table.columns["level"]
    assert column.reporting_required is True
    assert column.range == (0.0, 100.0)
    assert column.on_out_of_range == "error"


# ---------------------------------------------------------------------------
# Adjust: submit the change, not the new value
# ---------------------------------------------------------------------------


SINGLE_GAUGE_SCHEMA = {
    "gauge": {
        "scope": "actor",
        "columns": {
            "id": {"owner": "system", "type": "text"},
            "name": {"owner": "actor", "type": "text", "required": True},
            "level": {"owner": "actor", "type": "integer", "range": [0, 100]},
        },
    }
}


def gauge_store() -> Store:
    store = Store(parse_store_schema(SINGLE_GAUGE_SCHEMA))
    store.begin_turn(1)
    commands, malformed, _ = parse_store_changes(
        block(add_entry("gauge", name="G", level=43))
    )
    assert malformed == []
    assert store.apply(commands[0], "eu", 1).verdict == "applied"
    return store


def test_adjust_moves_the_value_by_the_delta():
    store = gauge_store()
    store.begin_turn(2)
    commands, malformed, _ = parse_store_changes(
        block({"op": "update", "table": "gauge", "id": "G1", "adjust": -9,
               "grounds": "portfolio charge 8, priority 1"})
    )
    assert malformed == []
    outcome = store.apply(commands[0], "eu", 2)
    assert outcome.verdict == "applied"
    assert store.live_records("gauge")[0].fields["level"] == 34
    assert "adjusted 'level' from 43 by -9 to 34" in outcome.note


def test_adjust_records_the_loss_at_the_bound():
    store = gauge_store()
    store.begin_turn(2)
    commands, _, _ = parse_store_changes(
        block({"op": "update", "table": "gauge", "id": "G1", "adjust": -50})
    )
    outcome = store.apply(commands[0], "eu", 2)
    assert outcome.verdict == "applied"
    assert store.live_records("gauge")[0].fields["level"] == 0
    assert "lost at the bound" in outcome.note


def test_adjust_needs_one_numeric_column(store: Store):
    """The measures table has two writer-owned numerics: ambiguous, rejected."""
    add_two(store)
    store.begin_turn(2)
    commands, malformed, _ = parse_store_changes(
        block({"op": "update", "table": "measures", "id": "M1", "adjust": -1})
    )
    assert malformed == []
    outcome = store.apply(commands[0], "eu", 2)
    assert outcome.verdict == "rejected"
    assert "no single numeric column" in outcome.reason


def test_fields_and_adjust_together_are_malformed():
    commands, malformed, _ = parse_store_changes(
        block({"op": "update", "table": "gauge", "id": "G1",
               "fields": {"level": 3}, "adjust": -1})
    )
    assert commands == []
    assert len(malformed) == 1


# ---------------------------------------------------------------------------
# reporting_required: omission is a fault the orchestrator re-asks
# ---------------------------------------------------------------------------


REPORTING_SCHEMA = {
    "gauges": {
        "scope": "actor",
        "columns": {
            "id": {"owner": "system", "type": "text"},
            "name": {"owner": "actor", "type": "text", "required": True},
            "level": {"owner": "actor", "type": "integer", "reporting_required": True},
        },
    }
}


def test_a_reported_turn_has_nothing_missing():
    store = Store(parse_store_schema(REPORTING_SCHEMA))
    store.begin_turn(1)
    commands, _, _ = parse_store_changes(block(add_entry("gauges", name="G", level=1)))
    assert store.apply(commands[0], "eu", 1).verdict == "applied"
    assert store.missing_required_reports("actor", "eu") == []


def test_silence_is_an_omission_when_reporting_is_required():
    store = Store(parse_store_schema(REPORTING_SCHEMA))
    store.begin_turn(1)
    commands, _, _ = parse_store_changes(block(add_entry("gauges", name="G", level=1)))
    assert store.apply(commands[0], "eu", 1).verdict == "applied"
    store.begin_turn(2)
    assert store.missing_required_reports("actor", "eu") == [("gauges", "G1", "level")]
    store.begin_turn(2)
    update, _, _ = parse_store_changes(
        block(update_entry("G1", "gauges", level=2))
    )
    assert store.apply(update[0], "eu", 2).verdict == "applied"
    assert store.missing_required_reports("actor", "eu") == []


def test_default_is_silence_means_persistence(store: Store):
    """Without the flag, an untouched record is persistence, not an omission."""
    add_two(store)
    store.begin_turn(2)
    assert store.missing_required_reports("actor", "eu") == []


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


def test_valid_chained_reference_passes():
    schema = parse_store_schema(SCHEMA)
    errors, warnings = check_store_references(
        schema,
        "Rows:\n{{ store.rows('measures', ['id', 'name', 'cost_per_turn'], status='running') }}\n"
        "Charge {{ store.rows('measures', ['cost_per_turn'], status='running').sum }}.",
        "metric-rules.md",
    )
    assert errors == []
    assert warnings == []


@pytest.mark.parametrize(
    "text",
    [
        "{{ store.sum('measures', 'costs') }}",
        "{{ store.sum('meausres', 'cost_per_turn') }}",
        "{{ store.median('measures', 'cost_per_turn') }}",
        "{{ store.sum('measures', 'cost_per_turn', nope='x') }}",
        "{{ store.sum('measures') }}",
        "{{ store.rows('measures', ['cost_per_turn', 'category']).sum }}",
        "{{ store.rows('measures').sum }}",
        "{{ store.rows('measures', ['nope']).sum }}",
        "{{ store.rows('measures', 'cost_per_turn').sum }}",
        "{{ store.rows('measures', ['cost_per_turn']).median }}",
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
    apply(store, 2, block(delete_entry("M2")))
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
        block(
            add_entry(name="X", size="small", finish_turn=4, grounds="because"),
            update_entry("M9", finish_turn=5),
        ),
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
