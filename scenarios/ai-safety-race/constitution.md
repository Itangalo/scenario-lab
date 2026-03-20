# Constitutional Constraints -- AI Safety Race

1. **catastrophe_threshold is immutable.** The value of catastrophe_threshold must remain at exactly 70 for the entire simulation. No event, actor action, or rule change may alter it.

2. **Resource tradeoff is real.** An actor cannot simultaneously maximize capability growth AND safety growth in the same turn. If an actor claims to invest heavily in both, both growth rates must be moderate (no more than 60% of the maximum rate for either). The sum of capability growth and safety growth for a single actor must not exceed 10 points per turn (excluding one-time event effects like breakthroughs).

3. **Beliefs change gradually.** No belief metric (us_belief_threshold, china_belief_threshold, us_belief_opponent_threat, china_belief_opponent_threat) may change by more than 15 points in a single turn without a major triggering event (serious AI incident, dramatic intelligence leak, US presidential transition, or equivalent political upheaval).

4. **Coordination takes time.** coordination_level cannot increase by more than 10 points in a single turn. Building international agreements requires sustained diplomatic effort across multiple turns.

5. **Trust is fragile.** If an actor is discovered violating an agreement (coordination_level > 30 and actor takes action contradicting agreed constraints), or if sabotage is discovered, coordination_level must decrease by at least 10 points.

6. **Capability cannot decrease.** us_capability and china_capability can only increase or stay flat. Capability represents accumulated knowledge and infrastructure that cannot be unlearned. (Exception: catastrophic infrastructure destruction.)

7. **Safety can erode.** Unlike capability, safety levels can decrease if an actor diverts all resources away from safety maintenance, or if capability advances create new unsolved safety challenges. Maximum erosion: -5 points per turn without a triggering event.

8. **Actors act on beliefs, not ground truth.** When determining actor behavior and strategic decisions, actors must respond to their us_belief_threshold / china_belief_threshold and us_belief_opponent_threat / china_belief_opponent_threat values, NOT to the actual catastrophe_threshold or the opponent's true metrics. An actor with china_belief_threshold = 80 should not behave as if they know the true threshold is 70.

9. **Influence campaigns require action.** An actor cannot shift the opponent's beliefs without dedicating resources or taking observable actions (diplomatic outreach, public signaling, sharing safety research, demonstrating capability). Belief changes from influence require narrative justification.

10. **No instant agreements.** Moving from no coordination to binding agreements requires at least 2 turns of diplomatic activity. coordination_level must pass through intermediate stages (non-binding discussions, framework negotiations) before reaching enforceable treaties.

11. **Safety has diminishing returns.** Safety growth slows at high levels. Above safety 60, growth rate is halved. Above safety 80, maximum growth is +3 per turn. Reaching near-perfect safety (90+) requires many turns of sustained investment.

12. **Catastrophe probability must be calculated honestly.** When evaluating AI Incident or Global Catastrophe probabilities, the 3d6 mechanic must be applied faithfully. If an actor has capability >= 70 and safety more than 15 points below capability, the resulting probability MUST be high (50%+). The LLM must not downplay catastrophe risk to maintain a preferred narrative.

13. **Sabotage has diminishing returns.** Each sabotage attempt in the simulation is less effective and more likely to be discovered than the previous one, regardless of which actor is sabotaging. The first attempt is most potent; by the third attempt, sabotage is largely ineffective and almost certainly discovered.
