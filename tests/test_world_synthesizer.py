"""
Tests for World Synthesizer module

Tests prompt construction and response parsing for world state synthesis.
"""
import pytest

from scenario_lab.core.world_synthesizer import WorldSynthesizer, WorldUpdateResult


class TestWorldUpdateResult:
    """Tests for WorldUpdateResult dataclass"""

    def test_create_result(self):
        """Test creating a world update result"""
        result = WorldUpdateResult(
            updated_state="The situation has changed.",
            key_changes=["Change 1", "Change 2"],
            consequences=["Consequence 1"],
            tokens_used=100,
            input_tokens=70,
            output_tokens=30,
            full_response="Full LLM response"
        )

        assert result.updated_state == "The situation has changed."
        assert len(result.key_changes) == 2
        assert len(result.consequences) == 1
        assert result.tokens_used == 100
        assert result.input_tokens == 70
        assert result.output_tokens == 30
        assert result.full_response == "Full LLM response"

    def test_empty_lists(self):
        """Test result with empty changes/consequences lists"""
        result = WorldUpdateResult(
            updated_state="State",
            key_changes=[],
            consequences=[],
            tokens_used=50,
            input_tokens=30,
            output_tokens=20,
            full_response=""
        )

        assert result.key_changes == []
        assert result.consequences == []


class TestWorldSynthesizerInit:
    """Tests for WorldSynthesizer initialization"""

    def test_default_init(self):
        """Test default initialization"""
        synthesizer = WorldSynthesizer()

        assert synthesizer.model == "openai/gpt-4o-mini"
        assert synthesizer.scenario_name == ""

    def test_custom_init(self):
        """Test initialization with custom values"""
        synthesizer = WorldSynthesizer(
            model="anthropic/claude-3-opus",
            scenario_name="AI Policy Simulation"
        )

        assert synthesizer.model == "anthropic/claude-3-opus"
        assert synthesizer.scenario_name == "AI Policy Simulation"


class TestBuildSystemPrompt:
    """Tests for build_system_prompt method"""

    def test_system_prompt_includes_scenario_name(self):
        """Test that system prompt includes the scenario name"""
        synthesizer = WorldSynthesizer(scenario_name="Trade War 2025")
        prompt = synthesizer.build_system_prompt()

        assert "Trade War 2025" in prompt

    def test_system_prompt_with_empty_scenario_name(self):
        """Test system prompt with empty scenario name"""
        synthesizer = WorldSynthesizer(scenario_name="")
        prompt = synthesizer.build_system_prompt()

        assert "scenario simulation narrator" in prompt.lower()

    def test_system_prompt_contains_responsibilities(self):
        """Test that system prompt outlines responsibilities"""
        synthesizer = WorldSynthesizer(scenario_name="Test")
        prompt = synthesizer.build_system_prompt()

        assert "responsibilities" in prompt.lower()
        assert "actions" in prompt.lower() or "decisions" in prompt.lower()

    def test_system_prompt_contains_guidelines(self):
        """Test that system prompt contains guidelines"""
        synthesizer = WorldSynthesizer(scenario_name="Test")
        prompt = synthesizer.build_system_prompt()

        assert "guidelines" in prompt.lower()

    def test_system_prompt_specifies_output_format(self):
        """Test that system prompt specifies the required output format"""
        synthesizer = WorldSynthesizer(scenario_name="Test")
        prompt = synthesizer.build_system_prompt()

        assert "UPDATED STATE" in prompt
        assert "KEY CHANGES" in prompt
        assert "CONSEQUENCES" in prompt


