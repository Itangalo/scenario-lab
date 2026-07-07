"""JSON schemas for provider-native structured outputs.

These schemas mirror exactly what the prompt templates ask the LLM to produce.
They must not change what the prompt asks for – the event-condition eval suites
in ``tests/evals/`` depend on the prompt semantics staying stable.
"""

from typing import Final

EVENTS_SCHEMA_NAME: Final[str] = "events_evaluation"

# The events prompt asks for a JSON array of objects, each with exactly two keys:
# ``id`` (string) and ``probability`` (number between 0 and 1). Providers that
# require an object at the top level (Anthropic forced tool calls) wrap this
# array under an ``events`` property; the array element schema is shared.
EVENT_ITEM_SCHEMA: Final[dict] = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "probability": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
    },
    "required": ["id", "probability"],
    "additionalProperties": False,
}

# Extended item shape used when emergent events are enabled. Strict structured
# output modes require every property to be listed in ``required``, so listed
# events set ``"emergent": false`` and ``"description": ""`` rather than
# omitting the fields. The prompt states this contract explicitly.
EMERGENT_EVENT_ITEM_SCHEMA: Final[dict] = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "probability": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
        "emergent": {"type": "boolean"},
        "description": {"type": "string"},
    },
    "required": ["id", "probability", "emergent", "description"],
    "additionalProperties": False,
}


def events_array_schema(emergent: bool = False) -> dict:
    """Return the bare top-level array schema for the events response.

    Used by providers (such as OpenRouter via ``response_format``) that can
    constrain output to an array directly.

    Args:
        emergent: Use the extended item shape that allows Game Master-proposed
            emergent events (adds required ``emergent`` and ``description``).
    """
    return {
        "type": "array",
        "items": EMERGENT_EVENT_ITEM_SCHEMA if emergent else EVENT_ITEM_SCHEMA,
    }


def events_object_schema(emergent: bool = False) -> dict:
    """Return an object schema wrapping the events array under ``events``.

    Used by providers (such as Anthropic forced tool calls) whose ``input_schema``
    must have an object at the top level.
    """
    return {
        "type": "object",
        "properties": {
            "events": events_array_schema(emergent),
        },
        "required": ["events"],
        "additionalProperties": False,
    }
