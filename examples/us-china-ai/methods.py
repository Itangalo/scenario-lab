"""
Scenario-specific methods for the US-China AI Race.
"""
from typing import List
from scenario_lab.methods_base import ScenarioMethods
from scenario_lab.models import WorldState


class USChinaAIRaceMethods(ScenarioMethods):
    """
    Methods and actions for the US-China AI Race scenario.
    """

    def _register_actions(self) -> None:
        """Register all available actions for this scenario."""
        self.register_action("invest_ai_research", self.invest_ai_research)
        self.register_action("invest_research", self.invest_ai_research)  # Alias for MockProvider-kompatibilitet
        self.register_action("invest_ai_safety", self.invest_ai_safety)
        self.register_action("impose_sanctions", self.impose_sanctions)
        self.register_action("form_alliance", self.form_alliance)
        self.register_action("propose_treaty", self.propose_treaty)
        self.register_action("military_posturing", self.military_posturing)
        self.register_action("public_announcement", self.public_announcement)

    def invest_ai_research(self, actor: str, args: dict, state: WorldState) -> List[str]:
        amount = args.get("amount", 10)
        state.set_metric(actor, "budget", state.get_metric(actor, "budget") - amount)
        
        # Diminishing returns
        current_capability = state.get_metric(actor, "private.ai_capability")
        gain = amount * (1 - (current_capability / 200))
        state.set_metric(actor, "private.ai_capability", current_capability + gain)

        # High capability + low safety = risk
        ai_safety = state.get_metric(actor, "private.ai_safety_research")
        if current_capability > 100 and ai_safety < 60:
            state.set_metric(None, "ai_catastrophe_risk", state.get_metric(None, "ai_catastrophe_risk") + 0.05)

        return [f"{actor} invests {amount} in AI research, boosting their AI capability."]

    def invest_ai_safety(self, actor: str, args: dict, state: WorldState) -> List[str]:
        amount = args.get("amount", 10)
        state.set_metric(actor, "budget", state.get_metric(actor, "budget") - amount)
        state.set_metric(actor, "private.ai_safety_research", state.get_metric(actor, "private.ai_safety_research") + amount)
        return [f"{actor} invests {amount} in AI safety research."]

    def impose_sanctions(self, actor: str, args: dict, state: WorldState) -> List[str]:
        target = args.get("target_actor")
        if not target:
            return ["No target specified for sanctions."]
        
        state.set_metric(target, "budget", state.get_metric(target, "budget") * 0.9) # 10% budget reduction
        state.get_relationship(actor, target).trust -= 0.2
        return [f"{actor} imposes sanctions on {target}, hurting their economy and souring relations."]

    def form_alliance(self, actor: str, args: dict, state: WorldState) -> List[str]:
        target = args.get("target_actor")
        if not target:
            return ["No target specified for alliance."]

        state.get_relationship(actor, target).trust += 0.2
        state.add_fact(f"{actor} and {target} formed a new strategic alliance.", source=f"action:form_alliance")
        return [f"{actor} and {target} form a new strategic alliance, increasing their mutual trust."]

    def propose_treaty(self, actor: str, args: dict, state: WorldState) -> List[str]:
        # A real implementation would have a multi-turn negotiation process.
        # This is a simplified one-turn version.
        state.set_metric(None, "global_ai_regulation", state.get_metric(None, "global_ai_regulation") + 0.1)
        state.set_metric(actor, "international_influence", state.get_metric(actor, "international_influence") - 5) # Political capital cost
        return [f"{actor} proposes a global AI treaty, increasing global regulation but spending some political capital."]

    def military_posturing(self, actor: str, args: dict, state: WorldState) -> List[str]:
        target = args.get("target_actor")
        state.set_metric(actor, "military_capacity", state.get_metric(actor, "private.military_capacity") + 5)
        if target:
            state.get_relationship(actor, target).trust -= 0.1
            return [f"{actor} engages in military posturing towards {target}, increasing their military readiness but also raising tensions."]
        return [f"{actor} increases their military readiness through exercises."]

    def public_announcement(self, actor: str, args: dict, state: WorldState) -> List[str]:
        # This action is purely narrative for now.
        announcement = args.get("announcement", "a generic statement.")
        state.add_fact(f"{actor} announced: '{announcement}'", source="action:public_announcement")
        return [f"{actor} made a public announcement: '{announcement}'"]