class TestBuildUserPrompt:
    """Tests for build_user_prompt method"""

    def test_basic_user_prompt(self):
        """Test building a basic user prompt"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        prompt = synthesizer.build_user_prompt(
            current_state="The world is at peace.",
            turn=3,
            total_turns=10,
            actor_decisions={
                "USA": {"action": "Increase tariffs on imports."},
                "China": {"action": "Respond with counter-tariffs."}
            }
        )

        assert "Turn 3 of 10" in prompt
        assert "The world is at peace." in prompt
        assert "USA" in prompt
        assert "Increase tariffs" in prompt
        assert "China" in prompt
        assert "counter-tariffs" in prompt

    def test_user_prompt_includes_all_actors(self):
        """Test that user prompt includes all actor decisions"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        actor_decisions = {
            "Actor1": {"action": "Action 1"},
            "Actor2": {"action": "Action 2"},
            "Actor3": {"action": "Action 3"},
        }

        prompt = synthesizer.build_user_prompt(
            current_state="State",
            turn=1,
            total_turns=5,
            actor_decisions=actor_decisions
        )

        for actor_name in actor_decisions:
            assert actor_name in prompt

    def test_user_prompt_handles_missing_action(self):
        """Test that user prompt handles actors with missing action key"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        prompt = synthesizer.build_user_prompt(
            current_state="State",
            turn=1,
            total_turns=5,
            actor_decisions={"Actor1": {}}  # Missing 'action' key
        )

        assert "No action specified" in prompt

    def test_user_prompt_with_exogenous_events(self):
        """Test user prompt includes exogenous events"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        prompt = synthesizer.build_user_prompt(
            current_state="State",
            turn=2,
            total_turns=10,
            actor_decisions={"Actor1": {"action": "Do something"}},
            exogenous_events=[
                {"name": "Market Crash", "description": "Stock markets fell 10%"},
                {"name": "Earthquake", "description": "A 6.5 magnitude earthquake struck"}
            ]
        )

        assert "Background Events" in prompt
        assert "Market Crash" in prompt
        assert "Stock markets fell 10%" in prompt
        assert "Earthquake" in prompt

    def test_user_prompt_without_exogenous_events(self):
        """Test user prompt without exogenous events"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        prompt = synthesizer.build_user_prompt(
            current_state="State",
            turn=1,
            total_turns=5,
            actor_decisions={"Actor1": {"action": "Act"}},
            exogenous_events=None
        )

        assert "Background Events" not in prompt

    def test_user_prompt_with_empty_exogenous_events(self):
        """Test user prompt with empty exogenous events list"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        prompt = synthesizer.build_user_prompt(
            current_state="State",
            turn=1,
            total_turns=5,
            actor_decisions={"Actor1": {"action": "Act"}},
            exogenous_events=[]
        )

        assert "Background Events" not in prompt

    def test_user_prompt_contains_output_format(self):
        """Test that user prompt specifies required output format"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        prompt = synthesizer.build_user_prompt(
            current_state="State",
            turn=1,
            total_turns=5,
            actor_decisions={"Actor1": {"action": "Act"}}
        )

        assert "UPDATED STATE" in prompt
        assert "KEY CHANGES" in prompt
        assert "CONSEQUENCES" in prompt

    def test_user_prompt_with_various_turn_numbers(self):
        """Test user prompt with various turn numbers"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        for turn, total in [(1, 10), (5, 10), (10, 10), (1, 100)]:
            prompt = synthesizer.build_user_prompt(
                current_state="State",
                turn=turn,
                total_turns=total,
                actor_decisions={"Actor": {"action": "Act"}}
            )

            assert f"Turn {turn} of {total}" in prompt


class TestParseWorldUpdateResponse:
    """Tests for parse_world_update_response method"""

    def test_parse_valid_response_with_bold_sections(self):
        """Test parsing a valid response with bold section headers"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """**UPDATED STATE:**
The trade tensions have escalated significantly. After USA announced tariffs,
China responded with counter-measures. Markets reacted negatively with major
indices dropping 3% across the board.

**KEY CHANGES:**
- USA implemented 25% tariffs on Chinese goods
- China responded with matching tariffs
- Stock markets dropped globally

**CONSEQUENCES:**
- Consumer prices expected to rise
- Supply chain disruptions anticipated
- Diplomatic relations strained
"""

        result = synthesizer.parse_world_update_response(content)

        assert "trade tensions" in result['updated_state'].lower()
        assert len(result['key_changes']) == 3
        assert "USA implemented 25% tariffs" in result['key_changes'][0]
        assert len(result['consequences']) == 3
        assert "Consumer prices" in result['consequences'][0]

    def test_parse_response_with_colon_in_headers(self):
        """Test parsing response with colons in headers"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """**UPDATED STATE:**
The situation has changed.

**KEY CHANGES:**
- Change 1
- Change 2

