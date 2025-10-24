"""
Tests for markdown_utils module - Markdown cleaning and validation
"""
import unittest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from markdown_utils import remove_duplicate_sections, clean_markdown_formatting, validate_markdown_structure


class TestRemoveDuplicateSections(unittest.TestCase):
    """Test remove_duplicate_sections function"""

    def test_no_duplicates(self):
        """Test that clean markdown is unchanged"""
        content = """# Actor - Turn 1

## Current Goals
Some goals here

## Reasoning
Some reasoning here

## Action
Some action here
"""
        result = remove_duplicate_sections(content)
        # Should have all three sections
        self.assertIn("## Current Goals", result)
        self.assertIn("## Reasoning", result)
        self.assertIn("## Action", result)
        # Count occurrences
        self.assertEqual(result.count("## Current Goals"), 1)
        self.assertEqual(result.count("## Reasoning"), 1)
        self.assertEqual(result.count("## Action"), 1)

    def test_duplicate_goals_removed(self):
        """Test that duplicate Goals section is removed"""
        content = """# Actor - Turn 1

## Current Goals
First occurrence

## Current Goals
Second occurrence (duplicate)

## Reasoning
Some reasoning
"""
        result = remove_duplicate_sections(content)
        # Should only have one Goals section
        self.assertEqual(result.count("## Current Goals"), 1)
        self.assertIn("First occurrence", result)
        self.assertNotIn("Second occurrence (duplicate)", result)

    def test_duplicate_reasoning_removed(self):
        """Test that duplicate Reasoning section is removed"""
        content = """# Actor - Turn 1

## Reasoning
First reasoning

## Action
Some action

## Reasoning
Duplicate reasoning
"""
        result = remove_duplicate_sections(content)
        self.assertEqual(result.count("## Reasoning"), 1)
        self.assertIn("First reasoning", result)
        self.assertNotIn("Duplicate reasoning", result)

    def test_duplicate_action_removed(self):
        """Test that duplicate Action section is removed"""
        content = """# Actor - Turn 1

## Action
First action

## Action
Duplicate action
"""
        result = remove_duplicate_sections(content)
        self.assertEqual(result.count("## Action"), 1)
        self.assertIn("First action", result)
        self.assertNotIn("Duplicate action", result)

    def test_case_insensitive_ACTION(self):
        """Test that different case variations are treated as same section"""
        content = """# Actor - Turn 1

## ACTION
First action

## Action
Second action (different case)
"""
        result = remove_duplicate_sections(content)
        # Should normalize and keep only first occurrence
        self.assertEqual(result.count("## Action"), 1)
        self.assertIn("First action", result)

    def test_multiple_duplicates(self):
        """Test removing multiple types of duplicate sections"""
        content = """# Actor - Turn 1

## Current Goals
Goals 1

## Reasoning
Reasoning 1

## Current Goals
Goals 2 (duplicate)

## Action
Action 1

## Reasoning
Reasoning 2 (duplicate)
"""
        result = remove_duplicate_sections(content)
        self.assertEqual(result.count("## Current Goals"), 1)
        self.assertEqual(result.count("## Reasoning"), 1)
        self.assertEqual(result.count("## Action"), 1)


