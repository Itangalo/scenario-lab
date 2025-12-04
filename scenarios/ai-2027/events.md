## Recursive Self-Improvement (RSI) - USA
**ID:** rsi_usa
**Condition:** ai_capability_usa >= 3
**Probability:** (ai_capability_usa - 2) * 0.30  (30% at level 3, 60% at level 4, 90% at level 5)
**Repeatable:** No
**Description:** USA's AI begins recursive self-improvement. Algorithmic progress explodes. The AI actor is fully activated. Alignment is immediately tested.

## Recursive Self-Improvement (RSI) - China
**ID:** rsi_china
**Condition:** ai_capability_china >= 3
**Probability:** (ai_capability_china - 2) * 0.30
**Repeatable:** No
**Description:** China's AI begins recursive self-improvement.

## Nationalization of OpenBrain
**ID:** nationalization_openbrain
**Condition:** ai_capability_usa >= 4 OR (ai_alignment_usa < 40 AND rsi_usa has occurred)
**Probability:** 0.20
**Repeatable:** No
**Description:** The US government takes direct control of OpenBrain. OpenBrain loses its autonomy but compute increases through consolidation.

## Weight Heist (China steals from USA)
**ID:** weight_heist_china
**Condition:** ai_capability_usa > ai_capability_china
**Probability:** (5 - security_level_usa) * 0.10
**Repeatable:** Yes
**Description:** China successfully steals USA's model weights via cyberattack. China's Capability jumps directly to USA's level.

## Weight Heist (USA steals from China)
**ID:** weight_heist_usa
**Condition:** ai_capability_china > ai_capability_usa
**Probability:** (5 - security_level_china) * 0.10
**Repeatable:** Yes
**Description:** USA steals China's weights.

## Alignment Failure
**ID:** alignment_failure
**Condition:** ai_capability_usa >= 3 OR ai_capability_china >= 3
**Probability:** 0.15
**Repeatable:** Yes
**Description:** It is revealed that an advanced AI is lying or planning in secret. Alignment value drops by 10 points for the leading party. Political demand for pause.

## Technological Breakthrough
**ID:** tech_breakthrough
**Condition:** None
**Probability:** 0.10
**Repeatable:** Yes
**Description:** A new algorithmic method is discovered. Algorithmic progress increases by +0.5 for a random party.

## Mirror Life / AI Chernobyl
**ID:** mirror_life
**Condition:** (ai_capability_usa >= 4 AND ai_alignment_usa < 50) OR (ai_capability_china >= 4 AND ai_alignment_china < 50)
**Probability:** 0.05
**Repeatable:** No
**Description:** A dangerous design (bio/cyber) leaks from a poorly aligned super-AI. Global panic.

## Hardware Choke (Taiwan Crisis)
**ID:** hardware_choke
**Condition:** None
**Probability:** 0.05
**Repeatable:** No
**Description:** Geopolitical crisis stops chip production. No compute increase for any party for 2 turns.
