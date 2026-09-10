"""Tests for shared LLM types (LLMResponse and related parsing utilities)."""

import json
import pytest

from scenario_lab.llm import LLMError, LLMParseError, LLMResponse


def test_llm_response_extract_json_from_code_block():
    resp = LLMResponse(
        content='Here is the json:\n```json\n{"key": "value"}\n```',
        raw_response={},
    )
    assert resp.extract_json() == {"key": "value"}


def test_llm_response_extract_json_from_raw_content():
    resp = LLMResponse(content='{"key": "value"}', raw_response={})
    assert resp.extract_json() == {"key": "value"}


def test_llm_response_extract_json_array():
    resp = LLMResponse(content='```json\n[{"id": "1"}]\n```', raw_response={})
    assert resp.extract_json_array() == [{"id": "1"}]


def test_llm_response_extract_json_invalid():
    resp = LLMResponse(content="Not json", raw_response={})
    with pytest.raises(json.JSONDecodeError):
        resp.extract_json()


def test_extract_metrics_and_narrative():
    content = """
## Metrics
```json
{"metric1": 10}
```

## Narrative
This is the narrative.

## Notepad
This is the notepad.
"""
    resp = LLMResponse(content=content, raw_response={})
    metrics, narrative, notepad = resp.extract_metrics_and_narrative()

    assert metrics == {"metric1": 10}
    assert narrative == "This is the narrative."
    assert notepad == "This is the notepad."


def test_extract_metrics_malformed():
    resp = LLMResponse(content="No metrics here", raw_response={})
    with pytest.raises(LLMParseError, match="Could not find metrics"):
        resp.extract_metrics_and_narrative()


def test_store_changes_are_not_carried_in_the_notepad():
    """A ## Store changes section after ## Notepad is writes, not memory.

    Without the cut the block rides the notepad into every later prompt --
    a sign-off read caught the events prompt carrying a whole store block
    inside the notepad -- and sits beside the live records as a stale copy.
    """
    content = """
## Metrics
```json
{"metric1": 10}
```

## Narrative
This is the narrative.

## Notepad
PORTFOLIO CHARGE: A −3 = −3

## Store changes
```json
{"store": []}
```
"""
    resp = LLMResponse(content=content, raw_response={})
    _metrics, _narrative, notepad = resp.extract_metrics_and_narrative()
    assert notepad == "PORTFOLIO CHARGE: A −3 = −3"
    assert "Store changes" not in notepad


def test_get_finish_reason():
    resp = LLMResponse(
        content="x",
        raw_response={"choices": [{"finish_reason": "length"}]},
    )
    assert resp.get_finish_reason() == "length"


def test_get_finish_reason_missing():
    resp = LLMResponse(content="x", raw_response={})
    assert resp.get_finish_reason() is None
