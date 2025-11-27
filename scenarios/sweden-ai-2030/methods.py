"""
Scenario-specific methods for Sverige och AI 2030.
"""
from typing import List
from scenario_lab.methods_base import ScenarioMethods
from scenario_lab.models import WorldState


class SverigeAI2030Methods(ScenarioMethods):
    """Methods and actions for Sverige och AI 2030 scenario."""

    def _register_actions(self) -> None:
        """Register all available actions for this scenario."""
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
        
        # MockProvider compatibility
        self.register_action("invest_research", self.invest_ai_adoption)

    # =========== HELPER METHOD ===========
    
    def _add_to_metric(self, state: WorldState, actor, path: str, delta: float) -> None:
        """Helper to increment/decrement a metric."""
        current = state.get_metric(actor, path)
        state.set_metric(actor, path, current + delta)

    # =========== GOVERNMENT ACTIONS ===========

    def invest_ai_adoption(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Government invests in pushing AI adoption across Swedish industry."""
        amount = args.get("amount", 2)
        budget = state.get_metric(actor, "public.budget_billion_sek")

        if budget < amount:
            return [f"Regeringen saknar budget för att investera {amount} miljarder."]

        state.set_metric(actor, "public.budget_billion_sek", budget - amount)
        self._add_to_metric(state, "business-sector", "public.ai_adoption_rate", 5)
        self._add_to_metric(state, None, "public_sentiment", 3)
        self._add_to_metric(state, actor, "private.ai_adoption_commitment", 10)

        return [
            f"Regeringen investerar {amount} miljarder SEK i AI-adoption.",
            "Svenska företag får incitament att accelerera AI-implementering.",
        ]

    def propose_regulation(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Government proposes new AI regulation."""
        stringency = args.get("stringency", 50)

        eu_pressure = state.get_metric(None, "eu_regulatory_pressure")
        new_pressure = min(100, eu_pressure + stringency / 2)
        state.set_metric(None, "eu_regulatory_pressure", new_pressure)

        if stringency > 70:
            self._add_to_metric(state, "business-sector", "private.regulatory_compliance_burden", 15)
            self._add_to_metric(state, "business-sector", "public.profitability", -5)
            sentiment_shift = -5
        else:
            sentiment_shift = 2

        self._add_to_metric(state, None, "public_sentiment", sentiment_shift)
        self._add_to_metric(state, actor, "private.political_capital", -10)

        return [f"Regeringen föreslår AI-reglering med stringency {stringency}."]

    def launch_ai_commission(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Government launches study commission on AI impacts."""
        self._add_to_metric(state, actor, "private.political_capital", -5)
        self._add_to_metric(state, actor, "public.international_influence", 2)
        return ["Regeringen tillsätter en utredningskommission för AI-påverkan."]

    def lobby_eu(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Government attempts to influence EU AI policy."""
        direction = args.get("direction", "balanced")

        if direction == "acceleration":
            eu_pressure = state.get_metric(None, "eu_regulatory_pressure")
            state.set_metric(None, "eu_regulatory_pressure", max(0, eu_pressure - 10))
            sentiment_shift = 5
        elif direction == "caution":
            eu_pressure = state.get_metric(None, "eu_regulatory_pressure")
            state.set_metric(None, "eu_regulatory_pressure", min(100, eu_pressure + 10))
            sentiment_shift = -2
        else:
            sentiment_shift = 0

        self._add_to_metric(state, actor, "public.international_influence", 5)
        self._add_to_metric(state, None, "public_sentiment", sentiment_shift)
        return [f"Regeringen lobbar EU med {direction} AI-agenda."]

    # =========== LABOR UNION ACTIONS ===========

    def negotiate_with_business(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Labor unions negotiate with business sector."""
        target = "business-sector"

        power = state.get_metric(actor, "private.negotiating_power")
        business_commitment = state.get_metric(target, "private.ai_investment_commitment")

        if power > business_commitment:
            self._add_to_metric(state, actor, "public.member_confidence", 10)
            self._add_to_metric(state, target, "private.labor_satisfaction", 5)
            sentiment_shift = 2
        else:
            self._add_to_metric(state, actor, "public.member_confidence", -5)
            sentiment_shift = -2

        rel = state.get_relationship(actor, target)
        rel.trust += 0.1

        self._add_to_metric(state, None, "public_sentiment", sentiment_shift)
        return [f"Fackföreningarna förhandlar med näringslivet om AI-implementering."]

    def public_campaign(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Labor unions launch public campaign."""
        message = args.get("message", "jobs_protection")

        self._add_to_metric(state, actor, "public.public_support", 8)
        self._add_to_metric(state, actor, "public.member_confidence", 5)

        if message == "fair_share":
            self._add_to_metric(state, None, "public_sentiment", 3)
        elif message == "safety":
            self._add_to_metric(state, None, "public_sentiment", -2)
        else:
            self._add_to_metric(state, None, "public_sentiment", 2)

        return [f"Fackföreningarna startar kampanj för {message}."]

    def threaten_strike(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Labor unions threaten strike action."""
        self._add_to_metric(state, actor, "private.strike_readiness", 15)
        self._add_to_metric(state, "business-sector", "private.labor_satisfaction", -10)
        self._add_to_metric(state, "government", "private.political_capital", -5)

        rel = state.get_relationship(actor, "business-sector")
        rel.trust -= 0.2
        return ["Fackföreningarna hotar stridsåtgärder."]

    def propose_retraining(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Labor unions propose retraining programs."""
        scope = args.get("scope", "modest")

        self._add_to_metric(state, "government", "private.political_capital", -5)
        self._add_to_metric(state, actor, "public.public_support", 5)

        if scope == "ambitious":
            self._add_to_metric(state, "government", "public.budget_billion_sek", -3)
            self._add_to_metric(state, None, "public_sentiment", 5)
        else:
            self._add_to_metric(state, "government", "public.budget_billion_sek", -1)
            self._add_to_metric(state, None, "public_sentiment", 2)

        return [f"Fackföreningarna kräver {scope} omställningsprogram."]

    # =========== MEDIA ACTIONS ===========

    def publish_investigation(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Media publishes investigation into AI impacts."""
        topic = args.get("topic", "jobs")

        self._add_to_metric(state, actor, "public.credibility", 8)
        self._add_to_metric(state, actor, "private.ai_expertise", 5)

        if topic == "safety":
            self._add_to_metric(state, None, "public_sentiment", -5)
            self._add_to_metric(state, "government", "private.political_capital", -3)
        elif topic == "jobs":
            self._add_to_metric(state, None, "public_sentiment", -3)
            self._add_to_metric(state, "labor-unions", "public.public_support", 5)
        elif topic == "inequality":
            self._add_to_metric(state, None, "public_sentiment", -2)
            self._add_to_metric(state, "labor-unions", "public.member_confidence", 3)
        else:
            self._add_to_metric(state, None, "public_sentiment", 2)
            self._add_to_metric(state, "government", "public.international_influence", 3)

        return [f"Media publicerar utredning om AI och {topic}."]

    def shape_sentiment(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Media attempts to shape public sentiment."""
        direction = args.get("direction", "neutral")
        self._add_to_metric(state, actor, "private.editorial_independence", -5)

        if direction == "positive":
            self._add_to_metric(state, None, "public_sentiment", 5)
            self._add_to_metric(state, actor, "public.credibility", -3)
        elif direction == "negative":
            self._add_to_metric(state, None, "public_sentiment", -5)
            self._add_to_metric(state, actor, "public.credibility", -3)

        return ["Media utövar redaktionell påverkan."]

    def build_expertise(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Media invests in AI expertise."""
        self._add_to_metric(state, actor, "private.ai_expertise", 15)
        self._add_to_metric(state, actor, "private.advertising_revenue", -3)
        return ["Media investerar i AI-expertkompetens."]

    # =========== BUSINESS SECTOR ACTIONS ===========

    def accelerate_ai_adoption(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Business sector accelerates AI adoption."""
        intensity = args.get("intensity", 60)

        self._add_to_metric(state, actor, "private.ai_investment_commitment", 15)
        self._add_to_metric(state, actor, "public.ai_adoption_rate", 8)
        self._add_to_metric(state, actor, "public.profitability", 5)
        self._add_to_metric(state, actor, "private.labor_satisfaction", -10)

        if intensity > 70:
            self._add_to_metric(state, None, "unemployment_rate", 0.3)
            self._add_to_metric(state, "labor-unions", "private.strike_readiness", 10)
            self._add_to_metric(state, None, "public_sentiment", -8)
        else:
            self._add_to_metric(state, None, "public_sentiment", 2)

        return [f"Näringslivet accelererar AI-implementering (intensitet {intensity})."]

    def lobby_government(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Business sector lobbies government."""
        target = args.get("target", "regulation")
        self._add_to_metric(state, actor, "private.regulatory_compliance_burden", -5)

        if target == "regulation":
            eu_pressure = state.get_metric(None, "eu_regulatory_pressure")
            state.set_metric(None, "eu_regulatory_pressure", max(0, eu_pressure - 8))
            self._add_to_metric(state, "government", "private.political_capital", -8)
        else:
            self._add_to_metric(state, actor, "public.profitability", 3)
            self._add_to_metric(state, None, "public_sentiment", -2)
            self._add_to_metric(state, "government", "public.budget_billion_sek", -1)

        rel = state.get_relationship(actor, "government")
        rel.trust += 0.15
        return [f"Näringslivet lobbar för {target} fördelar."]

    def invest_in_safety(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Business sector invests in AI safety."""
        amount = args.get("amount", 30)

        self._add_to_metric(state, actor, "public.profitability", -3)
        self._add_to_metric(state, "media", "public.credibility", 5)
        self._add_to_metric(state, None, "public_sentiment", 4)
        self._add_to_metric(state, actor, "private.labor_satisfaction", 5)

        state.add_fact("Näringslivet investerar i AI-säkerhet", source="action:invest_in_safety")
        return [f"Näringslivet satsar på AI-säkerhet ({amount}%)."]

    def cut_workforce(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Business sector cuts workforce due to AI automation."""
        percentage = args.get("percentage", 5)

        self._add_to_metric(state, actor, "public.profitability", 8)
        self._add_to_metric(state, None, "unemployment_rate", percentage / 10)
        self._add_to_metric(state, None, "public_sentiment", -15)
        self._add_to_metric(state, "labor-unions", "public.member_confidence", -8)
        self._add_to_metric(state, "labor-unions", "private.strike_readiness", 20)
        self._add_to_metric(state, "media", "public.credibility", 5)

        rel = state.get_relationship(actor, "labor-unions")
        rel.trust -= 0.4

        state.set_outcome_flag("workforce_reductions_announced", True)
        return [f"Näringslivet annonserar {percentage}% uppsägningar på grund av AI."]
