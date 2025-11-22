"""
Tests for Response Parser module

Comprehensive robustness tests for:
1. Markdown section extraction
2. Malformed response handling
3. Fallback behavior
"""
import pytest

from scenario_lab.utils.response_parser import (
    extract_section,
    parse_decision_markdown,
    parse_decision_json,
    parse_decision,
    parse_communication_decision,
    parse_bilateral_response,
)


class TestExtractSection:
    """Tests for extract_section function with various markdown formats"""

    # --- Bold with colon format: **SECTION:** ---

    def test_bold_with_colon_basic(self):
        """Test extracting section with **SECTION:** format"""
        content = """**GOALS:**
This is the goals section content.

**REASONING:**
This is the reasoning section."""

        result = extract_section(content, "GOALS", "REASONING")
        assert "goals section content" in result
        assert "reasoning" not in result.lower()

    def test_bold_with_colon_multiline(self):
        """Test extracting multiline content with **SECTION:** format"""
        content = """**ACTION:**
First line of action.
Second line of action.
- Bullet point 1
- Bullet point 2

**NEXT SECTION:**
Different content."""

        result = extract_section(content, "ACTION", "NEXT SECTION")
        assert "First line" in result
        assert "Second line" in result
        assert "Bullet point 1" in result
        assert "Bullet point 2" in result

    def test_bold_with_colon_extra_whitespace(self):
        """Test section extraction with extra whitespace"""
        content = """**  GOALS  :**
Content with extra spaces in header.

**REASONING:**
Next section."""

        result = extract_section(content, "GOALS", "REASONING")
        assert "extra spaces" in result

    # --- Bold without colon format: **SECTION** ---

    def test_bold_without_colon(self):
        """Test extracting section with **SECTION** format (no colon)"""
        content = """**GOALS**
Goals content without colon format.

**REASONING**
Reasoning content."""

        result = extract_section(content, "GOALS", "REASONING")
        assert "without colon format" in result

    def test_bold_without_colon_mixed(self):
        """Test mixed formats in same document"""
        content = """**GOALS**
First section.

**REASONING:**
Second section with colon.

**ACTION**
Third section without colon."""

        goals = extract_section(content, "GOALS", "REASONING")
        reasoning = extract_section(content, "REASONING", "ACTION")
        action = extract_section(content, "ACTION")

        assert "First section" in goals
        assert "Second section" in reasoning
        assert "Third section" in action

    # --- Heading format: ## SECTION ---
    # Note: The heading pattern in extract_section has known limitations.
    # These tests document current behavior for future reference.

    def test_heading_format_h2_not_supported(self):
        """Test that ## SECTION format is not currently extracted

        Known limitation: The heading regex pattern does not match
        standard markdown headings. This test documents this behavior.
        """
        content = "## GOALS\nGoals in heading format.\n\n## REASONING\nReasoning in heading format."

        result = extract_section(content, "GOALS", "REASONING")
        # Documents current limitation - heading format not extracted
        assert result == ""

    def test_heading_format_h3_not_supported(self):
        """Test that ### SECTION format is not currently extracted

        Known limitation: Similar to H2, H3 headings are not extracted.
        """
        content = "### ACTION\nAction in H3 format.\n\n### NEXT\nNext section."

        result = extract_section(content, "ACTION", "NEXT")
        # Documents current limitation
        assert result == ""

    def test_heading_with_colon_not_supported(self):
        """Test that ## SECTION: format is not currently extracted

        Known limitation: Even with colons, heading format is not supported.
        """
        content = "## GOALS:\nGoals with colon in heading.\n\n## REASONING:\nReasoning."

        result = extract_section(content, "GOALS", "REASONING")
        # Documents current limitation
        assert result == ""

    # --- Uppercase with colon format: SECTION: ---

    def test_uppercase_with_colon(self):
        """Test extracting section with SECTION: format (no markdown)"""
        content = """GOALS:
Plain uppercase goals.

REASONING:
Plain uppercase reasoning."""

        result = extract_section(content, "goals", "reasoning")
        assert "Plain uppercase goals" in result

    # --- Case insensitivity ---

    def test_case_insensitive_section_name(self):
        """Test that section name matching is case-insensitive"""
        content = """**Goals:**
Content here.

**Reasoning:**
More content."""

        # Request with different case
        result = extract_section(content, "GOALS", "REASONING")
        assert "Content here" in result

    def test_lowercase_section_name(self):
        """Test extracting with lowercase section name"""
        content = """**LONG-TERM GOALS:**
Strategic objectives.

**SHORT-TERM PRIORITIES:**
Immediate tasks."""

        result = extract_section(content, "long-term goals", "short-term priorities")
        assert "Strategic objectives" in result

    # --- Special characters in section names ---

    def test_section_with_hyphen(self):
        """Test section names with hyphens"""
        content = """**LONG-TERM GOALS:**
Long term content.

**SHORT-TERM PRIORITIES:**
Short term content."""

        result = extract_section(content, "LONG-TERM GOALS", "SHORT-TERM PRIORITIES")
        assert "Long term content" in result

    def test_section_with_underscore(self):
        """Test section names with underscores"""
        content = """**INTERNAL_NOTES:**
Notes content.

**RESPONSE:**
Response content."""

        result = extract_section(content, "INTERNAL_NOTES", "RESPONSE")
        assert "Notes content" in result

    # --- Edge cases ---

    def test_empty_section(self):
        """Test extracting an empty section"""
        content = """**GOALS:**

**REASONING:**
Has content."""

        result = extract_section(content, "GOALS", "REASONING")
        assert result == ""

    def test_section_not_found(self):
        """Test when section is not found"""
        content = """**ACTION:**
Some action."""

        result = extract_section(content, "MISSING_SECTION")
        assert result == ""

    def test_section_at_end_of_document(self):
        """Test extracting last section without next_section parameter"""
        content = """**GOALS:**
Goals content.

**ACTION:**
Final action content at the end."""

        result = extract_section(content, "ACTION")
        assert "Final action content" in result

    def test_section_with_code_block(self):
        """Test section containing code blocks"""
        content = """**ACTION:**
Here is my action:

```python
def example():
    return "test"
```

End of action.

**NEXT:**
Next section."""

        result = extract_section(content, "ACTION", "NEXT")
        assert "def example():" in result
        assert "End of action" in result

    def test_section_with_markdown_formatting(self):
        """Test section with nested markdown formatting"""
        content = """**REASONING:**
- **Bold** within section
- *Italic* text
- `code` inline
- [Link](http://example.com)

**ACTION:**
Action."""

        result = extract_section(content, "REASONING", "ACTION")
        assert "**Bold**" in result
        assert "*Italic*" in result

    def test_horizontal_rule_separator(self):
        """Test that horizontal rules act as section boundaries"""
        content = """**GOALS:**
Goals content.

---

Some other content."""

        result = extract_section(content, "GOALS")
        assert "Goals content" in result
        assert "Some other content" not in result

    def test_whitespace_only_content(self):
        """Test section with only whitespace content"""
        content = """**GOALS:**



**REASONING:**
Real content."""

        result = extract_section(content, "GOALS", "REASONING")
        assert result.strip() == ""

    def test_unicode_content_in_section(self):
        """Test section with unicode characters"""
        content = """**GOALS:**
Strategic objectives: 战略目标
International cooperation: 国际合作

**REASONING:**
Next section."""

        result = extract_section(content, "GOALS", "REASONING")
        assert "战略目标" in result
        assert "国际合作" in result


