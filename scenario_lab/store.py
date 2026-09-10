"""Custody of declared persistent state.

A scenario declares, in ``scenario.yaml``, what its actors must hold across
turns: tables of small records with typed columns. Python owns those records.
An actor never restates them; it emits deltas under one declared header, and
silence means persistence.

This is the third instance of a design the framework has already validated
twice. Goal re-derivation from prose failed, rules evolution with mandatory
re-emission failed, and the actor statement ledger -- carried forward verbatim
by Python -- does not drift. The measure portfolio was the remaining piece of
persistent state the model still had to remember to rewrite, and measurement
put the cost at 4.5% of proposals never arriving and 0.6% of entries vanishing
with no stated cause (``docs/proposals/persistent-state-custody.md``).

Three things are deliberately *not* here:

- **A query language.** Five aggregates, one equality filter, no joins, no
  arithmetic between aggregates. Every extension past that is individually
  reasonable and collectively a language with its own bugs, and a wrong
  aggregate looks exactly as authoritative as a right one.
- **Logic in derivation.** A derived column is a lookup table or a turn
  comparison. When a scenario wants more than that, the thing it wants is
  judgement, and judgement belongs to the LLM.
- **Runtime schema changes.** The actor cannot create a table or a column, and
  an unknown column in a command is a rejection rather than an addition. Every
  mechanism in this repository that grew informally had to be measured and
  clamped later.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

# The column owners. This is the load-bearing part of the schema: it is what
# turns "copied forward unchanged" from an instruction the model obeys by
# remembering into something it cannot express at all. `actor` columns are
# written by actors, `world` columns by the Game Master step; `system` is
# stamped by the framework and `derived` is computed at read time.
OWNERS = ("system", "actor", "world", "derived")

# A table belongs either to one actor's portfolio or to the run itself.
# Actor tables are written under `## Store changes` in actor outputs; world
# tables (alliances, treaty registers, standing conditions) are written by the
# Game Master step, read by every step, and persisted with everything else.
SCOPES = ("actor", "world")

COLUMN_TYPES = ("text", "integer", "number", "turn", "enum")

# What the aggregate surface is allowed to be. Named here so the validator and
# the self-test read from the same list as the renderer.
AGGREGATES = ("sum", "min", "max", "mean", "count", "rows")

NO_CHANGES_MARKERS = ("no changes", "no store changes", "none", "nothing")


class StoreSchemaError(ValueError):
    """A malformed ``store:`` block. Raised at load time, never at run time."""


class StoreCommandError(ValueError):
    """A command that cannot be applied. Recorded as a rejection, not raised."""


# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------


@dataclass
class StoreColumn:
    """One column, and who is allowed to put a value in it."""

    name: str
    owner: str
    type: str = "text"
    required: bool = False
    values: tuple[str, ...] = ()          # enum only
    source: Optional[str] = None          # derived: the column derived from
    mapping: dict[str, Any] = field(default_factory=dict)  # derived: lookup
    when_reached: Optional[str] = None    # derived: value once the turn arrives
    otherwise: Optional[str] = None       # derived: value before then
    reporting_required: bool = False      # the writer reports this every turn
    range: Optional[tuple[float, float]] = None  # numeric columns only
    on_out_of_range: str = "clamp"        # "clamp" (and record) | "error"

    @property
    def is_derived_map(self) -> bool:
        return self.owner == "derived" and bool(self.mapping)

    @property
    def is_derived_turn(self) -> bool:
        return self.owner == "derived" and self.when_reached is not None


@dataclass
class StoreTable:
    """One table of records, and the prefix its record ids carry."""

    name: str
    scope: str                            # "actor" | "world"
    columns: dict[str, StoreColumn]
    id_prefix: str = "R"
    reporting_required: bool = False      # every writer-owned column, every turn

    @property
    def id_column(self) -> str:
        """The system-owned identity column, if the schema declares one."""
        for name, column in self.columns.items():
            if column.owner == "system" and column.type == "text":
                return name
        return "id"

    @property
    def writer_owner(self) -> str:
        """Which column owner the table's writer writes: actors or the world."""
        return "world" if self.scope == "world" else "actor"

    def writable(self) -> list[str]:
        return [n for n, c in self.columns.items() if c.owner == self.writer_owner]


@dataclass
class StoreSchema:
    """Every table a scenario declares."""

    tables: dict[str, StoreTable] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return bool(self.tables)

    def to_dict(self) -> dict:
        """The resolved schema, for the run's ``config.json``.

        A schema change is a physics change, and two batches under different
        schemas are not comparable. Recorded for the same reason
        ``reasoning_effort`` is.
        """
        out: dict[str, Any] = {}
        for name, table in self.tables.items():
            columns: dict[str, Any] = {}
            for col_name, column in table.columns.items():
                entry: dict[str, Any] = {"owner": column.owner, "type": column.type}
                if column.required:
                    entry["required"] = True
                if column.reporting_required:
                    entry["reporting_required"] = True
                if column.range is not None:
                    entry["range"] = [column.range[0], column.range[1]]
                if column.on_out_of_range != "clamp":
                    entry["on_out_of_range"] = column.on_out_of_range
                if column.values:
                    entry["values"] = list(column.values)
                if column.source:
                    entry["from"] = column.source
                if column.mapping:
                    entry["map"] = dict(column.mapping)
                if column.when_reached is not None:
                    entry["when_reached"] = column.when_reached
                    entry["else"] = column.otherwise
                columns[col_name] = entry
            body: dict[str, Any] = {"scope": table.scope, "id_prefix": table.id_prefix,
                                    "columns": columns}
            if table.reporting_required:
                body["reporting_required"] = True
            out[name] = body
        return out


_TABLE_KEYS = {"scope", "columns", "reporting_required"}
_COLUMN_KEYS = {"owner", "type", "required", "reporting_required",
                "range", "on_out_of_range",
                "values", "from", "map", "when_reached", "else"}
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _unique_prefixes(names: list[str]) -> dict[str, str]:
    """Shortest uppercase prefix that tells the tables apart.

    Record ids are copied by a model from a rendered row into a command, so
    they have to be short. They also have to be unambiguous when a scenario
    declares several tables, and lengthening every prefix because two tables
    collide would penalise the common single-table case.
    """
    length = 1
    while length <= 8:
        prefixes = {name: name[:length].upper() for name in names}
        if len(set(prefixes.values())) == len(names):
            return prefixes
        length += 1
    return {name: name.upper() for name in names}


def parse_store_schema(data: object) -> StoreSchema:
    """Parse the ``store:`` block from ``scenario.yaml``.

    Strict on purpose: an unknown key is an error rather than an addition,
    which is the rule the resource-patch loader already enforces. A typo in a
    schema is silent everywhere else -- an undefined column renders as empty
    text and zeroes whatever term referenced it.
    """
    if data is None:
        return StoreSchema()
    if not isinstance(data, dict):
        raise StoreSchemaError("store must be a mapping of table name to table definition")
    if not data:
        # An empty block declares no tables, the same as no block at all. This
        # is also the shape inheritance produces when a base declares no store.
        return StoreSchema()

    names = list(data.keys())
    for name in names:
        if not isinstance(name, str) or not _NAME_RE.match(name):
            raise StoreSchemaError(
                f"store table name '{name}' must be lowercase letters, digits and underscores"
            )
    prefixes = _unique_prefixes(names)

    tables: dict[str, StoreTable] = {}
    for name in names:
        body = data[name]
        if not isinstance(body, dict):
            raise StoreSchemaError(f"store table '{name}' must be a mapping")
        unknown = set(body) - _TABLE_KEYS
        if unknown:
            raise StoreSchemaError(
                f"store table '{name}' has unknown key(s): {', '.join(sorted(unknown))}"
            )

        scope = body.get("scope", "actor")
        if scope not in SCOPES:
            raise StoreSchemaError(
                f"store table '{name}': scope must be one of {', '.join(SCOPES)}, "
                f"got '{scope}'"
            )

        raw_columns = body.get("columns")
        if not isinstance(raw_columns, dict) or not raw_columns:
            raise StoreSchemaError(f"store table '{name}' must declare columns")

        table_reporting = body.get("reporting_required", False)
        if not isinstance(table_reporting, bool):
            raise StoreSchemaError(
                f"store table '{name}': 'reporting_required' must be true or false"
            )

        columns: dict[str, StoreColumn] = {}
        for col_name, spec in raw_columns.items():
            columns[col_name] = _parse_column(name, col_name, spec)

        _check_derivations(name, columns)
        if not any(c.owner == "system" and c.type == "text" for c in columns.values()):
            raise StoreSchemaError(
                f"store table '{name}' must declare a system-owned text column for the record id "
                "(the writer addresses records by id, never by name)"
            )
        writer = "world" if scope == "world" else "actor"
        if not any(c.owner == writer for c in columns.values()):
            raise StoreSchemaError(
                f"store table '{name}' has no {writer}-owned column, so nothing could ever be written to it"
            )
        if scope == "actor" and any(c.owner == "world" for c in columns.values()):
            raise StoreSchemaError(
                f"store table '{name}' is actor-scoped but declares a world-owned column: "
                "actors cannot write it and the Game Master cannot reach this table"
            )
        if scope == "world" and any(c.owner == "actor" for c in columns.values()):
            raise StoreSchemaError(
                f"store table '{name}' is world-scoped but declares an actor-owned column: "
                "the Game Master cannot write it and no actor can reach this table"
            )

        tables[name] = StoreTable(
            name=name, scope=scope, columns=columns, id_prefix=prefixes[name],
            reporting_required=table_reporting,
        )

    return StoreSchema(tables=tables)