class TestCleanMarkdownFormatting(unittest.TestCase):
    """Test clean_markdown_formatting function"""

    def test_removes_duplicates(self):
        """Test that cleaning removes duplicate sections"""
        content = """# Actor - Turn 1

## Current Goals
Goals

## Current Goals
Duplicate goals
"""
        result = clean_markdown_formatting(content)
        self.assertEqual(result.count("## Current Goals"), 1)

    def test_normalizes_headers(self):
        """Test that ALL CAPS headers are normalized"""
        content = """# Actor - Turn 1

## CURRENT GOALS
Some goals

## REASONING
Some reasoning

## ACTION
Some action
"""
        result = clean_markdown_formatting(content)
        self.assertIn("## Current Goals", result)
        self.assertIn("## Reasoning", result)
        self.assertIn("## Action", result)
        self.assertNotIn("## CURRENT GOALS", result)
        self.assertNotIn("## REASONING", result)
        self.assertNotIn("## ACTION", result)

    def test_removes_excessive_blank_lines(self):
        """Test that excessive blank lines are reduced"""
        content = """# Actor - Turn 1



## Current Goals


Some goals



## Reasoning
"""
        result = clean_markdown_formatting(content)
        # Should not have 4+ consecutive newlines
        self.assertNotIn("\n\n\n\n", result)

    def test_ends_with_single_newline(self):
        """Test that result ends with single newline"""
        content = """# Actor - Turn 1

## Current Goals
Some content"""
        result = clean_markdown_formatting(content)
        self.assertTrue(result.endswith("\n"))
        self.assertFalse(result.endswith("\n\n"))

    def test_handles_empty_content(self):
        """Test handling of empty or whitespace-only content"""
        result = clean_markdown_formatting("")
        self.assertEqual(result, "\n")

        result = clean_markdown_formatting("   \n  \n  ")
        self.assertEqual(result, "\n")


class TestValidateMarkdownStructure(unittest.TestCase):
    """Test validate_markdown_structure function"""

    def test_valid_complete_structure(self):
        """Test validation of complete valid markdown"""
        content = """# Actor Name - Turn 1

**Scenario:** Test Scenario

**Turn Duration:** 1 month

## Current Goals
Some goals

## Reasoning
Some reasoning

## Action
Some action
"""
        is_valid, issues = validate_markdown_structure(content)
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)

    def test_missing_header(self):
        """Test detection of missing header"""
        content = """
**Scenario:** Test Scenario

## Reasoning
Some reasoning
"""
        is_valid, issues = validate_markdown_structure(content)
        self.assertFalse(is_valid)
        self.assertTrue(any("header" in issue.lower() for issue in issues))

    def test_missing_scenario(self):
        """Test detection of missing scenario name"""
        content = """# Actor Name - Turn 1

**Turn Duration:** 1 month

## Reasoning
Some reasoning
"""
        is_valid, issues = validate_markdown_structure(content)
        self.assertFalse(is_valid)
        self.assertTrue(any("scenario" in issue.lower() for issue in issues))

    def test_missing_turn_duration(self):
        """Test detection of missing turn duration"""
        content = """# Actor Name - Turn 1

**Scenario:** Test Scenario

## Reasoning
Some reasoning
"""
        is_valid, issues = validate_markdown_structure(content)
        self.assertFalse(is_valid)
        self.assertTrue(any("turn duration" in issue.lower() for issue in issues))

    def test_missing_reasoning_and_action(self):
        """Test detection when both reasoning and action missing"""
        content = """# Actor Name - Turn 1

**Scenario:** Test Scenario

**Turn Duration:** 1 month

## Current Goals
Some goals
"""
        is_valid, issues = validate_markdown_structure(content)
        self.assertFalse(is_valid)
        self.assertTrue(any("reasoning" in issue.lower() and "action" in issue.lower() for issue in issues))

    def test_valid_with_only_reasoning(self):
        """Test that markdown with only reasoning is valid"""
        content = """# Actor Name - Turn 1

**Scenario:** Test Scenario

**Turn Duration:** 1 month

## Reasoning
Some reasoning
"""
        is_valid, issues = validate_markdown_structure(content)
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)

    def test_valid_with_only_action(self):
        """Test that markdown with only action is valid"""
        content = """# Actor Name - Turn 1

**Scenario:** Test Scenario

**Turn Duration:** 1 month

## Action
Some action
"""
        is_valid, issues = validate_markdown_structure(content)
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)

    def test_multiple_issues_detected(self):
        """Test that multiple issues are all detected"""
        content = """Some content without proper structure"""
        is_valid, issues = validate_markdown_structure(content)
        self.assertFalse(is_valid)
        self.assertGreater(len(issues), 1)


if __name__ == '__main__':
    unittest.main()