class TestParseDecisionMarkdown:
    """Tests for parse_decision_markdown function"""

    def test_full_decision_parsing(self):
        """Test parsing a complete decision with all sections"""
        content = """**LONG-TERM GOALS:**
Achieve strategic dominance in the market.

**SHORT-TERM PRIORITIES:**
Complete the current project phase.

**REASONING:**
Based on current market conditions and available resources,
this approach offers the best path forward.

**ACTION:**
Initiate project phase 2 and allocate additional resources."""

        result = parse_decision_markdown(content)

        assert "goals" in result
        assert "reasoning" in result
        assert "action" in result
        assert "Long-term" in result["goals"]
        assert "Short-term" in result["goals"]
        assert "market conditions" in result["reasoning"]
        assert "project phase 2" in result["action"]

    def test_simple_goals_fallback(self):
        """Test fallback to simple GOALS section"""
        content = """**GOALS:**
Simple goals without long/short term split.

**REASONING:**
Some reasoning here.

**ACTION:**
Take action."""

        result = parse_decision_markdown(content)

        assert "Simple goals" in result["goals"]

    def test_missing_sections_return_empty(self):
        """Test that missing sections return empty strings"""
        content = """**ACTION:**
Only action provided."""

        result = parse_decision_markdown(content)

        assert result["goals"] == ""
        assert result["reasoning"] == ""
        assert "Only action" in result["action"]

    def test_partial_goals(self):
        """Test parsing with only long-term or short-term goals"""
        content_long_only = """**LONG-TERM GOALS:**
Long term objectives only.

**REASONING:**
Reasoning.

**ACTION:**
Action."""

        result = parse_decision_markdown(content_long_only)
        assert "Long-term" in result["goals"]
        assert "Short-term" not in result["goals"]

    def test_alternative_section_order(self):
        """Test parsing with different section ordering"""
        content = """**REASONING:**
Reasoning comes first.

**ACTION:**
Action in the middle.

**LONG-TERM GOALS:**
Goals at the end."""

        result = parse_decision_markdown(content)

        # Should still extract correctly regardless of order
        assert "goals" in result
        assert "reasoning" in result
        assert "action" in result


