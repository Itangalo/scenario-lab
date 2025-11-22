"""
Tests for JSON Response Parser module

Tests JSON extraction, parsing, validation, and fallback behavior.
"""
import pytest
from pydantic import ValidationError

from scenario_lab.utils.json_response_parser import (
    ActorDecisionJSON,
    extract_json_from_response,
    parse_json_decision,
    json_to_markdown,
    parse_decision_with_fallback,
    format_json_prompt_instructions,
)


class TestActorDecisionJSONSchema:
    """Tests for ActorDecisionJSON Pydantic model"""

    def test_valid_decision(self):
        """Test valid decision passes validation"""
        data = {
            "goals": {
                "long_term": "Achieve strategic dominance",
                "short_term": "Secure immediate resources"
            },
            "reasoning": "Based on current conditions, this approach is optimal for achieving objectives.",
            "action": "Deploy resources to priority sector and initiate negotiations."
        }
        decision = ActorDecisionJSON(**data)
        assert decision.goals["long_term"] == "Achieve strategic dominance"
        assert decision.goals["short_term"] == "Secure immediate resources"
        assert "strategic dominance" in decision.reasoning or "optimal" in decision.reasoning

    def test_missing_goals_fails(self):
        """Test missing goals field fails validation"""
        data = {
            "reasoning": "Valid reasoning text here",
            "action": "Valid action text here"
        }
        with pytest.raises(ValidationError):
            ActorDecisionJSON(**data)

    def test_reasoning_too_short_fails(self):
        """Test reasoning that is too short fails validation"""
        data = {
            "goals": {"long_term": "Goal", "short_term": "Priority"},
            "reasoning": "Short",
            "action": "Valid action text that is long enough"
        }
        with pytest.raises(ValidationError):
            ActorDecisionJSON(**data)

    def test_action_too_short_fails(self):
        """Test action that is too short fails validation"""
        data = {
            "goals": {"long_term": "Goal", "short_term": "Priority"},
            "reasoning": "Valid reasoning text that is long enough",
            "action": "Short"
        }
        with pytest.raises(ValidationError):
            ActorDecisionJSON(**data)

    def test_extra_fields_allowed(self):
        """Test extra fields are allowed (future extension)"""
        data = {
            "goals": {"long_term": "Goal", "short_term": "Priority"},
            "reasoning": "Valid reasoning text that is long enough",
            "action": "Valid action text that is long enough",
            "custom_field": "Extra data"
        }
        decision = ActorDecisionJSON(**data)
        assert decision.goals is not None


class TestExtractJsonFromResponse:
    """Tests for extract_json_from_response function"""

    def test_json_in_markdown_code_block(self):
        """Test extracting JSON from markdown code block"""
        content = '''Here is my decision:

```json
{
  "goals": {"long_term": "Test", "short_term": "Test"},
  "reasoning": "This is my reasoning",
  "action": "This is my action"
}
```

That concludes my decision.'''

        result = extract_json_from_response(content)
        assert result is not None
        assert '"goals"' in result
        assert '"reasoning"' in result

    def test_json_in_plain_code_block(self):
        """Test extracting JSON from plain code block"""
        content = '''Decision:

```
{"goals": {"long_term": "A", "short_term": "B"}, "reasoning": "C", "action": "D"}
```'''

        result = extract_json_from_response(content)
        assert result is not None
        assert '"goals"' in result

    def test_raw_json_object(self):
        """Test extracting raw JSON object from text"""
        content = '''My decision is {"goals": {"long_term": "A", "short_term": "B"}, "reasoning": "Test reasoning", "action": "Test action"} and that's it.'''

        result = extract_json_from_response(content)
        assert result is not None
        assert '"goals"' in result

    def test_raw_json_array(self):
        """Test extracting raw JSON array from text"""
        content = '''The items are [{"name": "item1"}, {"name": "item2"}] in this list.'''

        result = extract_json_from_response(content)
        assert result is not None
        assert '"name"' in result

    def test_no_json_returns_none(self):
        """Test that text without JSON returns None"""
        content = '''This is just plain text without any JSON content.
It has multiple lines but no structured data.'''

        result = extract_json_from_response(content)
        assert result is None

    def test_empty_content(self):
        """Test empty content returns None"""
        result = extract_json_from_response("")
        assert result is None

    def test_nested_json_object(self):
        """Test extracting nested JSON objects"""
        content = '''{
  "outer": {
    "inner": {
      "value": 42
    }
  }
}'''
        result = extract_json_from_response(content)
        # The regex may extract inner or outer depending on pattern matching
        assert result is not None
        # Just verify it found some JSON
        assert '{' in result


