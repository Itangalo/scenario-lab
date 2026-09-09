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
from typing import Any, Iterable, Optional

# The column owners. This is the load-bearing part of the schema: it is what
# turns "copied forward unchanged" from an instruction the model obeys by
# remembering into something it cannot express at all.
OWNERS = ("system", "actor", "derived")

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
    scope: str                            # "actor" (see parse_store_schema)
    columns: dict[str, StoreColumn]
    id_prefix: str = "R"

    @property
    def id_column(self) -> str:
        """The system-owned identity column, if the schema declares one."""
        for name, column in self.columns.items():
            if column.owner == "system" and column.type == "text":
                return name
        return "id"

    def writable(self) -> list[str]:
        return [n for n, c in self.columns.items() if c.owner == "actor"]


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
            out[name] = {"scope": table.scope, "id_prefix": table.id_prefix, "columns": columns}
        return out


_TABLE_KEYS = {"scope", "columns"}
_COLUMN_KEYS = {"owner", "type", "required", "values", "from", "map", "when_reached", "else"}
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
        if scope != "actor":
            # World-scoped tables are a real part of the design -- alliances,
            # permanent changes to the world -- but they need a writer, and the
            # only step that could write them is the one that also produces the
            # narrative and the metrics JSON. Adding a third parsed section to
            # that step is its own change with its own failure modes. Declared
            # unsupported rather than half-wired, so a scenario cannot quietly
            # depend on a table nothing ever writes to.
            raise StoreSchemaError(
                f"store table '{name}': scope '{scope}' is not supported yet; "
                "only scope: actor is implemented (see docs/ARCHITECTURE.md)"
            )

        raw_columns = body.get("columns")
        if not isinstance(raw_columns, dict) or not raw_columns:
            raise StoreSchemaError(f"store table '{name}' must declare columns")

        columns: dict[str, StoreColumn] = {}
        for col_name, spec in raw_columns.items():
            columns[col_name] = _parse_column(name, col_name, spec)

        _check_derivations(name, columns)
        if not any(c.owner == "system" and c.type == "text" for c in columns.values()):
            raise StoreSchemaError(
                f"store table '{name}' must declare a system-owned text column for the record id "
                "(the actor addresses records by id, never by name)"
            )
        if not any(c.owner == "actor" for c in columns.values()):
            raise StoreSchemaError(
                f"store table '{name}' has no actor-owned column, so nothing could ever be written to it"
            )

        tables[name] = StoreTable(
            name=name, scope=scope, columns=columns, id_prefix=prefixes[name]
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
        if column.required and owner != "actor":
            raise StoreSchemaError(f"{where}: only an actor-owned column can be required")

    return column


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
        return int(match.group(1))

    if column.type == "number":
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if not match:
            raise StoreCommandError(f"column '{column.name}' must be a number, got '{text}'")
        return float(match.group(0))

    raise StoreCommandError(f"column '{column.name}' has unsupported type {column.type}")


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


class Store:
    """The live records, and the only thing allowed to change them."""

    def __init__(self, schema: StoreSchema):
        self.schema = schema
        self.records: list[StoreRecord] = []
        self.counters: dict[str, int] = {name: 0 for name in schema.tables}
        self.current_turn: int = 0
        self._snapshots: dict[int, str] = {}

    # -- state -----------------------------------------------------------

    def live_records(self, table: str, actor_id: Optional[str] = None) -> list[StoreRecord]:
        return [
            r for r in self.records
            if r.table == table and r.live and (actor_id is None or r.actor_id == actor_id)
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

    def row(self, record: StoreRecord) -> dict[str, Any]:
        table = self.schema.tables[record.table]
        return {name: self.value(record, name) for name in table.columns}

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

    def apply(self, command: "StoreCommand", actor_id: str, turn: int) -> StoreOutcome:
        table = self.schema.tables.get(command.table)
        if table is None:
            known = ", ".join(sorted(self.schema.tables)) or "(none)"
            return StoreOutcome(
                command.raw, "rejected",
                f"unknown table '{command.table}' (this scenario declares: {known})",
                grounds=command.grounds,
            )

        try:
            if command.kind == "add":
                record = self._apply_add(table, command, actor_id, turn)
            elif command.kind == "update":
                record = self._apply_update(table, command, actor_id)
            elif command.kind == "delete":
                record = self._apply_delete(table, command, actor_id, turn)
            else:
                raise StoreCommandError(f"unknown command '{command.kind}'")
        except StoreCommandError as err:
            return StoreOutcome(command.raw, "rejected", str(err), grounds=command.grounds)

        return StoreOutcome(command.raw, "applied", record_id=record.id, grounds=command.grounds)

    def _validate_assignments(self, table: StoreTable, command: "StoreCommand") -> dict[str, Any]:
        values: dict[str, Any] = {}
        for name, raw in command.assignments.items():
            column = table.columns.get(name)
            if column is None:
                known = ", ".join(table.writable())
                raise StoreCommandError(
                    f"'{table.name}' has no column '{name}' (you may set: {known})"
                )
            if column.owner == "system":
                raise StoreCommandError(
                    f"column '{name}' is stamped by the framework and cannot be set"
                )
            if column.owner == "derived":
                raise StoreCommandError(
                    f"column '{name}' is computed from '{column.source}' and cannot be set directly"
                )
            values[name] = normalize_value(column, raw)
        return values

    def _apply_add(
        self, table: StoreTable, command: "StoreCommand", actor_id: str, turn: int
    ) -> StoreRecord:
        values = self._validate_assignments(table, command)
        missing = [
            name for name, column in table.columns.items()
            if column.owner == "actor" and column.required and name not in values
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
        return record

    def _apply_update(
        self, table: StoreTable, command: "StoreCommand", actor_id: str
    ) -> StoreRecord:
        record = self.find(table.name, command.record_id, actor_id)
        if record is None:
            raise StoreCommandError(f"no live record '{command.record_id}' in '{table.name}'")
        values = self._validate_assignments(table, command)
        if not values:
            raise StoreCommandError("an update must set at least one column")
        record.fields.update(values)
        return record

    def _apply_delete(
        self, table: StoreTable, command: "StoreCommand", actor_id: str, turn: int
    ) -> StoreRecord:
        record = self.find(table.name, command.record_id, actor_id)
        if record is None:
            raise StoreCommandError(f"no live record '{command.record_id}' in '{table.name}'")
        record.removed_turn = turn
        return record

    # -- persistence -----------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "counters": dict(self.counters),
            "records": [
                {
                    "id": r.id,
                    "table": r.table,
                    "actor": r.actor_id,
                    "fields": dict(r.fields),
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
# Commands
# --------------------------------------------------------------------------


@dataclass
class StoreCommand:
    """One parsed write."""

    kind: str                              # "add" | "update" | "delete"
    table: str
    record_id: str = ""
    assignments: dict[str, str] = field(default_factory=dict)
    grounds: str = ""
    raw: str = ""


# Matched leniently for the same reason the statement section is: an actor gets
# a heading level wrong often enough that strictness costs more than it buys,
# and a discarded section is indistinguishable from an actor that changed
# nothing.
_SECTION_RE = re.compile(
    r"^[ \t]{0,3}(?P<hashes>#{1,6})[ \t]+Store changes\b[^\n]*$",
    re.IGNORECASE | re.MULTILINE,
)

_ADD_RE = re.compile(r"^add\s+(?P<table>[a-z][a-z0-9_]*)\s*:\s*(?P<body>.+)$", re.IGNORECASE)
_UPDATE_RE = re.compile(
    r"^update\s+(?P<table>[a-z][a-z0-9_]*)\s+(?P<id>[A-Za-z]+\d+)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE,
)
_DELETE_RE = re.compile(
    r"^delete\s+(?P<table>[a-z][a-z0-9_]*)\s+(?P<id>[A-Za-z]+\d+)\s*\.?$", re.IGNORECASE
)
_GROUNDS_RE = re.compile(r"^grounds\s*:\s*(?P<value>.+)$", re.IGNORECASE)

# "No other changes." written after a command, which actors do. It is not a
# command and it is not malformed, and counting it as either poisons the one
# channel that says whether the turn went wrong: a fault report only means
# something while everything in it is a fault.
_NO_OP_LINE_RE = re.compile(
    r"^no\s+(?:other|further|more|additional|remaining)?\s*(?:store\s+)?changes?\b[\s.]*$",
    re.IGNORECASE,
)
_CODE_SPAN_RE = re.compile(r"^(?P<fence>`{1,}) *(?P<body>.+?) *(?P=fence)$", re.DOTALL)


def _next_section_re(level: int) -> re.Pattern[str]:
    return re.compile(rf"^[ \t]{{0,3}}#{{1,{level}}}[ \t]+", re.MULTILINE)


def _strip_code_span(item: str) -> str:
    match = _CODE_SPAN_RE.match(item.strip())
    return match.group("body").strip() if match else item


def _split_assignments(body: str) -> dict[str, str]:
    """``name = "x"; size = large`` to a mapping.

    Semicolon-separated because a measure name contains commas far more often
    than it contains semicolons, and requiring quoting of every value is a
    rule a model follows about as reliably as it copied the portfolio.
    """
    assignments: dict[str, str] = {}
    last: Optional[str] = None
    for part in body.split(";"):
        if not part.strip():
            continue
        key, sep, value = part.partition("=")
        name = key.strip().strip("`*_").lower()
        if not sep or not name or " " in name:
            # A semicolon inside a value rather than between pairs. Free text
            # columns invite this -- "resilience +3 to +6; sentiment +1" is a
            # natural thing to write -- and rejecting the whole command over
            # punctuation would lose a measure to a keystroke, which is the
            # class of failure this mechanism exists to remove. Put it back.
            if last is None:
                raise StoreCommandError(f"'{part.strip()}' is not a `column = value` pair")
            assignments[last] = f"{assignments[last]}; {part.strip()}"
            continue
        assignments[name] = value.strip()
        last = name
    if not assignments:
        raise StoreCommandError("no `column = value` pairs given")
    return assignments


def parse_store_changes(output: str) -> tuple[list[StoreCommand], list[str], bool]:
    """Extract commands from an actor's response.

    Returns ``(commands, malformed_lines, section_present)``.

    ``section_present`` is reported rather than inferred because its absence is
    the failure this whole mechanism exists to make visible. A missing section
    is detectable; a missing inline command never was, and that is the larger
    half of the measured defect.
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

    commands: list[StoreCommand] = []
    malformed: list[str] = []

    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        item = re.sub(r"^[-*+]\s+", "", stripped)
        item = _strip_code_span(item)
        if not item or item.lower().rstrip(".") in NO_CHANGES_MARKERS:
            continue
        if _NO_OP_LINE_RE.match(item):
            continue

        grounds = _GROUNDS_RE.match(item)
        if grounds:
            if commands:
                commands[-1].grounds = grounds.group("value").strip()
            continue

        parsed = _parse_command_line(item)
        if parsed is None:
            # A continuation of a wrapped Grounds line is not malformed.
            if line.startswith(("  ", "\t")) and commands:
                continue
            malformed.append(item)
            continue
        commands.append(parsed)

    return commands, malformed, True


def _parse_command_line(item: str) -> Optional[StoreCommand]:
    match = _ADD_RE.match(item)
    if match:
        try:
            assignments = _split_assignments(match.group("body"))
        except StoreCommandError:
            return StoreCommand(kind="add", table=match.group("table").lower(), raw=item)
        return StoreCommand(
            kind="add",
            table=match.group("table").lower(),
            assignments=assignments,
            raw=item,
        )

    match = _UPDATE_RE.match(item)
    if match:
        try:
            assignments = _split_assignments(match.group("body"))
        except StoreCommandError:
            assignments = {}
        return StoreCommand(
            kind="update",
            table=match.group("table").lower(),
            record_id=match.group("id").upper(),
            assignments=assignments,
            raw=item,
        )

    match = _DELETE_RE.match(item)
    if match:
        return StoreCommand(
            kind="delete",
            table=match.group("table").lower(),
            record_id=match.group("id").upper(),
            raw=item,
        )

    return None


# --------------------------------------------------------------------------
# The read surface
# --------------------------------------------------------------------------


# Aliased because the view's own methods are named after them, and reading
# ``_builtin_sum`` at the call site is clearer than relying on the reader to
# remember that a class attribute does not shadow a global.
_builtin_sum = sum
_builtin_min = min
_builtin_max = max


class StoreView:
    """What ``{{ store.… }}`` can do inside a template.

    Closed and small by design. Five aggregates, one equality filter, no
    joins, no arithmetic between aggregates. A rule that needs more than this
    is asking for judgement, and judgement is the LLM's job -- which is the
    whole reason the arithmetic was worth taking away from it.
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

    # -- aggregates ------------------------------------------------------

    def sum(self, table: str, column: str, **where: Any) -> Any:
        return self._tidy(_builtin_sum(self._numbers(table, column, where)))

    def count(self, table: str, **where: Any) -> int:
        return len(self._select(table, where))

    def min(self, table: str, column: str, **where: Any) -> Any:
        values = self._numbers(table, column, where)
        return self._tidy(_builtin_min(values)) if values else "(none)"

    def max(self, table: str, column: str, **where: Any) -> Any:
        values = self._numbers(table, column, where)
        return self._tidy(_builtin_max(values)) if values else "(none)"

    def mean(self, table: str, column: str, **where: Any) -> Any:
        values = self._numbers(table, column, where)
        # An empty mean is undefined, and rendering it as 0 would put an
        # authoritative-looking number where there is no answer. These values
        # are read as prose by a model, never consumed by Python arithmetic,
        # so a visible marker is the honest rendering.
        return self._tidy(_builtin_sum(values) / len(values)) if values else "(none)"

    def rows(self, table: str, **where: Any) -> str:
        """The itemised rows, as a markdown table.

        ``design-notes.md`` records that the portfolio charge binds *because*
        "the total cannot be known without summing it". Handing over a
        pre-computed total on its own risks the Game Master ceasing to attend
        to the portfolio at all, and the narrative drifting free of the store
        rather than the reverse. Every total is meant to be rendered beside
        these rows, and the validator warns when one is not.
        """
        records = self._select(table, where)
        schema_table = self._store.schema.tables[table]
        columns = list(schema_table.columns)
        multi_actor = len({r.actor_id for r in self._store.live_records(table)}) > 1
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
        lines += [f"## {table_name}", "", view.rows(table_name), ""]

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
        if outcome.reason:
            lines.append(f"  - Reason: {outcome.reason}")
    for line in malformed:
        lines.append(f"- **unparsed** — {line}")
        lines.append("  - Reason: not a recognised `add` / `update` / `delete` command")

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Template references
# --------------------------------------------------------------------------

_CALL_RE = re.compile(
    r"\bstore(?:\.actor\(\s*['\"][^'\"]*['\"]\s*\))?"
    r"\.(?P<method>[a-z_]+)\(\s*(?P<args>[^)]*)\)",
    re.IGNORECASE,
)
_STRING_ARG_RE = re.compile(r"['\"]([^'\"]*)['\"]")
_KWARG_RE = re.compile(r"([a-z_][a-z0-9_]*)\s*=")


@dataclass
class StoreReference:
    """One ``store.…`` call found in a template, for validation."""

    method: str
    table: Optional[str]
    column: Optional[str]
    kwargs: tuple[str, ...]
    raw: str


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
    for match in _CALL_RE.finditer(text):
        args = match.group("args")
        strings = _STRING_ARG_RE.findall(args)
        method = match.group("method").lower()
        table = strings[0] if strings else None
        column = strings[1] if len(strings) > 1 else None
        if method in ("count", "rows"):
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
        elif ref.method != "count":
            aggregated.add(ref.table)
        else:
            aggregated.add(ref.table)

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
        "## Store changes\n\n"
        "- add measures: name = InvestAI Gigafactories; size = **Large**; finish_turn = turn 7\n"
        "  - Grounds: inherited programme\n"
        "- add measures: name = `Incident Response Corps`; size = small; finish_turn = 3\n"
    )
    check("section present", present, True)
    check("malformed", malformed, [])
    check("commands parsed", len(commands), 2)

    _cmds, _malformed, _ = parse_store_changes(
        "## Store changes\n"
        "- add measures: name = X; size = small; finish_turn = 4\n"
        "- No other changes.\n"
    )
    check("trailing no-op is not a fault", (_malformed, len(_cmds)), ([], 1))
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
    check("rows render", view.rows("measures").count("\n") >= 3, True)

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
        "## Store changes\n"
        "- update measures M1: started_turn = 2\n"
        "- update measures M1: cost_per_turn = 1\n"
        "- update measures M9: finish_turn = 4\n"
        "- add measures: name = No finish turn given\n"
        "- add measures: name = X; size = enormous; finish_turn = 4\n"
        "- add widgets: name = Y\n"
    )
    verdicts = [store.apply(c, "eu", 3) for c in commands]
    check("system column refused", verdicts[0].verdict, "rejected")
    check("derived column refused", verdicts[1].verdict, "rejected")
    check("unknown id refused", verdicts[2].verdict, "rejected")
    check("missing required refused", verdicts[3].verdict, "rejected")
    check("bad enum refused", verdicts[4].verdict, "rejected")
    check("unknown table refused", verdicts[5].verdict, "rejected")
    check("nothing applied", len(store.live_records("measures")), 2)

    # Re-running a turn replaces rather than appends.
    store.begin_turn(4)
    commands, _, _ = parse_store_changes(
        "## Store changes\n- add measures: name = Twice; size = small; finish_turn = 9\n"
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
    commands, _, _ = parse_store_changes("## Store changes\n- delete measures M1\n")
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

    # Schema strictness.
    for label, bad in (
        ("unknown table key", {"m": {"scope": "actor", "colums": {}}}),
        ("world scope", {"m": {"scope": "world", "columns": {"id": {"owner": "system"}}}}),
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