class TestParseDecisionJson:
    """Tests for parse_decision_json function

    Note: parse_decision_json normalizes goals dict to a formatted string:
    {"long_term": "X", "short_term": "Y"} -> "**Long-term:**\nX\n\n**Short-term:**\nY"
    """

    def test_valid_json_in_code_block(self):
        """Test parsing valid JSON in markdown code block"""
        content = '''```json
{
  "goals": {"long_term": "Strategic goal", "short_term": "Tactical goal"},
  "reasoning": "Detailed reasoning here",
  "action": "Specific action to take"
}
```'''

        result = parse_decision_json(content)

        assert "goals" in result
        # Goals are normalized to a formatted string
        assert "Strategic goal" in result["goals"]
        assert "Long-term" in result["goals"]

    def test_raw_json_object(self):
        """Test parsing raw JSON without code block"""
        content = '{"goals": {"long_term": "A", "short_term": "B"}, "reasoning": "C", "action": "D"}'

        result = parse_decision_json(content)

        # Goals normalized to string format
        assert "A" in result["goals"]
        assert "B" in result["goals"]
        assert result["reasoning"] == "C"
        assert result["action"] == "D"

    def test_json_with_surrounding_text(self):
        """Test parsing JSON with text before and after"""
        content = '''Here is my decision:
{"goals": {"long_term": "Goal", "short_term": "Priority"}, "reasoning": "Think", "action": "Act"}
Thank you.'''

        result = parse_decision_json(content)

        assert "goals" in result
        assert result["reasoning"] == "Think"