class TestParseJsonDecision:
    """Tests for parse_json_decision function"""

    def test_valid_json_with_validation(self):
        """Test parsing valid JSON with schema validation"""
        content = '''```json
{
  "goals": {"long_term": "Strategic goal", "short_term": "Immediate priority"},
  "reasoning": "This is detailed reasoning about the situation and rationale.",
  "action": "This is the specific action to take this turn."
}
```'''

        result, error = parse_json_decision(content, validate=True)
        assert error is None
        assert result is not None
        assert result["goals"]["long_term"] == "Strategic goal"

    def test_valid_json_without_validation(self):
        """Test parsing valid JSON without schema validation"""
        content = '{"custom_key": "custom_value"}'

        result, error = parse_json_decision(content, validate=False)
        assert error is None
        assert result is not None
        assert result["custom_key"] == "custom_value"

    def test_no_json_found(self):
        """Test error when no JSON is found"""
        content = "Just plain text without JSON"

        result, error = parse_json_decision(content, validate=True)
        assert result is None
        assert error is not None
        assert "No JSON found" in error

    def test_invalid_json_syntax(self):
        """Test error on invalid JSON syntax"""
        content = '{"broken": json without quotes}'

        result, error = parse_json_decision(content, validate=True)
        assert result is None
        assert error is not None
        assert "Invalid JSON" in error

    def test_validation_failure_returns_data_with_warning(self):
        """Test that schema validation failure still returns raw data"""
        # Missing required fields but valid JSON
        content = '{"custom": "data", "other": 123}'

        result, error = parse_json_decision(content, validate=True)
        # Should return data even if validation fails
        assert result is not None
        assert "custom" in result
        assert error is not None
        assert "validation failed" in error.lower()


class TestJsonToMarkdown:
    """Tests for json_to_markdown function"""

    def test_full_decision_conversion(self):
        """Test converting full decision to markdown"""
        decision = {
            "goals": {
                "long_term": "Achieve market leadership",
                "short_term": "Launch new product"
            },
            "reasoning": "Market conditions are favorable for expansion.",
            "action": "Initiate product launch sequence."
        }

        markdown = json_to_markdown(decision)

        assert "**LONG-TERM GOALS:**" in markdown
        assert "Achieve market leadership" in markdown
        assert "**SHORT-TERM PRIORITIES:**" in markdown
        assert "Launch new product" in markdown
        assert "**REASONING:**" in markdown
        assert "Market conditions" in markdown
        assert "**ACTION:**" in markdown
        assert "product launch" in markdown

    def test_partial_decision_conversion(self):
        """Test converting partial decision (missing fields)"""
        decision = {
            "reasoning": "Only reasoning present.",
            "action": "Only action present."
        }

        markdown = json_to_markdown(decision)

        assert "**REASONING:**" in markdown
        assert "Only reasoning present" in markdown
        assert "**ACTION:**" in markdown
        assert "**LONG-TERM GOALS:**" not in markdown

    def test_empty_decision(self):
        """Test converting empty decision"""
        decision = {}

        markdown = json_to_markdown(decision)

        assert markdown == ""

    def test_goals_only_long_term(self):
        """Test goals with only long_term"""
        decision = {
            "goals": {"long_term": "Long term goal only"}
        }

        markdown = json_to_markdown(decision)

        assert "**LONG-TERM GOALS:**" in markdown
        assert "Long term goal only" in markdown
        assert "**SHORT-TERM PRIORITIES:**" not in markdown

    def test_goals_only_short_term(self):
        """Test goals with only short_term"""
        decision = {
            "goals": {"short_term": "Short term priority only"}
        }

        markdown = json_to_markdown(decision)

        assert "**SHORT-TERM PRIORITIES:**" in markdown
        assert "Short term priority only" in markdown
        assert "**LONG-TERM GOALS:**" not in markdown


