# Metric Rules v1 (Turn 0 - Initial)

## Rules

1. ai_capability grows very quickly at low levels (roughly +100% per turn), but growth should slow as capability increases, especially after ai_capability > 200 unless reinforced by breakthroughs.
2. Whenever ai_capability is above ~100 and grows by a factor above ~1.2 in a turn, ai_adoption_sweden first decreases by the inverse factor. If ai_capability doubles, ai_adoption_sweden is halved. This is a direct drop in the adoption level, not just slower growth, and represents frontier AI advancing faster than users and organizations can absorb it.
3. After that drop, ai_adoption_sweden increases based on technology usability, access, training, and rollout. High public_sentiment_to_ai may boost adoption. Adoption growth slows above ~60.
4. Faster capability progress creates labor-market pressure: if ai_capability grows rapidly while adoption is broad, unemployment should tend to rise unless strong transition measures are present.
5. If unemployment is above 9, public_sentiment_to_ai usually falls; if unemployment is above 12, the negative effect on sentiment strengthens.
6. public_sentiment_to_ai should not drift automatically upward each turn; outside major positive developments, it tends to move slowly and can revert toward neutral.
7. If ai_capability rises much faster than ai_adoption_sweden for 2 consecutive turns, public_sentiment_to_ai decreases due to perceived exclusion and insecurity.
8. Significant strikes or labor conflict usually slow ai_adoption_sweden growth in the same turn and can increase unemployment in the next turn.
9. Major supply-chain shocks (e.g., Taiwan blockade) reduce ai_capability growth and can dampen adoption momentum until de-escalation or adaptation is established.