def _parse_column(table: str, name: object, spec: object) -> StoreColumn:
    where = f"store table '{table}', column '{name}'"
    if not isinstance(name, str) or not _NAME_RE.match(name):
        raise StoreSchemaError(f"{where}: name must be lowercase letters, digits and underscores")
    if not isinstance(spec, dict):
        raise StoreSchemaError(f"{where}: must be a mapping")
    unknown = set(spec) - _COLUMN_KEYS
    if unknown:
        raise StoreSchemaError(f"{where}: unknown key(s): {', '.join(sorted(unknown))}")

    owner = spec.get("owner")
    if owner not in OWNERS:
        raise StoreSchemaError(f"{where}: owner must be one of {', '.join(OWNERS)}")

    col_type = spec.get("type", "text")
    if col_type not in COLUMN_TYPES:
        raise StoreSchemaError(f"{where}: type must be one of {', '.join(COLUMN_TYPES)}")

    values: tuple[str, ...] = ()
    if col_type == "enum":
        raw_values = spec.get("values")
        if not isinstance(raw_values, list) or not raw_values:
            raise StoreSchemaError(f"{where}: an enum column must declare a non-empty values list")
        values = tuple(str(v) for v in raw_values)

    column = StoreColumn(
        name=name,
        owner=owner,
        type=col_type,
        required=bool(spec.get("required", False)),
        values=values,
    )

    if owner == "derived":
        column.source = spec.get("from")
        if not isinstance(column.source, str):
            raise StoreSchemaError(f"{where}: a derived column must name the column it derives from")
        has_map = "map" in spec
        has_turn = "when_reached" in spec
        if has_map == has_turn:
            raise StoreSchemaError(
                f"{where}: a derived column takes exactly one of 'map' (a lookup) "
                "or 'when_reached' (a turn comparison)"
            )
        if has_map:
            mapping = spec["map"]
            if not isinstance(mapping, dict) or not mapping:
                raise StoreSchemaError(f"{where}: 'map' must be a non-empty mapping")
            column.mapping = {str(k): v for k, v in mapping.items()}
        else:
            column.when_reached = str(spec["when_reached"])
            if "else" not in spec:
                raise StoreSchemaError(f"{where}: 'when_reached' requires a matching 'else'")
            column.otherwise = str(spec["else"])
    else:
        for key in ("from", "map", "when_reached", "else"):
            if key in spec:
                raise StoreSchemaError(f"{where}: '{key}' is only meaningful on a derived column")
        if column.required and owner not in ("actor", "world"):
            raise StoreSchemaError(f"{where}: only an actor-owned or world-owned column can be required")
        if "reporting_required" in spec:
            if not isinstance(spec["reporting_required"], bool):
                raise StoreSchemaError(f"{where}: 'reporting_required' must be true or false")
            if spec["reporting_required"] and owner not in ("actor", "world"):
                raise StoreSchemaError(
                    f"{where}: only a writer-owned column reports every turn"
                )
            column.reporting_required = spec["reporting_required"]
        if "range" in spec or "on_out_of_range" in spec:
            if col_type not in ("integer", "number", "turn"):
                raise StoreSchemaError(
                    f"{where}: 'range' is only meaningful on a numeric column"
                )
            if "range" in spec:
                column.range = _parse_range(where, spec["range"])
            policy = spec.get("on_out_of_range", "clamp")
            if policy not in ("clamp", "error"):
                raise StoreSchemaError(
                    f"{where}: 'on_out_of_range' must be clamp or error, got {policy!r}"
                )
            column.on_out_of_range = policy

    return column


def _parse_range(where: str, raw: object) -> tuple[float, float]:
    """``range: [0, 100]`` or ``range: {min: 0, max: 100}`` to a bound pair."""
    low: object = None
    high: object = None
    if isinstance(raw, list) and len(raw) == 2:
        low, high = raw
    elif isinstance(raw, dict) and set(raw) <= {"min", "max"} and "min" in raw and "max" in raw:
        low, high = raw["min"], raw["max"]
    else:
        raise StoreSchemaError(
            f"{where}: 'range' must be [min, max] or {{min: _, max: _}}, got {raw!r}"
        )
    if isinstance(low, bool) or not isinstance(low, (int, float)):
        raise StoreSchemaError(f"{where}: range minimum must be a number, got {low!r}")
    if isinstance(high, bool) or not isinstance(high, (int, float)):
        raise StoreSchemaError(f"{where}: range maximum must be a number, got {high!r}")
    if low > high:
        raise StoreSchemaError(
            f"{where}: range minimum {low} is above maximum {high}"
        )
    return (float(low), float(high))


def _check_derivations(table: str, columns: dict[str, StoreColumn]) -> None:
    for name, column in columns.items():
        if column.owner != "derived":
            continue
        where = f"store table '{table}', column '{name}'"
        source = columns.get(column.source)
        if source is None:
            raise StoreSchemaError(f"{where}: derives from unknown column '{column.source}'")
        if source.owner == "derived":
            raise StoreSchemaError(
                f"{where}: derives from '{column.source}', which is itself derived. "
                "Derivation is one step deep, so that a value is always traceable to a stored one."
            )
        if column.is_derived_turn and source.type != "turn":
            raise StoreSchemaError(
                f"{where}: 'when_reached' compares against a turn, but '{column.source}' "
                f"is type {source.type}"
            )
        if column.is_derived_map and source.type == "enum":
            missing = [v for v in source.values if v not in column.mapping]
            if missing:
                raise StoreSchemaError(
                    f"{where}: 'map' has no entry for {', '.join(missing)} "
                    f"(every value of '{column.source}' must map to something)"
                )


# --------------------------------------------------------------------------
# Values
# --------------------------------------------------------------------------

_DECORATION_RE = re.compile(r"^[\s`*_\"']+|[\s`*_\"'.,;]+$")
_TURN_RE = re.compile(r"(?:turn\s*)?(-?\d+)", re.IGNORECASE)


def normalize_value(column: StoreColumn, raw: object) -> Any:
    """Forgiving on write, strict in store.

    Models write ``Large``, `` `large` `` and ``**large**`` for the same thing,
    and ``finishes on turn 7`` for the number 7. Normalising here is the same
    move ``structured_outputs`` makes when it folds YAML booleans to canonical
    strings at load time. What will not normalise is rejected loudly rather
    than stored as something else.
    """
    text = _DECORATION_RE.sub("", str(raw).strip())
    if not text:
        raise StoreCommandError(f"column '{column.name}' was given an empty value")

    if column.type == "text":
        return text

    if column.type == "enum":
        for value in column.values:
            if value.lower() == text.lower():
                return value
        raise StoreCommandError(
            f"column '{column.name}' must be one of {', '.join(column.values)}, got '{text}'"
        )

    if column.type in ("integer", "turn"):
        match = _TURN_RE.search(text)
        if not match:
            raise StoreCommandError(f"column '{column.name}' must be a whole number, got '{text}'")
        value = int(match.group(1))
        if column.type == "turn" and value < 1:
            # Turns are 1-indexed. A non-positive one is not a turn, and it
            # would quietly satisfy every `when_reached` comparison there is.
            raise StoreCommandError(
                f"column '{column.name}' must be a turn number of 1 or more, got {value}"
            )
        return value

    if column.type == "number":
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if not match:
            raise StoreCommandError(f"column '{column.name}' must be a number, got '{text}'")
        return float(match.group(0))

    raise StoreCommandError(f"column '{column.name}' has unsupported type {column.type}")


def _enforce_range(column: StoreColumn, value: float) -> tuple[float, Optional[str]]:
    """Apply a column's ``range`` to a normalised value.

    The default policy clamps *and records*: a silent clamp is the quiet
    wrongness this project usually refuses, but a clamp that leaves a trace in
    the turn's changelog is not. ``on_out_of_range: error`` rejects instead,
    for columns where an out-of-bounds write means the writer is broken rather
    than approximate.
    """
    assert column.range is not None
    low, high = column.range
    if low <= value <= high:
        return value, None
    if column.on_out_of_range == "error":
        raise StoreCommandError(
            f"column '{column.name}' value {value:g} is outside range [{low:g}, {high:g}]"
        )
    clamped = min(high, max(low, value))
    return clamped, (
        f"'{column.name}' clamped from {value:g} to {clamped:g} (range [{low:g}, {high:g}])"
    )


# --------------------------------------------------------------------------
# Records and the live store
# --------------------------------------------------------------------------


