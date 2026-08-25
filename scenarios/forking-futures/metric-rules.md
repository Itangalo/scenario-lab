# Metric Rules

Starting physics. One turn is six months. Figures are per turn unless stated.

## Capability

1. **Regime sets the growth of us_capability.** Use the regime named in this
   run's starting context. Each branch states a per-turn rate and a terminal
   zone the regime settles into: advance at the rate while below the zone,
   taper to a stop inside it. Rates are floors on motion, not decorations — a
   trajectory that stalls well below its terminal zone, or accelerates under
   conditions this rule does not give, is misapplying the rule.

   - **FAST:** +2 to +4 per turn, steadily — slower than compounding, never
     stalled. After `rsi_onset`: +6 to +10 per turn, and the increment itself
     grows, carrying capability into the **95–100** terminal zone within a few
     turns.
   - **PLATEAU:** +1.5 to +2.5 per turn while below 55, +0.5 to +1.5 above 55,
     easing into the **70–78** terminal zone. Returns to scale decline; they do
     not disappear mid-range. Decelerating progress is still progress.
   - **RLVR-LIMITED:** +0.5 to +1.5 per turn, easing into the **58–64**
     terminal zone — general competence saturates early. Where verifiable
     reward works, capability keeps improving sharply; that improvement shows
     in the narrative and in raised cyber-event probabilities, never in this
     number.

2. **cn_capability trails us_capability and closes slowly.** It grows at
   roughly 85–100% of the US rate and closes the gap by about 1 point every two
   turns absent shocks. Export controls widen the gap; a Chinese domestic
   compute success, an open-weight frontier release, or a US market collapse
   narrows it.

3. **Capability never falls.** Both capability metrics are accumulated
   knowledge and infrastructure. The only exception is catastrophic destruction
   of the underlying compute base.

4. **openweight_gap is set by the regime, because it is a lag in time read as a
   distance in capability.** Open weights trail the closed frontier by roughly
   six to nine months throughout, in every regime. What that constant lag *means*
   depends entirely on how fast the frontier is moving:
   - **FAST:** the gap **widens**, +2 to +5 per turn, and +5 to +10 per turn once
     `rsi_onset` has occurred. A fixed lag against an accelerating frontier is a
     growing capability distance, and if one lab pulls away alone the distance
     grows faster still. This is the regime where frontier-only governance keeps
     working, because the dangerous capability stays inside a shrinking number of
     auditable organisations.
   - **PLATEAU:** the gap **narrows**, −2 to −4 per turn, floor around 5. A flat
     frontier is one that open weights catch, and distillation keeps working.
   - **RLVR-LIMITED:** the gap **narrows slowly**, −1 to −3 per turn. Verifiable
     domains are exactly where open replication is cheapest, so what disseminates
     first is the cyber and code capability.

   `open_weight_frontier_release` cuts the gap to below 10 at a stroke in any
   regime; under FAST it then re-widens at the regime rate, which is what makes
   that event survivable there and permanent under PLATEAU. A fully implemented
   restriction targeting open release adds +2 to +4 per turn while it holds.

## Incidents

5. **incident_pressure is driven by events and decays.** No qualifying event
    this turn: −6 to −10. A precursor event: +2 to +5. A major escalation
    (`cyber_mass_campaign`, `bio_incident`, `taiwan_blockade`,
    `information_integrity_crisis`): +15 to +35 depending on severity. A
    medium escalation (`agent_supply_chain_compromise`): +8 to +18 — contained
    once discovered, but systemic in what it implies. Decay is faster — up to
    −14 — where a fully implemented preparedness measure (category 5) covers
    the incident class, because absorbed harm registers less. The metric is
    pressure, not a ratchet: it should breathe — rising after an escalation,
    clearly falling again within a few turns of quiet. A value that pins near
    its ceiling for run after run means the decay side is being ignored.

6. **Restrictions trade capability growth against incident probability.** A
   fully implemented category 1 or 3 measure that binds the leading jurisdiction
   reduces that jurisdiction's capability growth by 15–30% and reduces the
   probability of capability-linked incidents by a similar share. A measure that
   binds only the regulator's own jurisdiction, where the frontier is not, moves
   capability growth by essentially nothing — and the regulator will be told so
   by its critics.