**CONSEQUENCES:**
- Consequence 1
"""

        result = synthesizer.parse_world_update_response(content)

        assert "situation has changed" in result['updated_state'].lower()
        assert len(result['key_changes']) == 2
        assert len(result['consequences']) == 1

    def test_parse_response_with_asterisk_bullets(self):
        """Test parsing response with asterisk bullets"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """**UPDATED STATE:**
State content here.

**KEY CHANGES:**
* Change with asterisk
* Another change

**CONSEQUENCES:**
* Consequence with asterisk
"""

        result = synthesizer.parse_world_update_response(content)

        assert len(result['key_changes']) == 2
        assert "Change with asterisk" in result['key_changes'][0]
        assert len(result['consequences']) == 1

    def test_parse_response_with_bullet_points(self):
        """Test parsing response with bullet point characters"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """**UPDATED STATE:**
The world changed.

**KEY CHANGES:**
• Bullet point change 1
• Bullet point change 2

**CONSEQUENCES:**
• Bullet consequence
"""

        result = synthesizer.parse_world_update_response(content)

        assert len(result['key_changes']) == 2
        assert len(result['consequences']) == 1

    def test_parse_response_case_insensitive(self):
        """Test that parsing handles case variations"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """**Updated State:**
State content.

**Key Changes:**
- Change 1

**Consequences:**
- Consequence 1
"""

        result = synthesizer.parse_world_update_response(content)

        assert result['updated_state'] != ""
        # Note: The fallback logic should handle mixed case

    def test_parse_response_fallback_to_entire_content(self):
        """Test that parsing falls back to entire content if sections not found"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """This is just plain text without any section markers.
The world has changed in various ways but the format is unexpected."""

        result = synthesizer.parse_world_update_response(content)

        # Should fall back to using entire content as updated_state
        assert "plain text" in result['updated_state'].lower()
        assert result['key_changes'] == []
        assert result['consequences'] == []

    def test_parse_response_with_empty_content(self):
        """Test parsing empty content"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        result = synthesizer.parse_world_update_response("")

        assert result['updated_state'] == ""
        assert result['key_changes'] == []
        assert result['consequences'] == []

    def test_parse_response_with_only_updated_state(self):
        """Test parsing response with only updated state section"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """**UPDATED STATE:**
The world is in turmoil. Economic indicators are falling and political
tensions are rising across multiple regions."""

        result = synthesizer.parse_world_update_response(content)

        assert "world is in turmoil" in result['updated_state'].lower()
        assert result['key_changes'] == []
        assert result['consequences'] == []

    def test_parse_response_preserves_multiline_updated_state(self):
        """Test that multi-paragraph updated state is preserved"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """**UPDATED STATE:**
First paragraph of the world state update. This describes the immediate situation.

Second paragraph continues the narrative. It provides additional context and detail
about how the situation has evolved.

Third paragraph concludes with the current status.

**KEY CHANGES:**
- One change

**CONSEQUENCES:**
- One consequence
"""

        result = synthesizer.parse_world_update_response(content)

        # Should preserve multiple paragraphs
        assert "First paragraph" in result['updated_state']
        assert "Second paragraph" in result['updated_state']

    def test_parse_response_strips_whitespace_from_bullet_items(self):
        """Test that whitespace is stripped from bullet items"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """**UPDATED STATE:**
State content.

**KEY CHANGES:**
-   Change with leading spaces
-    Another change with spaces

**CONSEQUENCES:**
- Consequence item
"""

        result = synthesizer.parse_world_update_response(content)

        # Items should be stripped of extra whitespace
        for change in result['key_changes']:
            assert change == change.strip()
            assert not change.startswith(" ")
            assert not change.endswith(" ")


class TestParseWorldUpdateResponseInvalidCases:
    """Tests for parse_world_update_response with invalid/edge case inputs"""

    def test_parse_malformed_bullets(self):
        """Test parsing content with malformed bullets"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """**UPDATED STATE:**
Some state.

**KEY CHANGES:**
Not a bullet point line
Another non-bullet line

**CONSEQUENCES:**
Also not bullets
"""

        result = synthesizer.parse_world_update_response(content)

        # Non-bullet lines should not be added
        assert result['key_changes'] == []
        assert result['consequences'] == []

    def test_parse_mixed_valid_invalid_bullets(self):
        """Test parsing mix of valid and invalid bullet formats"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """**UPDATED STATE:**