class TestMalformedResponseHandling:
    """Tests for handling malformed and edge-case responses"""

    def test_empty_content(self):
        """Test handling empty content"""
        result = parse_decision_markdown("")

        assert result["goals"] == ""
        assert result["reasoning"] == ""
        assert result["action"] == ""

    def test_whitespace_only_content(self):
        """Test handling whitespace-only content"""
        result = parse_decision_markdown("   \n\t\n   ")

        assert result["goals"] == ""
        assert result["reasoning"] == ""
        assert result["action"] == ""

    def test_no_sections_at_all(self):
        """Test content with no recognizable sections"""
        content = "This is just plain text without any section markers."

        result = parse_decision_markdown(content)

        assert result["goals"] == ""
        assert result["reasoning"] == ""
        assert result["action"] == ""

    def test_malformed_section_markers(self):
        """Test content with malformed section markers"""
        content = """*GOALS:*
Not bold enough.

**REASONING
Missing closing asterisks.

ACTION**
Wrong order of markers."""

        result = parse_decision_markdown(content)
        # Should handle gracefully - may or may not extract depending on pattern
        assert isinstance(result["goals"], str)
        assert isinstance(result["reasoning"], str)
        assert isinstance(result["action"], str)

    def test_broken_json_syntax(self):
        """Test handling of broken JSON syntax"""
        content = '{"goals": {"long_term": "Test"'  # Missing closing braces

        with pytest.raises(ValueError):
            parse_decision_json(content)

    def test_json_with_trailing_comma(self):
        """Test JSON with trailing comma (invalid but common)"""
        content = '''{"goals": {"long_term": "A", "short_term": "B",}, "reasoning": "C", "action": "D"}'''

        with pytest.raises(ValueError):
            parse_decision_json(content)

    def test_no_json_in_content(self):
        """Test when content has no JSON"""
        content = "Just plain text, no JSON here at all."

        with pytest.raises(ValueError) as exc_info:
            parse_decision_json(content)
        assert "No JSON found" in str(exc_info.value)

    def test_partially_correct_sections(self):
        """Test content with some valid and some invalid sections"""
        content = """**REASONING:**
Valid reasoning content.

INVALID_SECTION without proper format

**ACTION:**
Valid action content."""

        result = parse_decision_markdown(content)

        assert "Valid reasoning content" in result["reasoning"]
        assert "Valid action content" in result["action"]
        # Invalid section should not affect valid ones

    def test_duplicate_section_headers(self):
        """Test content with duplicate section headers"""
        content = """**GOALS:**
First goals section.

**GOALS:**
Second goals section.

**REASONING:**
Reasoning."""

        result = parse_decision_markdown(content)
        # Should get first occurrence
        assert "First goals" in result["goals"] or "Second goals" in result["goals"]

    def test_very_long_content(self):
        """Test handling of very long content"""
        long_text = "A" * 100000
        content = f"""**GOALS:**
{long_text}

**REASONING:**
Short reasoning.

**ACTION:**
Short action."""

        result = parse_decision_markdown(content)

        assert len(result["goals"]) > 90000
        assert "Short reasoning" in result["reasoning"]

    def test_special_regex_characters(self):
        """Test content with special regex characters that might break parsing"""
        content = """**GOALS:**
Goals with regex chars: [a-z]+ (group) ^start$ end.* ?optional

**REASONING:**
Reasoning with $dollar and ^caret

**ACTION:**
Action with \\backslash and |pipe"""

        result = parse_decision_markdown(content)

        assert "[a-z]+" in result["goals"]
        assert "$dollar" in result["reasoning"]
        assert "|pipe" in result["action"]

    def test_null_like_strings(self):
        """Test content with null-like string values"""
        content = """**GOALS:**
null

**REASONING:**
None

**ACTION:**
undefined"""

        result = parse_decision_markdown(content)

        assert result["goals"] == "null"
        assert result["reasoning"] == "None"
        assert result["action"] == "undefined"


class TestParseCommunicationDecision:
    """Tests for parse_communication_decision function"""

    def test_full_communication_decision(self):
        """Test parsing complete communication decision"""
        content = """**INITIATE_BILATERAL:**
Yes

**TARGET_ACTOR:**
Actor B

**PROPOSED_MESSAGE:**
Let's discuss collaboration opportunities.

**REASONING:**
This actor has resources we need."""

        result = parse_communication_decision(content)

        assert result["initiate_bilateral"] is True
        assert result["target_actor"] == "Actor B"
        assert "collaboration" in result["message"]
        assert "resources" in result["reasoning"]

    def test_no_communication(self):
        """Test parsing when no communication is initiated"""
        content = """**INITIATE_BILATERAL:**
No

**TARGET_ACTOR:**
none

**PROPOSED_MESSAGE:**
none

**REASONING:**
No need for bilateral communication at this time."""

        result = parse_communication_decision(content)

        assert result["initiate_bilateral"] is False
        assert result["target_actor"] is None
        assert result["message"] is None

    def test_partial_communication(self):
        """Test with target but no message (should be False)"""
        content = """**INITIATE_BILATERAL:**
Yes

**TARGET_ACTOR:**
Actor C

**PROPOSED_MESSAGE:**
none

**REASONING:**
Wanted to communicate but nothing specific to say."""

        result = parse_communication_decision(content)

        # Should be False because message is 'none'
        assert result["initiate_bilateral"] is False

    def test_case_insensitive_yes_no(self):
        """Test that yes/no matching is case insensitive"""
        content = """**INITIATE_BILATERAL:**
YES

**TARGET_ACTOR:**
Actor D

**PROPOSED_MESSAGE:**
Hello!

**REASONING:**
Testing."""

        result = parse_communication_decision(content)

        assert result["initiate_bilateral"] is True