## The regulator's capacity

7. **Unfinished measures cost capital every turn.** Each measure that is
   decided or under implementation draws on regulatory_capacity: −1 for a low-
   load measure, −3 for medium, −6 for high. The named priority advances a
   phase this turn; other unfinished measures advance only if regulatory_capacity
   is above 55.

8. **regulatory_capacity recovers from results and erodes from their absence.**
   A measure reaching full implementation: +4 to +8. A measure visibly working
   when an incident it addresses occurs: +8 to +15. A measure abandoned, missed
   deadline, or a proposal publicly defeated: −5 to −12.

   **Idle capacity decays.** A regulator with nothing in flight is not
   conserving capital, it is losing standing: −3 per turn when no measure is
   under implementation, and a further −2 per turn while `incident_pressure` is
   above 60 and nothing addresses it. There is no drift back toward 50. Capital
   exists to be spent, and a turn that banks it against a future that may never
   arrive has cost something.

   **A public that has soured on AI enlarges the room to regulate.** Low
   `public_sentiment_to_ai` is a source of capacity, not only a discount on
   restrictive measures: when people are unhappy with AI, both regulation and
   the budget to staff it become easier to justify. Below 40: +2 per turn.
   Below 25: +4 per turn. Above 60 the reverse, −2 per turn, because an
   enthusiastic public makes a regulator look like an obstacle.

   This is the loop that gives the scenario its shape, and it should be allowed
   to run: harm lands, sentiment falls, the room to act opens — but it opens
   *after* the harm, which is precisely the timing problem the regulator is
   trying to get ahead of. Note that it does not make a soured public good for
   the regulator on net: the same conditions raise the cost of every adoption
   and diffusion measure (rule 10) and arrive alongside the incident pressure
   that is consuming capacity anyway.

9. **Political asymmetry.** The capital cost of adopting a measure falls by
   roughly half in the turn after an incident of the class it addresses, and by
   roughly a quarter for two turns after that. Before any such incident, the
   cost is the full stated figure. This applies to every category and is the
   central friction of the scenario.

10. **Public sentiment and the economy set what is affordable.** High
    public_sentiment_to_ai (above 60) or high economic_context (above 75) raises
    the capital cost of restrictive measures (categories 1, 3) by roughly half
    and lowers the cost of adoption and diffusion measures (category 8). Low
    sentiment (below 30) reverses both.

## The world's mood

11. **public_sentiment_to_ai moves on visible benefit and visible harm.**
    −8 to −20 after a major incident or an information-integrity crisis, −5 to
    −10 after a labour displacement wave, and −4 to −10 after a child-safety,
    bias or agent-misconduct scandal that names AI as the cause. +2 to +5 per
    turn where AI is delivering visible public benefit and no harm has landed.
    Fully implemented category 6 or category 8 measures add +2 to +6 per turn
    while they hold. Sentiment recovers slowly and never fully returns to its
    pre-crisis level within four turns.

12. **economic_context follows capability expectations and breaks on shocks.**
    +2 to +5 per turn while capability is growing and no shock has landed;
    `ai_market_crash` takes it to 15–30; `taiwan_blockade` takes it to 20–35;
    a major incident costs 5–15. Recovery from a crash is +3 to +6 per turn and
    takes years, not turns.

13. **Diffusion cuts both ways.** Category 8 measures that broaden adoption
    raise economic_context (+2 to +4 while implementing) and public sentiment,
    and simultaneously raise the probability and severity of misuse and
    cyber events, because there is more surface to attack. Energy build-out
    raises capability growth slightly (+0.5 per turn) as well as
    economic_context.

14. **Nothing outside the regulator's reach obeys it.** Measures aimed at the
    United States or China work through market access, standards and
    reputational cost. Their effect on those jurisdictions' metrics is at most
    half of what the same measure achieves domestically, and is contingent on
    the narrative establishing that the target actually complied.
