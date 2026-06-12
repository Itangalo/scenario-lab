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


def events_array_schema() -> dict:
    """Return the bare top-level array schema for the events response.

    Used by providers (such as OpenRouter via ``response_format``) that can
    constrain output to an array directly.
    """
    return {
        "type": "array",
        "items": EVENT_ITEM_SCHEMA,
    }


def events_object_schema() -> dict:
    """Return an object schema wrapping the events array under ``events``.

    Used by providers (such as Anthropic forced tool calls) whose ``input_schema``
    must have an object at the top level.
    """
    return {
        "type": "object",
        "properties": {
            "events": events_array_schema(),
        },
        "required": ["events"],
        "additionalProperties": False,
    }