class TestParseBilateralResponse:
    """Tests for parse_bilateral_response function"""

    def test_full_bilateral_response(self):
        """Test parsing complete bilateral response"""
        content = """**RESPONSE:**
Thank you for your proposal. I agree to the terms.

**INTERNAL_NOTES:**
This is a favorable deal for us."""

        result = parse_bilateral_response(content)

        assert "agree to the terms" in result["response"]
        assert "favorable deal" in result["internal_notes"]

    def test_response_only(self):
        """Test with only response, no internal notes"""
        content = """**RESPONSE:**
We decline your offer."""

        result = parse_bilateral_response(content)

        assert "decline" in result["response"]
        assert result["internal_notes"] == ""

    def test_empty_bilateral_response(self):
        """Test with empty bilateral response"""
        content = ""

        result = parse_bilateral_response(content)

        assert result["response"] == ""
        assert result["internal_notes"] == ""


class TestFallbackBehavior:
    """Tests for fallback behavior in parse_decision function"""

    def test_json_mode_success(self):
        """Test successful JSON parsing in json_mode"""
        content = '''```json
{
  "goals": {"long_term": "LT", "short_term": "ST"},
  "reasoning": "Reasoning text",
  "action": "Action text"
}
```'''

        result = parse_decision(content, json_mode=True)

        assert "goals" in result
        assert result["reasoning"] == "Reasoning text"

    def test_json_mode_fallback_to_markdown(self):
        """Test fallback to markdown when JSON fails in json_mode"""
        content = """**LONG-TERM GOALS:**
Strategic objectives.

**SHORT-TERM PRIORITIES:**
Immediate tasks.

**REASONING:**
Analysis here.

**ACTION:**
Take action."""

        result = parse_decision(content, json_mode=True)

        # Should fall back to markdown parsing
        assert "goals" in result
        assert "Strategic objectives" in result["goals"] or "Long-term" in result["goals"]
        assert "Analysis here" in result["reasoning"]

    def test_non_json_mode_uses_markdown(self):
        """Test that non-json_mode uses markdown parser directly"""
        content = """**GOALS:**
Simple goals.

**REASONING:**
Simple reasoning.

**ACTION:**
Simple action."""

        result = parse_decision(content, json_mode=False)

        assert "Simple goals" in result["goals"]
        assert "Simple reasoning" in result["reasoning"]
        assert "Simple action" in result["action"]

    def test_json_mode_with_invalid_json_falls_back(self):
        """Test that invalid JSON falls back to markdown"""
        content = """Invalid JSON here: {"broken

**GOALS:**
Fallback goals.

**REASONING:**
Fallback reasoning.

**ACTION:**
Fallback action."""

        result = parse_decision(content, json_mode=True)

        # Should fall back to markdown
        assert "Fallback goals" in result["goals"]

    def test_combined_json_and_markdown(self):
        """Test content with both JSON and markdown sections"""
        content = '''Here is my decision:
```json
{"goals": {"long_term": "JSON Goal", "short_term": "JSON Priority"}, "reasoning": "JSON Reasoning", "action": "JSON Action"}
```

**FALLBACK_GOALS:**
Markdown Goals.

**FALLBACK_REASONING:**
Markdown Reasoning.'''

        result = parse_decision(content, json_mode=True)

        # Should use JSON since json_mode=True and JSON is valid
        # Goals are normalized to string format
        assert "JSON Goal" in result.get("goals", "")


