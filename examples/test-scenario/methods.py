"""
Scenario-specific methods for the AI Governance test scenario.

Defines custom actions and validation logic for the test scenario.
"""

from typing import List
from scenario_lab.methods_base import ScenarioMethods
from scenario_lab.models import WorldState


class TestScenarioMethods(ScenarioMethods):
    """
    Methods and actions for the AI Governance test scenario.

    Demonstrates basic scenario action implementation.
    """

    def _register_actions(self) -> None:
        """Register all available actions for this scenario."""
        self.register_action("invest_research", self.invest_research)
        self.register_action("sign_agreement", self.sign_agreement)
        self.register_action("increase_risk_assessment", self.increase_risk_assessment)

    def invest_research(
        self,
        actor: str,
        args: dict,
        state: WorldState
    ) -> List[str]:
        """
        Action: Invest in AI research capability.

        Args:
            actor: Actor performing the action
            args: Action arguments (should contain 'amount' key)
            state: Current world state

        Returns:
            List of interpretation strings for the Director
        """
        amount = args.get("amount", 10)

        # Update actor's research capacity
        self.modify_metric(
            state,
            f"actors.{actor}.private.ai_research_capacity",
            amount
        )

        interpretation = f"{actor} invests {amount} units in AI research, increasing their research capacity."

        return [interpretation]

    def sign_agreement(
        self,
        actor: str,
        args: dict,
        state: WorldState
    ) -> List[str]:
        """
        Action: Sign a cooperation agreement with another actor.

        Args:
            actor: Actor performing the action
            args: Action arguments (should contain 'other_actor' key)
            state: Current world state

        Returns:
            List of interpretation strings for the Director
        """
        other_actor = args.get("other_actor", "unknown")

        # Update relationship trust
        relationship = self.get_relationship(state, actor, other_actor)
        relationship.trust = min(1.0, relationship.trust + 0.1)

        # Add agreement to active agreements
        agreement_name = f"{actor}-{other_actor} AI Safety Accord"
        if agreement_name not in relationship.active_agreements:
            relationship.active_agreements.append(agreement_name)

        # Update world cooperation metric
        self.modify_metric(state, "world.international_cooperation", 0.05)

        # Add fact
        self.add_fact(
            state,
            turn=0,  # TODO: Get actual turn number
            fact=f"{actor} and {other_actor} signed AI Safety Accord",
            source=f"action:sign_agreement"
        )

        interpretation = (
            f"{actor} and {other_actor} sign an AI Safety Accord, "
            f"strengthening their cooperation and mutual trust."
        )

        return [interpretation]

    def increase_risk_assessment(
        self,
        actor: str,
        args: dict,
        state: WorldState
    ) -> List[str]:
        """
        Action: Increase catastrophic risk assessment (e.g., public warning).

        Args:
            actor: Actor performing the action
            args: Action arguments (should contain 'risk_increase' key)
            state: Current world state

        Returns:
            List of interpretation strings for the Director
        """
        risk_increase = args.get("risk_increase", 0.05)

        # Increase global catastrophic risk
        self.modify_metric(
            state,
            "world.catastrophic_risk_level",
            risk_increase
        )

        # Set outcome flag
        self.set_outcome_flag(
            state,
            "risk_warning_issued",
            True
        )

        interpretation = (
            f"{actor} issues a public warning about AI catastrophic risks, "
            f"increasing global risk assessment by {risk_increase}."
        )

        return [interpretation]