class TestParseDecisionWithFallback:
    """Tests for parse_decision_with_fallback function"""

    def test_json_parsing_success(self):
        """Test successful JSON parsing"""
        content = '''```json
{
  "goals": {"long_term": "Strategic", "short_term": "Tactical"},
  "reasoning": "Analysis of the situation leads to this conclusion.",
  "action": "Execute the planned initiative."
}
```'''

        result = parse_decision_with_fallback(content)

        assert "goals" in result
        assert "reasoning" in result
        assert "action" in result
        assert "Analysis" in result["reasoning"]

    def test_goals_dict_conversion(self):
        """Test that goals dict is converted to formatted string"""
        content = '''{
  "goals": {"long_term": "Long goal text", "short_term": "Short priority text"},
  "reasoning": "The reasoning here",
  "action": "The action here"
}'''

        result = parse_decision_with_fallback(content)

        assert "**LONG-TERM GOALS:**" in result["goals"]
        assert "Long goal text" in result["goals"]
        assert "**SHORT-TERM PRIORITIES:**" in result["goals"]
        assert "Short priority text" in result["goals"]

    def test_goals_string_preserved(self):
        """Test that goals as string is preserved"""
        content = '''{
  "goals": "Simple string goals",
  "reasoning": "The reasoning here",
  "action": "The action here"
}'''

        result = parse_decision_with_fallback(content)

        assert result["goals"] == "Simple string goals"

    def test_fallback_to_markdown_parser(self):
        """Test fallback to markdown parser when JSON fails"""
        # This content doesn't have valid JSON, should fall back to markdown
        content = '''**LONG-TERM GOALS:**
Establish market presence

**SHORT-TERM PRIORITIES:**
Complete phase one

**REASONING:**
Based on market analysis

**ACTION:**
Launch marketing campaign'''

        result = parse_decision_with_fallback(content)

        # Should have parsed the markdown sections
        assert "goals" in result
        assert "reasoning" in result
        assert "action" in result

    def test_missing_fields_default_to_empty(self):
        """Test that missing fields default to empty strings"""
        content = '{"goals": {"long_term": "Test"}}'

        result = parse_decision_with_fallback(content)

        assert result["reasoning"] == ""
        assert result["action"] == ""


class TestFormatJsonPromptInstructions:
    """Tests for format_json_prompt_instructions function"""

    def test_returns_markdown_string(self):
        """Test that function returns a markdown string"""
        instructions = format_json_prompt_instructions()

        assert isinstance(instructions, str)
        assert len(instructions) > 0

    def test_contains_json_example(self):
        """Test that instructions contain JSON example"""
        instructions = format_json_prompt_instructions()

        assert "```json" in instructions
        assert '"goals"' in instructions
        assert '"reasoning"' in instructions
        assert '"action"' in instructions

    def test_contains_format_guidance(self):
        """Test that instructions contain format guidance"""
        instructions = format_json_prompt_instructions()

        assert "Response Format" in instructions
        assert "long_term" in instructions
        assert "short_term" in instructions

    def test_contains_important_notes(self):
        """Test that instructions contain important notes"""
        instructions = format_json_prompt_instructions()

        assert "Important" in instructions
        assert "valid json object" in instructions.lower()


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_unicode_content(self):
        """Test handling of unicode content"""
        content = '''```json
{
  "goals": {"long_term": "目标", "short_term": "优先事项"},
  "reasoning": "基于当前情况的分析结果",
  "action": "执行计划中的行动"
}
```'''

        result = extract_json_from_response(content)
        assert result is not None
        assert "目标" in result

    def test_special_characters_in_strings(self):
        """Test handling of special characters"""
        content = '''{"goals": {"long_term": "Goal with 'quotes' and \\"escapes\\"", "short_term": "Priority"}, "reasoning": "Text with newlines\\nand tabs\\t", "action": "Action with symbols: @#$%"}'''

        result = extract_json_from_response(content)
        assert result is not None

    def test_very_long_content(self):
        """Test handling of very long content"""
        long_text = "A" * 10000
        content = f'{{"goals": {{"long_term": "{long_text}", "short_term": "B"}}, "reasoning": "C", "action": "D"}}'

        result = extract_json_from_response(content)
        assert result is not None

    def test_multiple_json_objects_returns_first(self):
        """Test that with multiple JSON objects, the function extracts one"""
        content = '''First: {"a": 1} and second: {"b": 2}'''

        result = extract_json_from_response(content)
        assert result is not None
        # Should extract one of them (implementation dependent)
        assert '"a"' in result or '"b"' in result

    def test_json_with_comments_style_content(self):
        """Test JSON-like content with comment-style markers"""
        content = '''```json
{
  "goals": {"long_term": "Test goal", "short_term": "Test priority"},
  "reasoning": "Some reasoning here",
  "action": "Some action here"
}
```
// This is not JSON'''

        result = extract_json_from_response(content)
        assert result is not None
        assert '"goals"' in result