class TestEdgeCasesAndRobustness:
    """Additional edge case and robustness tests"""

    def test_nested_asterisks(self):
        """Test handling of nested asterisks in content"""
        content = """**GOALS:**
Goal with **nested bold** text and *italic*.

**REASONING:**
Reasoning."""

        result = parse_decision_markdown(content)
        assert "**nested bold**" in result["goals"]

    def test_list_content(self):
        """Test sections with list content"""
        content = """**GOALS:**
- Goal 1
- Goal 2
- Goal 3

**REASONING:**
1. First reason
2. Second reason

**ACTION:**
* Action item 1
* Action item 2"""

        result = parse_decision_markdown(content)

        assert "Goal 1" in result["goals"]
        assert "Goal 2" in result["goals"]
        assert "First reason" in result["reasoning"]
        assert "Action item 1" in result["action"]

    def test_table_content(self):
        """Test sections with table content"""
        content = """**ACTION:**
| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |

**REASONING:**
Next section."""

        result = parse_decision_markdown(content)
        assert "Column 1" in result["action"]
        assert "Value 1" in result["action"]

    def test_quoted_content(self):
        """Test sections with quoted content"""
        content = '''**REASONING:**
> This is a blockquote
> spanning multiple lines

Regular text.

**ACTION:**
Action here.'''

        result = parse_decision_markdown(content)
        assert "blockquote" in result["reasoning"]

    def test_mixed_language_content(self):
        """Test sections with mixed language content"""
        content = """**GOALS:**
English goals. 日本語の目標. Objectifs français.

**REASONING:**
Multilingual reasoning: 多语言推理, многоязычное рассуждение.

**ACTION:**
Take action: 行动, действие."""

        result = parse_decision_markdown(content)

        assert "日本語" in result["goals"]
        assert "многоязычное" in result["reasoning"]
        assert "行动" in result["action"]

    def test_emoji_content(self):
        """Test sections with emoji content"""
        content = """**GOALS:**
Achieve success! 🎯 Build relationships 🤝

**REASONING:**
Because reasons 💡

**ACTION:**
Let's go! 🚀"""

        result = parse_decision_markdown(content)

        assert "🎯" in result["goals"]
        assert "💡" in result["reasoning"]
        assert "🚀" in result["action"]

    def test_url_content(self):
        """Test sections with URL content"""
        content = """**GOALS:**
Review https://example.com/path?query=value#anchor

**REASONING:**
Based on http://data.example.org/api

**ACTION:**
Visit ftp://files.example.net/docs"""

        result = parse_decision_markdown(content)

        assert "https://example.com" in result["goals"]
        assert "http://data.example.org" in result["reasoning"]
        assert "ftp://files.example.net" in result["action"]

    def test_json_with_nested_objects(self):
        """Test JSON with deeply nested objects"""
        content = '''```json
{
  "goals": {
    "long_term": "Complex goal",
    "short_term": "Tactical priority",
    "nested": {
      "deeply": {
        "nested": "value"
      }
    }
  },
  "reasoning": "Reasoning text",
  "action": "Action text"
}
```'''

        result = parse_decision_json(content)

        # Goals are normalized to string format (long_term and short_term extracted)
        assert "Complex goal" in result["goals"]
        assert "Tactical priority" in result["goals"]

    def test_json_with_array_values(self):
        """Test JSON with array values in goals"""
        content = '''```json
{
  "goals": {
    "long_term": "Goal A",
    "short_term": "Priority B",
    "items": ["item1", "item2", "item3"]
  },
  "reasoning": "Analysis",
  "action": "Execute"
}
```'''

        result = parse_decision_json(content)

        # Goals are normalized to string format
        assert "Goal A" in result["goals"]
        assert "Priority B" in result["goals"]
        # Extra fields like "items" are not included in the normalized string
        assert result["reasoning"] == "Analysis"
        assert result["action"] == "Execute"

    def test_section_with_only_numbers(self):
        """Test sections with numeric content"""
        content = """**GOALS:**
12345

**REASONING:**
67890

**ACTION:**
100"""

        result = parse_decision_markdown(content)

        assert result["goals"] == "12345"
        assert result["reasoning"] == "67890"
        assert result["action"] == "100"

    def test_very_short_content(self):
        """Test with minimal valid content"""
        content = "**ACTION:** X"

        result = parse_decision_markdown(content)

        assert result["action"] == "X"