@dataclass
class StoreRecord:
    """One row. ``fields`` holds only stored values; derived ones are computed."""

    id: str
    table: str
    actor_id: str
    fields: dict[str, Any] = field(default_factory=dict)
    added_turn: int = 0
    removed_turn: Optional[int] = None

    @property
    def live(self) -> bool:
        return self.removed_turn is None


@dataclass
class StoreOutcome:
    """What happened to one command, for the changelog."""

    command: str
    verdict: str          # "applied" | "rejected"
    reason: str = ""
    record_id: str = ""
    grounds: str = ""
    note: str = ""        # applied, but worth a reader's attention


class Store:
    """The live records, and the only thing allowed to change them."""

    def __init__(self, schema: StoreSchema):
        self.schema = schema
        self.records: list[StoreRecord] = []
        self.counters: dict[str, int] = {name: 0 for name in schema.tables}
        self.current_turn: int = 0
        self._snapshots: dict[int, str] = {}
        # What the last applied command asked for and did not get, so the
        # outcome can carry it into the changelog.
        self._ignored: list[str] = []
        # Which (table, record id) reported which columns this turn. Reset by
        # begin_turn; both writers in the turn accumulate into it, which is
        # what reporting_required reads to find omissions.
        self._reported: dict[tuple[str, str], set[str]] = {}

    # -- state -----------------------------------------------------------

    def live_records(self, table: str, actor_id: Optional[str] = None) -> list[StoreRecord]:
        # A world table belongs to the run, not to an actor: every step reads
        # the same records, so the actor filter does not apply to it.
        schema_table = self.schema.tables.get(table)
        world = schema_table is not None and schema_table.scope == "world"
        return [
            r for r in self.records
            if r.table == table and r.live and (world or actor_id is None or r.actor_id == actor_id)
        ]

    def find(self, table: str, record_id: str, actor_id: Optional[str] = None) -> Optional[StoreRecord]:
        wanted = record_id.strip().upper()
        for record in self.live_records(table, actor_id):
            if record.id.upper() == wanted:
                return record
        return None

    def value(self, record: StoreRecord, column_name: str) -> Any:
        """The value of one column, computing it when the column is derived."""
        table = self.schema.tables[record.table]
        column = table.columns.get(column_name)
        if column is None:
            return None
        if column.owner != "derived":
            if column_name == table.id_column:
                return record.id
            return record.fields.get(column_name)

        source_value = self.value(record, column.source)
        if source_value is None:
            return None
        if column.is_derived_map:
            return column.mapping.get(str(source_value))
        if isinstance(source_value, int) and self.current_turn >= source_value:
            return column.when_reached
        return column.otherwise

    # -- mutation --------------------------------------------------------

    def _next_id(self, table_name: str) -> str:
        table = self.schema.tables[table_name]
        self.counters[table_name] = self.counters.get(table_name, 0) + 1
        return f"{table.id_prefix}{self.counters[table_name]}"

    def begin_turn(self, turn: int) -> None:
        """Make this turn's application replace, never append.

        ``constitutional_enforcement.max_attempts`` means a turn can be run
        more than once. Commands applied twice would double a portfolio;
        commands applied from a partial re-emission would leave one that is
        half of attempt 2 and half of attempt 3. Restoring the pre-turn
        snapshot before applying makes the declared section the complete
        declaration for the turn, whichever attempt produced it.
        """
        if turn in self._snapshots:
            self.restore(json.loads(self._snapshots[turn]))
        else:
            self._snapshots[turn] = json.dumps(self.to_dict())
        self.current_turn = turn
        self._reported = {}

    def apply(
        self, command: "StoreCommand", actor_id: str, turn: int,
        writer_kind: str = "actor",
    ) -> StoreOutcome:
        """Apply one parsed write, enforcing which scope the writer may touch.

        Actor outputs write actor-scoped tables; the Game Master step writes
        world-scoped ones. A command crossing that boundary is rejected rather
        than half-wired: a scenario must never depend on a table nothing writes
        to, nor let an actor rewrite standing conditions of the world.
        """
        table = self.schema.tables.get(command.table)
        if table is None:
            known = ", ".join(sorted(self.schema.tables)) or "(none)"
            return StoreOutcome(
                command.raw, "rejected",
                f"unknown table '{command.table}' (this scenario declares: {known})",
                grounds=command.grounds,
            )
        if writer_kind == "world" and table.scope != "world":
            return StoreOutcome(
                command.raw, "rejected",
                f"table '{command.table}' is actor-scoped and cannot be written "
                "by the Game Master",
                grounds=command.grounds,
            )
        if writer_kind != "world" and table.scope == "world":
            return StoreOutcome(
                command.raw, "rejected",
                f"table '{command.table}' is world-scoped: only the Game Master "
                "step writes to it",
                grounds=command.grounds,
            )

        self._ignored: list[str] = []
        try:
            if command.kind == "add":
                record = self._apply_add(table, command, actor_id, turn, writer_kind)
            elif command.kind == "update":
                record = self._apply_update(table, command, actor_id, writer_kind)
            elif command.kind == "delete":
                record = self._apply_delete(table, command, actor_id, turn)
            else:
                raise StoreCommandError(f"unknown command '{command.kind}'")
        except StoreCommandError as err:
            return StoreOutcome(command.raw, "rejected", str(err), grounds=command.grounds)

        notes = list(self._ignored)
        duplicate = self._note_for(table, command, record, actor_id)
        if duplicate:
            notes.append(duplicate)
        return StoreOutcome(
            command.raw, "applied", record_id=record.id, grounds=command.grounds,
            note="; ".join(notes),
        )

    def _note_for(
        self, table: StoreTable, command: "StoreCommand", record: StoreRecord, actor_id: str
    ) -> str:
        """Anything applied that a reader should still look at.

        Currently one thing: an `add` whose name already belongs to a live
        record. Names are not keys and never become keys -- a scenario may
        legitimately want two measures of similar name -- so this is recorded
        and not rejected, in the same spirit as the fuzzy matcher that audits
        history rather than running the system. A run once carried the same
        initiative twice for two turns, at full cost, because the actor
        believed its first attempt had not gone through.
        """
        if command.kind != "add":
            return ""
        name = str(record.fields.get("name", "")).strip().lower()
        if not name:
            return ""
        twins = [
            other.id for other in self.live_records(table.name, actor_id)
            if other.id != record.id
            and str(other.fields.get("name", "")).strip().lower() == name
        ]
        if not twins:
            return ""
        return (
            f"duplicates the name of {', '.join(twins)}, which is still live. "
            "Both remain live."
        )

    def _validate_assignments(
        self, table: StoreTable, command: "StoreCommand", writer_kind: str = "actor"
    ) -> tuple[dict[str, Any], list[str]]:
        """The values to store, and what was ignored getting there.

        An *unknown* column is a rejection: a typo must never silently become
        an addition, which is the rule the patch loader already enforces.

        A *known but unwritable* one is not the same thing, and treating it as
        one was expensive. The writer sees the rendered rows -- it has to, the
        rows are the portfolio -- and it copies the columns it sees, so it
        writes `cost_per_turn = 3` beside the fields it owns. The value is
        right, the framework computes it anyway, and rejecting the command
        threw away the whole measure over it: six measures lost in one
        eight-turn run. The assignment is dropped and noted instead. Nothing
        the writer sends can reach a system or derived column either way,
        which is the guarantee that matters.
        """
        allowed = table.writer_owner
        values: dict[str, Any] = {}
        ignored: list[str] = []
        for name, raw in command.assignments.items():
            column = table.columns.get(name)
            if column is None:
                known = ", ".join(table.writable())
                raise StoreCommandError(
                    f"'{table.name}' has no column '{name}' (you may set: {known})"
                )
            if column.owner == "system":
                ignored.append(f"'{name}' is stamped by the framework")
                continue
            if column.owner == "derived":
                ignored.append(f"'{name}' is computed from '{column.source}'")
                continue
            if column.owner != allowed:
                ignored.append(f"'{name}' is not yours to write")
                continue
            normalised = normalize_value(column, raw)
            if column.range is not None:
                normalised, clamp_note = _enforce_range(column, float(normalised))
                if column.type in ("integer", "turn") and float(normalised).is_integer():
                    normalised = int(normalised)
                if clamp_note is not None:
                    ignored.append(clamp_note)
            values[name] = normalised
        return values, ignored

    def _adjustment_target(self, table: StoreTable) -> StoreColumn:
        """The one numeric column an ``adjust`` entry may move.

        ``adjust`` submits the change rather than the new value, so it is only
        meaningful where exactly one writer-owned numeric column exists -- the
        metrics table's value column, for example. Anything else is ambiguous,
        and an ambiguous adjustment is a rejection rather than a guess.
        """
        candidates = [
            c for c in table.columns.values()
            if c.owner == table.writer_owner and c.type in ("integer", "number", "turn")
        ]
        if len(candidates) != 1:
            raise StoreCommandError(
                f"'{table.name}' has no single numeric column to adjust "
                "(an 'adjust' entry needs exactly one)"
            )
        return candidates[0]

    def _apply_adjustment(
        self, table: StoreTable, record: StoreRecord, delta: float
    ) -> tuple[str, Any]:
        """Move the adjustment target by ``delta``. Returns (column, result).

        The artifact records prior value, adjustment, and result: a wrong delta
        compounds forever where a wrong absolute value self-corrects next turn,
        and the legible trail is the only defence. Clamping interacts -- an
        adjustment that runs past a bound loses the overshoot, and the loss is
        recorded rather than absorbed.
        """
        column = self._adjustment_target(table)
        prior = record.fields.get(column.name)
        if not isinstance(prior, (int, float)) or isinstance(prior, bool):
            raise StoreCommandError(
                f"record '{record.id}' has no prior '{column.name}' value to adjust"
            )
        result: Any = float(prior) + delta
        trail = f"adjusted '{column.name}' from {prior} by {delta:g} to {result:g}"
        if column.range is not None:
            result, clamp_note = _enforce_range(column, result)
            if clamp_note is not None:
                lost = (float(prior) + delta) - result
                trail += f" (clamped: {lost:g} lost at the bound)"
        if column.type in ("integer", "turn") and isinstance(result, float) and result.is_integer():
            result = int(result)
        record.fields[column.name] = result
        self._reported.setdefault((table.name, record.id), set()).add(column.name)
        return column.name, trail

    def _apply_add(
        self, table: StoreTable, command: "StoreCommand", actor_id: str, turn: int,
        writer_kind: str = "actor",
    ) -> StoreRecord:
        values, ignored = self._validate_assignments(table, command, writer_kind)
        self._ignored = ignored
        missing = [
            name for name, column in table.columns.items()
            if column.owner == table.writer_owner and column.required and name not in values
        ]
        if missing:
            raise StoreCommandError(f"missing required column(s): {', '.join(missing)}")

        record = StoreRecord(
            id=self._next_id(table.name),
            table=table.name,
            actor_id=actor_id,
            fields=values,
            added_turn=turn,
        )
        # System-owned turn columns are stamped, never written. This is the
        # whole point of declaring provenance: `started_turn` cannot be
        # rewritten later because there is no command that reaches it.
        for name, column in table.columns.items():
            if column.owner == "system" and column.type == "turn":
                record.fields[name] = turn
        self.records.append(record)
        self._reported[(table.name, record.id)] = set(values)
        return record

    def _apply_update(
        self, table: StoreTable, command: "StoreCommand", actor_id: str,
        writer_kind: str = "actor",
    ) -> StoreRecord:
        record = self.find(table.name, command.record_id, actor_id)
        if record is None:
            raise StoreCommandError(f"no live record '{command.record_id}' in '{table.name}'")
        values, ignored = self._validate_assignments(table, command, writer_kind)
        self._ignored = ignored
        if command.adjust is not None:
            if values:
                raise StoreCommandError(
                    "an update carries 'fields' or 'adjust', not both"
                )
            _, trail = self._apply_adjustment(table, record, command.adjust)
            self._ignored.append(trail)
            return record
        if not values:
            raise StoreCommandError(
                "an update must set at least one column you own"
                + (f" ({'; '.join(ignored)})" if ignored else "")
            )
        record.fields.update(values)
        self._reported.setdefault((table.name, record.id), set()).update(values)
        return record

    def _apply_delete(
        self, table: StoreTable, command: "StoreCommand", actor_id: str, turn: int
    ) -> StoreRecord:
        record = self.find(table.name, command.record_id, actor_id)
        if record is None:
            raise StoreCommandError(f"no live record '{command.record_id}' in '{table.name}'")
        record.removed_turn = turn
        return record

    # -- required reports --------------------------------------------------

    def required_columns(self, table: StoreTable) -> list[str]:
        """Writer-owned columns the writer must report every turn.

        A table-level ``reporting_required: true`` covers every writer-owned
        column; otherwise only columns flagged individually. Default off:
        omitted means unchanged, which is the silence-means-persistence rule
        the whole store rests on.
        """
        return [
            name for name, column in table.columns.items()
            if column.owner == table.writer_owner
            and (column.reporting_required or table.reporting_required)
        ]

    def missing_required_reports(
        self, writer_kind: str = "actor", actor_id: Optional[str] = None
    ) -> list[tuple[str, str, str]]:
        """Live (table, record id, column) triples the turn did not report.

        Read after a writer's entries applied, before the turn moves on. An
        omission here is a fault -- the counterpart of the absent-section
        check -- and the orchestrator re-asks once rather than only warning,
        in the pattern of the metrics repair.
        """
        missing: list[tuple[str, str, str]] = []
        for table_name, table in self.schema.tables.items():
            if writer_kind == "world" and table.scope != "world":
                continue
            if writer_kind != "world" and table.scope == "world":
                continue
            required = self.required_columns(table)
            if not required:
                continue
            for record in self.live_records(table_name, actor_id):
                reported = self._reported.get((table_name, record.id), set())
                for column in required:
                    if column not in reported:
                        missing.append((table_name, record.id, column))
        return missing

    # -- persistence -----------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the whole store.

        ``fields`` holds stored values only and is what ``restore`` reads back;
        derived values are recomputed from it, never trusted from the file.
        ``derived`` is written alongside it anyway, stamped at the turn the
        file was written, so that anything reading a turn's artifact -- the
        dashboard, the tree extractor, a person -- sees what the prompts saw
        that turn without having to know the scenario's derivation rules.
        """
        return {
            "turn": self.current_turn,
            "counters": dict(self.counters),
            "records": [
                {
                    "id": r.id,
                    "table": r.table,
                    "actor": r.actor_id,
                    "fields": dict(r.fields),
                    "derived": {
                        name: self.value(r, name)
                        for name, column in self.schema.tables[r.table].columns.items()
                        if column.owner == "derived"
                    },
                    "added_turn": r.added_turn,
                    "removed_turn": r.removed_turn,
                }
                for r in self.records
            ],
        }

    def restore(self, data: dict) -> None:
        self.records = []
        self.counters = {name: 0 for name in self.schema.tables}
        for name, value in (data.get("counters") or {}).items():
            if name in self.counters and isinstance(value, int):
                self.counters[name] = value
        for entry in data.get("records") or []:
            if entry.get("table") not in self.schema.tables:
                continue
            self.records.append(
                StoreRecord(
                    id=str(entry.get("id")),
                    table=entry["table"],
                    actor_id=str(entry.get("actor", "")),
                    fields=dict(entry.get("fields") or {}),
                    added_turn=int(entry.get("added_turn") or 0),
                    removed_turn=entry.get("removed_turn"),
                )
            )


# --------------------------------------------------------------------------
# Commands (one JSON block per writing step)
# --------------------------------------------------------------------------


@dataclass
class StoreCommand:
    """One parsed write."""

    kind: str                              # "add" | "update" | "delete"
    table: str
    record_id: str = ""
    assignments: dict[str, Any] = field(default_factory=dict)
    grounds: str = ""
    raw: str = ""
    adjust: Optional[float] = None         # update only: submit the change


# Matched leniently for the same reason the statement section is: a writer gets
# a heading level wrong often enough that strictness costs more than it buys,
# and a discarded section is indistinguishable from a writer that changed
# nothing.
_SECTION_RE = re.compile(
    r"^[ \t]{0,3}(?P<hashes>#{1,6})[ \t]+Store changes\b[^\n]*$",
    re.IGNORECASE | re.MULTILINE,
)

# Fenced blocks carrying the write form, e.g.
# ```json
# {"store": [{"op": "add", "table": "measures", "fields": {...}}]}
# ```
_FENCED_BLOCK_RE = re.compile(
    r"```(?:json)?[ \t]*\n(?P<body>.*?)\n```", re.IGNORECASE | re.DOTALL
)


def _next_section_re(level: int) -> re.Pattern[str]:
    return re.compile(rf"^[ \t]{{0,3}}#{{1,{level}}}[ \t]+", re.MULTILINE)


def _entry_to_command(entry: object, index: int) -> StoreCommand:
    """One ``{"store": [...]}`` array element to a command.

    Shape problems raise ``StoreCommandError`` with the entry's position, and
    the caller records them per entry: one malformed entry rejects that entry,
    never the turn's other writes.
    """
    where = f"entry {index}"
    if not isinstance(entry, dict):
        raise StoreCommandError(f"{where} must be an object, got {entry!r}"[:160])
    op = str(entry.get("op", "")).strip().lower()
    if op not in ("add", "update", "delete"):
        raise StoreCommandError(
            f"{where}: 'op' must be one of add, update, delete, got {entry.get('op')!r}"[:160]
        )
    table = str(entry.get("table", "")).strip().lower()
    if not table:
        raise StoreCommandError(f"{where}: a '{op}' needs a table name")
    grounds = entry.get("grounds", "")
    grounds = str(grounds).strip() if grounds is not None else ""

    raw = json.dumps(entry, ensure_ascii=False)[:400]

    if op == "delete":
        record_id = str(entry.get("id", "")).strip().upper()
        if not record_id:
            raise StoreCommandError(f"{where}: a 'delete' needs an 'id'")
        return StoreCommand(kind=op, table=table, record_id=record_id, grounds=grounds, raw=raw)

    fields = entry.get("fields", {})
    if fields is None:
        fields = {}
    if not isinstance(fields, dict):
        raise StoreCommandError(f"{where}: 'fields' must be an object")
    adjust_raw = entry.get("adjust")
    if adjust_raw is not None and fields:
        raise StoreCommandError(
            f"{where}: give 'fields' or 'adjust', not both -- "
            "set the value, or submit the change"
        )
    adjust: Optional[float] = None
    if adjust_raw is not None:
        if isinstance(adjust_raw, bool):
            raise StoreCommandError(f"{where}: 'adjust' must be a number")
        if isinstance(adjust_raw, (int, float)):
            adjust = float(adjust_raw)
        elif isinstance(adjust_raw, str):
            try:
                adjust = float(adjust_raw.strip().lstrip("+"))
            except ValueError:
                raise StoreCommandError(
                    f"{where}: 'adjust' must be a number, got {adjust_raw!r}"[:160]
                ) from None
        else:
            raise StoreCommandError(f"{where}: 'adjust' must be a number")
    assignments: dict[str, Any] = {}
    for name, value in fields.items():
        clean = str(name).strip().strip("`*_\"' ").lower()
        if clean:
            assignments[clean] = value
    if op == "add":
        if adjust is not None:
            raise StoreCommandError(f"{where}: an 'add' sets 'fields', not 'adjust'")
        return StoreCommand(kind=op, table=table, assignments=assignments, grounds=grounds, raw=raw)
    record_id = str(entry.get("id", "")).strip().upper()
    if not record_id:
        raise StoreCommandError(f"{where}: an 'update' needs an 'id'")
    return StoreCommand(
        kind=op, table=table, record_id=record_id,
        assignments=assignments, adjust=adjust, grounds=grounds, raw=raw,
    )


def _commands_from_candidates(
    candidates: list[str],
) -> tuple[list[StoreCommand], list[str]]:
    """Parse candidate JSON documents into commands and per-entry rejections."""
    commands: list[StoreCommand] = []
    malformed: list[str] = []
    for candidate in candidates:
        try:
            document = json.loads(candidate)
        except json.JSONDecodeError as err:
            malformed.append(f"unparseable JSON block: {err}"[:200])
            continue
        if isinstance(document, dict) and isinstance(document.get("store"), list):
            entries = document["store"]
        elif isinstance(document, list):
            entries = document
        else:
            malformed.append(
                'expected {"store": [...]} — the block parsed but holds no store array'[:200]
            )
            continue
        for index, entry in enumerate(entries):
            try:
                commands.append(_entry_to_command(entry, index))
            except StoreCommandError as err:
                malformed.append(str(err))
    return commands, malformed


def parse_store_changes(output: str) -> tuple[list[StoreCommand], list[str], bool]:
    """Extract JSON write commands from a step's response.

    Returns ``(commands, malformed_entries, section_present)``.

    ``section_present`` is reported rather than inferred because its absence is
    the failure this whole mechanism exists to make visible. A missing section
    is detectable; a missing inline command never was, and that is the larger
    half of the measured defect. Per-entry rejection survives the format
    change: one malformed entry rejects that entry while the rest apply.
    """
    match = _SECTION_RE.search(output)
    if not match:
        return [], [], False

    body = output[match.end():]
    next_section = _next_section_re(len(match.group("hashes"))).search(body)
    if next_section:
        body = body[: next_section.start()]

    if body.strip().lower().rstrip(".") in NO_CHANGES_MARKERS:
        return [], [], True

    candidates = [m.group("body") for m in _FENCED_BLOCK_RE.finditer(body)]
    if not candidates and body.strip():
        candidates = [body.strip()]

    commands, malformed = _commands_from_candidates(candidates)
    if not candidates:
        return [], [], True
    if not commands and not malformed:
        # An explicit empty array: {"store": []}. Nothing to do, and the
        # section was present, so this is a declaration of no change.
        return [], [], True
    return commands, malformed, True


# --------------------------------------------------------------------------
# The read surface
# --------------------------------------------------------------------------


# Aliased because the view's own methods are named after them, and reading
# ``_builtin_sum`` at the call site is clearer than relying on the reader to
# remember that a class attribute does not shadow a global.
_builtin_sum = sum
_builtin_min = min
_builtin_max = max


class StoreSelection:
    """One selector: ``store.rows(table, [columns], **where)`` plus reducers.

    A bare selector renders the markdown table (``str(selection)``); a reduced
    one yields a number (``selection.sum`` and friends). Writing the same
    selector twice -- once bare and once reduced -- is how "render the itemised
    rows beside any total" is expressed.

    Reducers are properties (not methods) so they resolve under the Jinja
    sandbox without a call: ``{{ store.rows('measures', ['cost_per_turn'],
    status='running').sum }}``. Underscored helpers stay out of reach by the
    same rule that keeps ``StoreView._store`` out.
    """

    def __init__(
        self,
        store: Store,
        table: str,
        columns: Optional[list[str]],
        where: dict[str, Any],
        actor_id: Optional[str] = None,
    ):
        self._store = store
        self._table = table
        # None means every column, in schema order. A list means exactly those,
        # in the given order.
        self._columns = list(columns) if columns is not None else None
        self._where = dict(where)
        self._actor_id = actor_id

    @property
    def _view(self) -> "StoreView":
        return StoreView(self._store, self._actor_id)

    def _select(self) -> list[StoreRecord]:
        view = self._view
        records = view._select(self._table, self._where)
        if self._columns is not None:
            schema_table = self._store.schema.tables.get(self._table)
            if schema_table is not None:
                for name in self._columns:
                    if name not in schema_table.columns:
                        raise StoreSchemaError(
                            f"store table '{self._table}' has no column '{name}'"
                        )
        return records

    def _numbers(self) -> list[float]:
        if self._columns is None or len(self._columns) != 1:
            selected = (
                "none" if not self._columns else ", ".join(self._columns)
            )
            raise StoreSchemaError(
                f"rows('{self._table}', [{selected}]) has no single column to reduce: "
                "a reducer needs exactly one selected column, e.g. "
                f"rows('{self._table}', ['cost_per_turn']).sum"
            )
        column = self._columns[0]
        return self._view._numbers(self._table, column, self._where)

    @staticmethod
    def _tidy(value: float) -> Any:
        return int(value) if float(value).is_integer() else round(value, 3)

    @property
    def count(self) -> int:
        return len(self._select())

    @property
    def sum(self) -> Any:
        return self._tidy(_builtin_sum(self._numbers()))

    @property
    def min(self) -> Any:
        values = self._numbers()
        return self._tidy(_builtin_min(values)) if values else "(none)"

    @property
    def max(self) -> Any:
        values = self._numbers()
        return self._tidy(_builtin_max(values)) if values else "(none)"

    @property
    def mean(self) -> Any:
        values = self._numbers()
        # An empty mean is undefined, and rendering it as 0 would put an
        # authoritative-looking number where there is no answer. These values
        # are read as prose by a model, never consumed by Python arithmetic,
        # so a visible marker is the honest rendering.
        return self._tidy(_builtin_sum(values) / len(values)) if values else "(none)"

    def __str__(self) -> str:
        records = self._select()
        schema_table = self._store.schema.tables[self._table]
        columns = list(schema_table.columns) if self._columns is None else list(self._columns)
        multi_actor = len({r.actor_id for r in self._store.live_records(self._table)}) > 1
        header = (["actor"] if multi_actor else []) + columns

        if not records:
            return "(none)"

        lines = ["| " + " | ".join(header) + " |",
                 "|" + "|".join("---" for _ in header) + "|"]
        for record in records:
            cells = [record.actor_id] if multi_actor else []
            for name in columns:
                value = self._store.value(record, name)
                cells.append("" if value is None else str(value).replace("|", "\\|"))
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return str(self)

    def __format__(self, spec: str) -> str:
        return format(str(self), spec)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return str(self) == other
        if isinstance(other, StoreSelection):
            return str(self) == str(other)
        return NotImplemented

    def __contains__(self, item: object) -> bool:
        return str(item) in str(self)


class StoreView:
    """What ``{{ store.… }}`` can do inside a template.

    The read surface is one selector plus reducers: ``store.rows(table,
    [columns], **filter)`` renders the markdown table, and ``.count`` /
    ``.sum`` / ``.min`` / ``.max`` / ``.mean`` on it yield numbers. Closed and
    small by design: one equality filter, no joins, no arithmetic between
    aggregates. A rule that needs more than this is asking for judgement, and
    judgement is the LLM's job.
    """

    def __init__(self, store: Store, actor_id: Optional[str] = None):
        self._store = store
        self._actor_id = actor_id

    def actor(self, actor_id: str) -> "StoreView":
        return StoreView(self._store, actor_id)

    # -- internals (underscored, so the Jinja sandbox keeps them out of reach)

    def _select(self, table: str, where: dict[str, Any]) -> list[StoreRecord]:
        schema_table = self._store.schema.tables.get(table)
        if schema_table is None:
            known = ", ".join(sorted(self._store.schema.tables)) or "(none)"
            raise StoreSchemaError(f"unknown store table '{table}' (declared: {known})")
        if len(where) > 1:
            raise StoreSchemaError(
                f"store queries take at most one filter, got {len(where)}: "
                f"{', '.join(sorted(where))}"
            )
        for name in where:
            if name not in schema_table.columns:
                raise StoreSchemaError(f"store table '{table}' has no column '{name}'")

        records = self._store.live_records(table, self._actor_id)
        for name, wanted in where.items():
            records = [
                r for r in records
                if str(self._store.value(r, name)).lower() == str(wanted).lower()
            ]
        return records

    def _numbers(self, table: str, column: str, where: dict[str, Any]) -> list[float]:
        schema_table = self._store.schema.tables.get(table)
        if schema_table is not None and column not in schema_table.columns:
            raise StoreSchemaError(f"store table '{table}' has no column '{column}'")
        values: list[float] = []
        for record in self._select(table, where):
            value = self._store.value(record, column)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                values.append(float(value))
        return values

    @staticmethod
    def _tidy(value: float) -> Any:
        return int(value) if float(value).is_integer() else round(value, 3)

    # -- aggregates (legacy thin wrappers; prefer rows(...).<reducer>) ------

    def sum(self, table: str, column: str, **where: Any) -> Any:
        return self.rows(table, [column], **where).sum

    def count(self, table: str, **where: Any) -> int:
        return self.rows(table, **where).count

    def min(self, table: str, column: str, **where: Any) -> Any:
        return self.rows(table, [column], **where).min

    def max(self, table: str, column: str, **where: Any) -> Any:
        return self.rows(table, [column], **where).max

    def mean(self, table: str, column: str, **where: Any) -> Any:
        return self.rows(table, [column], **where).mean

    def rows(
        self, table: str, columns: Optional[list[str] | tuple[str, ...]] = None, **where: Any
    ) -> StoreSelection:
        """The itemised rows, as a markdown table -- and the reducers on it.

        ``design-notes.md`` records that the portfolio charge binds *because*
        "the total cannot be known without summing it". Handing over a
        pre-computed total on its own risks the Game Master ceasing to attend
        to the portfolio at all, and the narrative drifting free of the store
        rather than the reverse. Every total is meant to be rendered beside
        these rows, and the validator warns when one is not.

        ``columns`` narrows the rendered table: ``rows('measures',
        ['id', 'name', 'cost_per_turn'], status='running')`` renders three
        columns instead of ten. A reducer needs exactly one selected column --
        ``rows('measures', ['cost_per_turn'], status='running').sum`` -- except
        ``count``, which counts rows whatever is selected.
        """
        if columns is not None and not isinstance(columns, (list, tuple)):
            raise StoreSchemaError(
                f"rows('{table}') takes a list of columns, got {columns!r}"
            )
        return StoreSelection(self._store, table, columns, where, self._actor_id)


# --------------------------------------------------------------------------
# Artifacts
# --------------------------------------------------------------------------


def render_store_file(
    store: Store,
    actor_id: str,
    actor_name: str,
    turn: int,
    outcomes: list[StoreOutcome],
    malformed: list[str],
    section_present: bool,
) -> str:
    """The per-turn artifact, written every turn whether anything changed or not.

    Same contract as the statements artifact: a diff between consecutive turns
    is empty unless a command was actually applied, so drift is visible in the
    artifacts rather than hidden in narrative.
    """
    view = StoreView(store, actor_id)
    lines = [f"# Store: {actor_name} (turn {turn})", ""]

    for table_name in store.schema.tables:
        lines += [f"## {table_name}", "", str(view.rows(table_name)), ""]

    lines += ["## Changes this turn", ""]
    if not section_present:
        lines.append(
            "**No `## Store changes` section in the actor's response.** Nothing was "
            "applied this turn. An absent section is a fault, not a declaration of "
            "no change: the actor is required to write `No changes.` when it has none."
        )
        lines.append("")
    if not outcomes and not malformed:
        if section_present:
            lines.append("No changes.")
    for outcome in outcomes:
        head = f"- **{outcome.verdict}**"
        if outcome.record_id:
            head += f" `{outcome.record_id}`"
        head += f" — {outcome.command}"
        lines.append(head)
        if outcome.grounds:
            lines.append(f"  - Grounds: {outcome.grounds}")
        if outcome.note:
            lines.append(f"  - Note: {outcome.note}")
        if outcome.reason:
            lines.append(f"  - Reason: {outcome.reason}")
    for line in malformed:
        lines.append(f"- **unparsed** — {line}")
        lines.append("  - Reason: not a recognised store entry (see the `{\"store\": [...]}` write form)")

    return "\n".join(lines) + "\n"


def world_tables(schema: StoreSchema) -> list[str]:
    """Names of the run-owned tables, in declaration order."""
    return [name for name, table in schema.tables.items() if table.scope == "world"]


def render_world_store_file(
    store: Store,
    turn: int,
    outcomes: list[StoreOutcome],
    malformed: list[str],
    section_present: bool,
) -> str:
    """The per-turn artifact for run-owned tables, written by the Game Master step.

    Same contract as the actor file: a diff between consecutive turns is empty
    unless a world entry was actually applied. An absent block is a fault, not
    a declaration of no change -- the step is required to write
    ``{"store": []}`` when it changes nothing.
    """
    view = StoreView(store)
    lines = [f"# World store (turn {turn})", ""]
    names = world_tables(store.schema)

    for table_name in names:
        lines += [f"## {table_name}", "", str(view.rows(table_name)), ""]

    lines += ["## Changes this turn", ""]
    if not section_present:
        lines.append(
            "**No `## Store changes` section in the Game Master response.** Nothing was "
            "applied this turn. An absent section is a fault, not a declaration of "
            "no change: the step is required to write `{\"store\": []}` when it has none."
        )
        lines.append("")
    if not outcomes and not malformed:
        if section_present:
            lines.append("No changes.")
    for outcome in outcomes:
        head = f"- **{outcome.verdict}**"
        if outcome.record_id:
            head += f" `{outcome.record_id}`"
        head += f" — {outcome.command}"
        lines.append(head)
        if outcome.grounds:
            lines.append(f"  - Grounds: {outcome.grounds}")
        if outcome.note:
            lines.append(f"  - Note: {outcome.note}")
        if outcome.reason:
            lines.append(f"  - Reason: {outcome.reason}")
    for line in malformed:
        lines.append(f"- **unparsed** — {line}")
        lines.append("  - Reason: not a recognised store entry (see the `{\"store\": [...]}` write form)")

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Template references
# --------------------------------------------------------------------------

_CALL_RE = re.compile(
    r"\bstore(?:\.actor\(\s*['\"][^'\"]*['\"]\s*\))?"
    r"\.(?P<method>[a-z_]+)\(\s*(?P<args>[^)]*)\)",
    re.IGNORECASE,
)
# The chained read surface: store.rows('t', ['c'], f='v').sum and friends. The
# trailing reducer is part of the match so a bare rows() and a reduced one are
# told apart at validation time.
_ROWS_CHAIN_RE = re.compile(
    r"\bstore(?:\.actor\(\s*['\"][^'\"]*['\"]\s*\))?"
    r"\.rows\(\s*(?P<args>[^)]*)\)\s*(?:\.\s*(?P<reducer>[a-z_]+))?",
    re.IGNORECASE,
)
_STRING_ARG_RE = re.compile(r"['\"]([^'\"]*)['\"]")
_KWARG_RE = re.compile(r"([a-z_][a-z0-9_]*)\s*=")
_LIST_RE = re.compile(r"\[([^\]]*)\]")


@dataclass
class StoreReference:
    """One ``store.…`` call found in a template, for validation."""

    method: str
    table: Optional[str]
    column: Optional[str]
    kwargs: tuple[str, ...]
    raw: str
    # The chained read surface carries its column selection separately: None
    # means "every column" (bare ``rows('t')`` or ``rows('t').count``), a tuple
    # means exactly those. ``chained`` tells a rows() call apart from the
    # legacy ``store.sum('t', 'c')`` form, which keeps ``column`` instead.
    columns: Optional[tuple[str, ...]] = None
    chained: bool = False


def _parse_rows_args(args: str) -> tuple[Optional[str], Optional[tuple[str, ...]], bool]:
    """Split a rows() argument list into table, column selection, bare-column flag.

    Returns ``(table, columns, has_bare_column)`` where ``columns`` is None for
    "every column" and a tuple otherwise. ``has_bare_column`` is true when the
    call passes a second positional quoted string instead of a list -- e.g.
    ``rows('measures', 'cost_per_turn')`` -- which the runtime rejects (it
    takes a list) and the validator reports as such.
    """
    list_match = _LIST_RE.search(args)
    columns: Optional[tuple[str, ...]] = None
    rest = args
    if list_match:
        columns = tuple(_STRING_ARG_RE.findall(list_match.group(1)))
        rest = args[: list_match.start()] + args[list_match.end():]
    # Positional parts are the comma-separated pieces without an '='; keyword
    # parts carry the single equality filter. A quoted filter value such as
    # status='running' must not read as a column selection.
    positionals: list[str] = []
    for part in rest.split(","):
        if "=" in part:
            continue
        part = part.strip()
        if part:
            positionals.append(part)
    strings = _STRING_ARG_RE.findall(" ".join(positionals))
    table = strings[0] if strings else None
    has_bare_column = list_match is None and len(strings) > 1
    if has_bare_column:
        columns = tuple(strings[1:])
    if list_match and columns is not None and len(positionals) > 1:
        # A list selection plus an extra bare positional string: keep both so
        # the validator can report the stray one rather than dropping it.
        extra = [s for s in strings[1:] if s not in columns]
        if extra:
            columns = tuple([*columns, *extra])
            has_bare_column = True
    return table, columns, has_bare_column


def find_store_references(text: str) -> list[StoreReference]:
    """Every ``store.…`` call in a template.

    An undefined Jinja variable renders as empty text, so a mistyped column
    silently zeroes an arithmetic term and the rule stops applying with
    nothing recording it. The cautionary case is `openweight_frontier_release`,
    where the correct instruction was written, reviewed, and never sent to
    anything. These references are checked against the schema at validation
    time for exactly that reason.
    """
    references: list[StoreReference] = []
    chained_spans: list[tuple[int, int]] = []
    for match in _ROWS_CHAIN_RE.finditer(text):
        args = match.group("args")
        reducer = (match.group("reducer") or "rows").lower()
        table, columns, _bare = _parse_rows_args(args)
        column: Optional[str] = None
        if reducer != "rows" and reducer != "count" and columns is not None and len(columns) == 1:
            column = columns[0]
        references.append(
            StoreReference(
                method=reducer,
                table=table,
                column=column,
                kwargs=tuple(_KWARG_RE.findall(args)),
                raw=match.group(0),
                columns=tuple(columns) if columns is not None else None,
                chained=True,
            )
        )
        chained_spans.append((match.start(), match.end()))
    for match in _CALL_RE.finditer(text):
        # Rows calls are owned by the chained pass above; matching them again
        # here would double-count every selector.
        if any(start <= match.start() < end for start, end in chained_spans):
            continue
        args = match.group("args")
        strings = _STRING_ARG_RE.findall(args)
        method = match.group("method").lower()
        if method == "rows":
            # A rows() the chained regex missed (unusual spacing); parse it
            # the same way rather than dropping it.
            table, columns, _bare = _parse_rows_args(args)
            references.append(
                StoreReference(
                    method="rows",
                    table=table,
                    column=None,
                    kwargs=tuple(_KWARG_RE.findall(args)),
                    raw=match.group(0),
                    columns=tuple(columns) if columns is not None else None,
                    chained=True,
                )
            )
            continue
        table = strings[0] if strings else None
        column = strings[1] if len(strings) > 1 else None
        if method == "count":
            column = None
        references.append(
            StoreReference(
                method=method,
                table=table,
                column=column,
                kwargs=tuple(_KWARG_RE.findall(args)),
                raw=match.group(0),
            )
        )
    return references


def check_store_references(schema: StoreSchema, text: str, where: str) -> tuple[list[str], list[str]]:
    """Validate a template's ``store.…`` calls against the schema."""
    errors: list[str] = []
    warnings: list[str] = []
    references = find_store_references(text)
    if not references:
        return errors, warnings

    if not schema:
        errors.append(f"{where}: uses store.…, but this scenario declares no `store:` block")
        return errors, warnings

    aggregated: set[str] = set()
    itemised: set[str] = set()

    for ref in references:
        if ref.method not in AGGREGATES:
            errors.append(
                f"{where}: `{ref.raw}` — unknown store operation '{ref.method}' "
                f"(available: {', '.join(AGGREGATES)})"
            )
            continue
        if ref.table is None:
            errors.append(f"{where}: `{ref.raw}` — the table must be a quoted name")
            continue
        table = schema.tables.get(ref.table)
        if table is None:
            errors.append(
                f"{where}: `{ref.raw}` — unknown table '{ref.table}' "
                f"(declared: {', '.join(sorted(schema.tables))})"
            )
            continue
        if ref.method == "rows":
            itemised.add(ref.table)
            if ref.chained and ref.columns is not None:
                _table, _cols, bare = _parse_rows_args(
                    _ROWS_CHAIN_RE.search(ref.raw).group("args")
                    if _ROWS_CHAIN_RE.search(ref.raw)
                    else ""
                )
                if bare:
                    errors.append(
                        f"{where}: `{ref.raw}` — pass columns as a list, e.g. "
                        f"rows('{ref.table}', ['id', 'name'])"
                    )
                for name in ref.columns:
                    if name not in table.columns:
                        errors.append(
                            f"{where}: `{ref.raw}` — table '{ref.table}' has no column '{name}' "
                            f"(declared: {', '.join(table.columns)})"
                        )
        else:
            aggregated.add(ref.table)
            if ref.chained:
                _table, _cols, bare = _parse_rows_args(
                    _ROWS_CHAIN_RE.search(ref.raw).group("args")
                    if _ROWS_CHAIN_RE.search(ref.raw)
                    else ""
                )
                if bare:
                    errors.append(
                        f"{where}: `{ref.raw}` — pass columns as a list, e.g. "
                        f"rows('{ref.table}', ['cost_per_turn']).{ref.method}"
                    )
                    continue
                if ref.method == "count":
                    for name in ref.columns or ():
                        if name not in table.columns:
                            errors.append(
                                f"{where}: `{ref.raw}` — table '{ref.table}' has no column '{name}' "
                                f"(declared: {', '.join(table.columns)})"
                            )
                else:
                    selected = list(ref.columns or ())
                    if len(selected) != 1:
                        shown = ", ".join(selected) if selected else "none"
                        errors.append(
                            f"{where}: `{ref.raw}` — {ref.method} needs exactly one "
                            f"selected column, got [{shown}]: "
                            f"rows('{ref.table}', ['<column>']).{ref.method}"
                        )
                    elif selected[0] not in table.columns:
                        errors.append(
                            f"{where}: `{ref.raw}` — table '{ref.table}' has no column '{selected[0]}' "
                            f"(declared: {', '.join(table.columns)})"
                        )
            else:
                if ref.method not in ("count", "rows"):
                    if ref.column is None:
                        errors.append(f"{where}: `{ref.raw}` — {ref.method} needs a quoted column name")
                    elif ref.column not in table.columns:
                        errors.append(
                            f"{where}: `{ref.raw}` — table '{ref.table}' has no column '{ref.column}' "
                            f"(declared: {', '.join(table.columns)})"
                        )
        for name in ref.kwargs:
            if name not in table.columns:
                errors.append(
                    f"{where}: `{ref.raw}` — filter on unknown column '{name}' "
                    f"in table '{ref.table}'"
                )
        if len(ref.kwargs) > 1:
            errors.append(
                f"{where}: `{ref.raw}` — a store query takes at most one filter, got {len(ref.kwargs)}"
            )

    for table_name in sorted(aggregated - itemised):
        warnings.append(
            f"{where}: aggregates over '{table_name}' without rendering "
            f"store.rows('{table_name}') anywhere. A total the Game Master cannot "
            "check against the rows is a number it stops attending to; render the "
            "itemised rows beside it."
        )

    return errors, warnings


# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------

_SELF_TEST_SCHEMA = {
    "measures": {
        "scope": "actor",
        "columns": {
            "id": {"owner": "system", "type": "text"},
            "name": {"owner": "actor", "type": "text", "required": True},
            "size": {"owner": "actor", "type": "enum", "values": ["large", "small"]},
            "started_turn": {"owner": "system", "type": "turn"},
            "finish_turn": {"owner": "actor", "type": "turn", "required": True},
            "cost_per_turn": {
                "owner": "derived", "type": "integer",
                "from": "size", "map": {"large": 3, "small": 2},
            },
            "status": {
                "owner": "derived", "type": "text",
                "from": "finish_turn", "when_reached": "finished", "else": "running",
            },
        },
    }
}


def self_test() -> int:
    """Check the store against its own contract. Returns a process exit code."""
    failures: list[str] = []

    def check(label: str, got: Any, want: Any) -> None:
        if got != want:
            failures.append(f"{label}: expected {want!r}, got {got!r}")

    schema = parse_store_schema(_SELF_TEST_SCHEMA)
    store = Store(schema)

    # A well-formed turn.
    store.begin_turn(1)
    commands, malformed, present = parse_store_changes(
        "## Store changes\n\n```json\n"
        + json.dumps({"store": [
            {"op": "add", "table": "measures",
             "fields": {"name": "InvestAI Gigafactories", "size": "**Large**",
                        "finish_turn": "turn 7"},
             "grounds": "inherited programme"},
            {"op": "add", "table": "measures",
             "fields": {"name": "`Incident Response Corps`", "size": "small",
                        "finish_turn": 3}},
        ]})
        + "\n```\n"
    )
    check("section present", present, True)
    check("malformed", malformed, [])
    check("commands parsed", len(commands), 2)
    check("grounds ride along", commands[0].grounds, "inherited programme")

    _cmds, _malformed, _ = parse_store_changes(
        "## Store changes\n"
        + "```json\n"
        + json.dumps({"store": [
            {"op": "add", "table": "measures",
             "fields": {"name": "X", "size": "small", "finish_turn": 4}},
        ]})
        + "\n```\nNo other changes.\n"
    )
    check("trailing prose is not a fault", (_malformed, len(_cmds)), ([], 1))
    outcomes = [store.apply(c, "eu", 1) for c in commands]
    check("all applied", [o.verdict for o in outcomes], ["applied", "applied"])
    check("ids assigned", [o.record_id for o in outcomes], ["M1", "M2"])

    view = StoreView(store, "eu")
    check("decoration normalised", store.live_records("measures")[0].fields["size"], "large")
    check("turn parsed from prose", store.live_records("measures")[0].fields["finish_turn"], 7)
    check("started_turn stamped", store.live_records("measures")[0].fields["started_turn"], 1)
    check("derived map", view.sum("measures", "cost_per_turn"), 5)
    check("count", view.count("measures"), 2)
    check("filtered sum", view.sum("measures", "cost_per_turn", size="large"), 3)
    check("mean", view.mean("measures", "cost_per_turn"), 2.5)
    check("min", view.min("measures", "cost_per_turn"), 2)
    check("rows render", str(view.rows("measures")).count("\n") >= 3, True)
    # The selector surface: the same selector twice, once bare and once reduced.
    check("selector sum", view.rows("measures", ["cost_per_turn"]).sum, 5)
    check(
        "selector filtered sum",
        view.rows("measures", ["cost_per_turn"], size="large").sum,
        3,
    )
    check("selector count", view.rows("measures", status="running").count, 2)
    check(
        "selector narrow render",
        str(view.rows("measures", ["id", "name"], status="running")).count("cost_per_turn"),
        0,
    )

    # Derived status follows the turn, and the running filter with it.
    store.current_turn = 3
    check("status at finish turn", store.value(store.live_records("measures")[1], "status"), "finished")
    check("running charge", view.sum("measures", "cost_per_turn", status="running"), 3)
    store.current_turn = 1

    # Silence means persistence: a turn with no section changes nothing.
    store.begin_turn(2)
    commands, malformed, present = parse_store_changes("## Portfolio\n\nNothing here.\n")
    check("absent section reported", present, False)
    check("nothing lost", len(store.live_records("measures")), 2)

    # Provenance is enforced, not requested.
    store.begin_turn(3)
    commands, _, _ = parse_store_changes(
        "## Store changes\n```json\n"
        + json.dumps({"store": [
            {"op": "update", "table": "measures", "id": "M1",
             "fields": {"started_turn": 2}},
            {"op": "update", "table": "measures", "id": "M1",
             "fields": {"cost_per_turn": 1}},
            {"op": "update", "table": "measures", "id": "M9",
             "fields": {"finish_turn": 4}},
            {"op": "add", "table": "measures",
             "fields": {"name": "No finish turn given"}},
            {"op": "add", "table": "measures",
             "fields": {"name": "X", "size": "enormous", "finish_turn": 4}},
            {"op": "add", "table": "widgets", "fields": {"name": "Y"}},
        ]})
        + "\n```\n"
    )
    verdicts = [store.apply(c, "eu", 3) for c in commands]
    check("update of a system column alone refused", verdicts[0].verdict, "rejected")
    check("update of a derived column alone refused", verdicts[1].verdict, "rejected")
    check("unknown id refused", verdicts[2].verdict, "rejected")
    check("missing required refused", verdicts[3].verdict, "rejected")
    check("bad enum refused", verdicts[4].verdict, "rejected")
    check("unknown table refused", verdicts[5].verdict, "rejected")
    check("nothing applied", len(store.live_records("measures")), 2)
    check("started_turn untouched", store.live_records("measures")[0].fields["started_turn"], 1)


    # Re-running a turn replaces rather than appends.
    store.begin_turn(4)
    commands, _, _ = parse_store_changes(
        "## Store changes\n```json\n"
        + json.dumps({"store": [
            {"op": "add", "table": "measures",
             "fields": {"name": "Twice", "size": "small", "finish_turn": 9}},
        ]})
        + "\n```\n"
    )
    for command in commands:
        store.apply(command, "eu", 4)
    check("added once", len(store.live_records("measures")), 3)
    store.begin_turn(4)
    for command in commands:
        store.apply(command, "eu", 4)
    check("re-run replaces", len(store.live_records("measures")), 3)

    # Deletion, and a round trip through persistence.
    store.begin_turn(5)
    commands, _, _ = parse_store_changes(
        "## Store changes\n```json\n"
        + json.dumps({"store": [
            {"op": "delete", "table": "measures", "id": "M1"},
        ]})
        + "\n```\n"
    )
    check("delete applied", store.apply(commands[0], "eu", 5).verdict, "applied")
    check("delete removes", len(store.live_records("measures")), 2)

    restored = Store(schema)
    restored.restore(json.loads(json.dumps(store.to_dict())))
    restored.current_turn = store.current_turn
    check("round trip records", len(restored.live_records("measures")), 2)
    check(
        "round trip aggregates",
        StoreView(restored, "eu").sum("measures", "cost_per_turn"),
        StoreView(store, "eu").sum("measures", "cost_per_turn"),
    )
    check("counter survives", restored.counters["measures"], store.counters["measures"])

    # A command that names an unwritable column *alongside* the ones the actor
    # owns keeps its measure. The value is dropped, not the command.
    store.begin_turn(6)
    commands, _, _ = parse_store_changes(
        "## Store changes\n```json\n"
        + json.dumps({"store": [
            {"op": "add", "table": "measures",
             "fields": {"name": "Copied the table", "size": "large",
                        "finish_turn": 9, "cost_per_turn": 99, "started_turn": 4}},
        ]})
        + "\n```\n"
    )
    outcome = store.apply(commands[0], "eu", 6)
    check("kept despite unwritable columns", outcome.verdict, "applied")
    check("and said what it dropped", "computed from" in outcome.note, True)
    added = store.find("measures", outcome.record_id)
    check("framework's derivation wins", store.value(added, "cost_per_turn"), 3)
    check("framework's stamp wins", added.fields["started_turn"], 6)

    # Schema strictness.
    for label, bad in (
        ("unknown table key", {"m": {"scope": "actor", "colums": {}}}),
        ("unknown scope", {"m": {"scope": "orbit", "columns": {"id": {"owner": "system"}}}}),
        ("world table without a world column",
         {"m": {"scope": "world", "columns": {"id": {"owner": "system"}}}}),
        ("actor column in a world table", {"m": {"scope": "world", "columns": {
            "id": {"owner": "system"}, "w": {"owner": "world"},
            "n": {"owner": "actor"}}}}),
        ("derived from unknown", {"m": {"columns": {
            "id": {"owner": "system"}, "n": {"owner": "actor"},
            "d": {"owner": "derived", "from": "nope", "map": {"a": 1}}}}}),
        ("enum without values", {"m": {"columns": {
            "id": {"owner": "system"}, "e": {"owner": "actor", "type": "enum"}}}}),
        ("no id column", {"m": {"columns": {"n": {"owner": "actor"}}}}),
        ("no writable column", {"m": {"columns": {"id": {"owner": "system"}}}}),
    ):
        try:
            parse_store_schema(bad)
            failures.append(f"schema '{label}' was accepted and should not have been")
        except StoreSchemaError:
            pass

    # Reference checking against a template.
    errors, warnings = check_store_references(
        schema, "Charge {{ store.sum('measures', 'cost_per_turn', status='running') }}.", "t"
    )
    check("valid reference errors", errors, [])
    check("aggregate without rows warns", len(warnings), 1)
    errors, _ = check_store_references(schema, "{{ store.sum('measures', 'costs') }}", "t")
    check("mistyped column caught", len(errors), 1)
    errors, _ = check_store_references(schema, "{{ store.sum('meausres', 'cost_per_turn') }}", "t")
    check("mistyped table caught", len(errors), 1)
    errors, _ = check_store_references(schema, "{{ store.median('measures', 'x') }}", "t")
    check("unknown operation caught", len(errors), 1)
    errors, _ = check_store_references(
        schema, "{{ store.sum('measures', 'cost_per_turn', size='large', status='running') }}", "t"
    )
    check("two filters caught", len(errors), 1)

    if failures:
        print(f"store self-test FAILED ({len(failures)}):")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("store self-test passed")
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys

    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    print("usage: python -m scenario_lab.store --self-test")
