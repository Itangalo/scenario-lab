"""
Scenario-specific methods for Sverige och AI 2030.

NOTE: This scenario now uses the World Interpreter (execution_mode: "narrative").
The action functions below are NO LONGER USED. They are kept for reference and
for backward compatibility if you switch to legacy mode.

In narrative mode:
- Actors describe their intentions in natural language
- The World Interpreter translates narratives into metric changes
- Generic primitives (adjust_metric, set_metric_direct) handle all mechanics
- Bounds, magnitudes, and dependencies are defined in metrics.yaml

To switch back to legacy mode:
1. Set execution_mode: "legacy" in scenario.yaml
2. The action functions below will be used again
"""
from typing import List
from scenario_lab.methods_base import ScenarioMethods
from scenario_lab.models import WorldState


class SverigeAI2030Methods(ScenarioMethods):
    """
    Methods for Sverige och AI 2030 scenario.

    This class is kept for backward compatibility but is not used
    when execution_mode is set to "narrative".
    """

    def _register_actions(self) -> None:
        """
        Register actions for legacy mode.

        These are NOT used in narrative mode (current setting).
        The World Interpreter handles all action interpretation.
        """
        # Government actions
        self.register_action("invest_ai_adoption", self.invest_ai_adoption)
        self.register_action("propose_regulation", self.propose_regulation)
        self.register_action("launch_ai_commission", self.launch_ai_commission)
        self.register_action("lobby_eu", self.lobby_eu)

        # Labor union actions
        self.register_action("negotiate_with_business", self.negotiate_with_business)
        self.register_action("public_campaign", self.public_campaign)
        self.register_action("threaten_strike", self.threaten_strike)
        self.register_action("propose_retraining", self.propose_retraining)

        # Media actions
        self.register_action("publish_investigation", self.publish_investigation)
        self.register_action("shape_sentiment", self.shape_sentiment)
        self.register_action("build_expertise", self.build_expertise)

        # Business sector actions
        self.register_action("accelerate_ai_adoption", self.accelerate_ai_adoption)
        self.register_action("lobby_government", self.lobby_government)
        self.register_action("invest_in_safety", self.invest_in_safety)
        self.register_action("cut_workforce", self.cut_workforce)

    # =========== LEGACY MODE ACTIONS (NOT USED IN NARRATIVE MODE) ===========

    # The functions below are preserved for reference but are not called
    # when using the World Interpreter (narrative mode).

    # Instead, the World Interpreter:
    # 1. Receives free-form narrative from actors
    # 2. Translates it into metric changes using LLM
    # 3. Applies changes via generic primitives
    # 4. Respects bounds and dependencies defined in metrics.yaml

    def invest_ai_adoption(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def propose_regulation(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def launch_ai_commission(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def lobby_eu(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def negotiate_with_business(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def public_campaign(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def threaten_strike(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def propose_retraining(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def publish_investigation(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def shape_sentiment(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def build_expertise(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def accelerate_ai_adoption(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def lobby_government(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def invest_in_safety(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]

    def cut_workforce(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Legacy action - not used in narrative mode."""
        return ["This action is not used in narrative mode"]