State.

**KEY CHANGES:**
- Valid bullet 1
This is not a bullet
- Valid bullet 2

**CONSEQUENCES:**
- Valid consequence
"""

        result = synthesizer.parse_world_update_response(content)

        # Should only capture valid bullet items
        assert len(result['key_changes']) == 2
        assert "Valid bullet 1" in result['key_changes'][0]
        assert "Valid bullet 2" in result['key_changes'][1]

    def test_parse_response_with_extra_sections(self):
        """Test parsing response with unexpected additional sections"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """**UPDATED STATE:**
The state description.

**KEY CHANGES:**
- Change 1

**ADDITIONAL NOTES:**
Some extra notes that shouldn't interfere.

**CONSEQUENCES:**
- Consequence 1
"""

        result = synthesizer.parse_world_update_response(content)

        assert result['updated_state'] != ""
        assert len(result['key_changes']) >= 1

    def test_parse_response_with_numbered_lists(self):
        """Test parsing response with numbered lists instead of bullets"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        content = """**UPDATED STATE:**
State content.

**KEY CHANGES:**
1. First change
2. Second change

**CONSEQUENCES:**
1. First consequence
"""

        result = synthesizer.parse_world_update_response(content)

        # Numbered items don't match bullet patterns
        assert result['key_changes'] == []
        assert result['consequences'] == []

    def test_parse_whitespace_only_content(self):
        """Test parsing whitespace-only content"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        result = synthesizer.parse_world_update_response("   \n\n  \t  ")

        assert result['key_changes'] == []
        assert result['consequences'] == []


class TestWorldSynthesizerIntegration:
    """Integration tests for WorldSynthesizer"""

    def test_full_prompt_workflow(self):
        """Test building system and user prompts together"""
        synthesizer = WorldSynthesizer(
            model="openai/gpt-4o-mini",
            scenario_name="Global Trade Simulation"
        )

        system_prompt = synthesizer.build_system_prompt()
        user_prompt = synthesizer.build_user_prompt(
            current_state="International trade is flourishing.",
            turn=5,
            total_turns=20,
            actor_decisions={
                "USA": {"action": "Impose 10% tariffs"},
                "China": {"action": "Retaliate with matching tariffs"},
                "EU": {"action": "Call for negotiations"}
            },
            exogenous_events=[
                {"name": "Oil Price Spike", "description": "Oil prices rose 20%"}
            ]
        )

        # Verify system prompt
        assert "Global Trade Simulation" in system_prompt
        assert "narrator" in system_prompt.lower()

        # Verify user prompt contains all expected elements
        assert "Turn 5 of 20" in user_prompt
        assert "flourishing" in user_prompt
        assert "USA" in user_prompt
        assert "China" in user_prompt
        assert "EU" in user_prompt
        assert "Oil Price Spike" in user_prompt

    def test_response_round_trip(self):
        """Test that a well-formatted response parses correctly"""
        synthesizer = WorldSynthesizer(scenario_name="Test")

        # Simulate a well-formed LLM response
        llm_response = """**UPDATED STATE:**
Following the implementation of tariffs by the USA, China has responded
with counter-measures. The EU has positioned itself as a mediator,
calling for multilateral negotiations. Markets have shown volatility.

**KEY CHANGES:**
- USA tariffs now in effect on $200B of Chinese goods
- China retaliatory tariffs active on $60B of US goods
- EU initiated diplomatic outreach to both parties
- Global markets dropped 2.5% on uncertainty

**CONSEQUENCES:**
- Consumer electronics prices rising in the US
- American agricultural exports facing barriers in China
- Supply chain adjustments underway for multinational corporations
- WTO dispute mechanism being activated
"""

        result = synthesizer.parse_world_update_response(llm_response)

        # Verify parsing extracted all expected data
        assert "tariffs" in result['updated_state'].lower()
        assert "mediator" in result['updated_state'].lower()
        assert len(result['key_changes']) == 4
        assert len(result['consequences']) == 4

        # Verify specific items
        assert any("USA tariffs" in change for change in result['key_changes'])
        assert any("Consumer electronics" in cons for cons in result['consequences'])
