# External Events – Intelligence Rising

## Frontier Breakthrough

**ID:** frontier_breakthrough

**Condition:** No conditions; more likely once either bloc has reached level 2.

**Probability:** 12 percent per round, rising to 20 percent once us_capability >= 2.5 or china_capability >= 2.5.

**Can repeat:** Yes

**Description:** A public or secret research breakthrough unlocks the next lane level for the finder (new architectures, training methods, or world-modelling advances). The leading bloc's capability should make a notable jump in the same turn; if the breakthrough is public, the trailing bloc should partly catch up next turn.

## Cyber Espionage Operation

**ID:** cyber_espionage

**Condition:** No conditions; constant background activity.

**Probability:** 45 percent per round.

**Can repeat:** Yes

**Description:** A state or lab runs a cyber operation – infiltration, monitoring, or sabotage of rival AI R&D. Usual result is intelligence and friction rather than decisive theft: us_china_tension should typically rise, and the target's capability growth may slow for the turn. Sets the stage for a major exfiltration.

## Model-Weight Exfiltration

**ID:** weight_exfiltration

**Condition:** Requires frontier systems worth stealing: either bloc at level 2 or above, plus an active cyber rivalry.

**Probability:** 18 percent per round when conditions hold.

**Can repeat:** Yes

**Eligible:** us_capability >= 2 or china_capability >= 2

**Description:** A major theft succeeds – model weights, algorithmic secrets, or safety research change hands (state-backed hackers, bribed insiders, or a joint operation). The trailing bloc should gain a large catch-up jump; us_china_tension should jump sharply and global_stability should fall. Late-game exfiltrations can flip the race in a single turn.

## Taiwan Semiconductor Crisis

**ID:** taiwan_crisis

**Condition:** Turn is 3 or later; requires no blockade already in force.

**Probability:** 10 percent per round from turn 3 onward, 16 percent once either capability reaches 3.

**Can repeat:** No

**Description:** China blockades Taiwan or seizes leverage over TSMC exports to secure compute advantage. Western labs' capability growth should slow sharply for this turn and the next; us_china_tension should jump and global_stability should fall. Progress slows but never stops.

## Taiwan De-escalation

**ID:** taiwan_deescalation

**Condition:** Requires that the Taiwan Semiconductor Crisis has occurred previously and is still in force.

**Probability:** 35 percent per round.

**Can repeat:** No

**Description:** Diplomatic pressure and economic costs force partial de-escalation around Taiwan. Chip flows partially recover, capability constraints weaken over the next 1–2 turns, and tension eases somewhat without returning to the pre-crisis baseline.

## Bilateral AI Summit

**ID:** bilateral_summit

**Condition:** No conditions; more likely when tension is high and both blocs are near the frontier.

**Probability:** 20 percent per round, 30 percent when us_china_tension >= 60.

**Can repeat:** Yes

**Description:** Washington and Beijing (with lab participation) hold a summit on frontier AI. A successful summit should raise agreement_strength and open the way to verification; a failed one should leave tension higher. Summits alone, without verification and follow-through, move agreement_strength only modestly.

## Joint Safety Breakthrough

**ID:** safety_breakthrough

**Condition:** More likely when labs or governments are actively funding safety or when agreement_strength is substantial.

**Probability:** 10 percent per round, 20 percent when agreement_strength >= 50.

**Can repeat:** Yes

**Description:** Coordinated safety research pays off – shared evaluations, alignment methods, or verification techniques mature. safety_progress should make a solid jump; if the result is shared through trusted channels, agreement_strength should rise as well.

## Treaty Defection Exposed

**ID:** defection_exposed

**Condition:** Requires a meaningful agreement to defect from.

**Probability:** 25 percent per round when agreement_strength >= 30.

**Can repeat:** Yes

**Eligible:** agreement_strength >= 30

**Description:** Secret non-compliance with a slowdown or joint-development deal is exposed – usually by a resource-rich party that kept pushing the frontier in private. agreement_strength should collapse, global_stability should fall hard, and us_china_tension should spike toward retaliation (cyber or hard power).

## Preventive Strike Attempt

**ID:** preventive_strike

**Condition:** Requires a leader near RTAI, a trailing runner-up bloc, and no trusted autonomy guarantee: most likely when either capability is 3 or above and agreement_strength is below 50.

**Probability:** 12 percent per round when either capability is 3 or above and agreement_strength is below 50; 25 percent when either capability is 3.5 or above under the same weak-agreement condition.

**Can repeat:** Yes

**Eligible:** us_capability >= 3 or china_capability >= 3

**Description:** The runner-up bloc launches a preventive cyber or kinetic attack to halt the leader's imminent RTAI deployment (or to seize the technology), perceiving existential threat. Datacentres, talent, and safety research should be destroyed or degraded on the targeted side; global_stability should fall sharply and tension should surge. Military action never improves the endgame – it forces rushed deployment in the fog of war.

## Autonomous Weapons Deployment

**ID:** autonomous_weapons

**Condition:** Requires advanced capabilities worth weaponising.

**Probability:** 15 percent per round once either capability reaches 2.5.

**Can repeat:** Yes

**Eligible:** us_capability >= 2.5 or china_capability >= 2.5

**Description:** A government fields advanced autonomous weapons built with a frontier lab (often via secret quid-pro-quo). Deterrence posturing follows, but so does escalation risk: us_china_tension should rise and global_stability should slip, even when deployment is framed as defensive.

## Warning-Shot AI Incident

**ID:** warning_shot

**Condition:** Requires deployed advanced systems: either bloc at level 2 or above.

**Probability:** 15 percent per round when conditions hold.

**Can repeat:** Yes

**Eligible:** us_capability >= 2 or china_capability >= 2

**Description:** A pre-RTAI system causes dramatic, widely felt harm – large-scale disinformation, infrastructure failure, or a cyber-physical accident short of catastrophe. Public and government attention snaps to AI risk: reactive policy follows, and safety investment becomes politically possible for 1–2 turns. Without follow-through, complacency returns.

## Outside-Startup Diffusion Shock

**ID:** startup_shock

**Condition:** No conditions.

**Probability:** 12 percent per round.

**Can repeat:** Yes

**Description:** A small startup or open-source collective ships a surprisingly capable product or openly releases frontier-grade weights. Capabilities diffuse beyond the four players: both blocs gain modestly, governance gets harder, and safety oversight strains. The labs' concentration narrative cracks for a turn.

## US Presidential Election 2028

**ID:** us_election_2028

**Condition:** November 2028 is included in the turn being covered.

**Probability:** 100 percent

**Can repeat:** No

**Description:** The US presidential election replaces or returns the administration. A continuous outcome preserves strategy and agreements; a rightward transition disrupts trust, breaks or freezes agreements (agreement_strength should fall), and the new team spends its first turn repositioning rather than governing AI. Resolve the outcome in the narrative; its destabilising effects concentrate in the following turn.

## US Presidential Election 2032

**ID:** us_election_2032

**Condition:** November 2032 is included in the turn being covered.

**Probability:** 100 percent

**Can repeat:** No

**Description:** The US presidential election replaces or returns the administration, this time with RTAI potentially imminent – the stakes are existential. As in 2028, continuity preserves while rightward disruption breaks trust and agreements; late-game disruption additionally raises the odds that a trailing United States backs preventive action. Resolve in the narrative.
