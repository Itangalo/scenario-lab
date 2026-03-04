# Metric Rules v1 (Turn 0 - Initial)

## Rules

1. ai_capability grows quickly at low levels (roughly +40% to +80% per turn), but growth should slow as capability increases, especially after ai_capability > 200 unless reinforced by breakthroughs.
2. ai_adoption_sweden tends to rise when AI is usable, accessible, and stable enough to deploy, but when ai_capability increases very rapidly, adoption can and often should temporarily fall because organizations, workers, and even previously knowledgeable users cannot keep up with the pace of change. As a default heuristic, holding other factors constant, if ai_capability changes by factor f in a turn, immediate adoption pressure should first scale by roughly 1/f (for example, a doubling of ai_capability can temporarily halve adoption) before slower "natural" adoption growth resumes from usability gains, training, and rollout efforts. Adoption growth should also slow as adoption increases (saturation/friction), especially beyond 60.
3. Faster capability progress creates labor-market pressure: if ai_capability grows rapidly while adoption is broad, unemployment should tend to rise unless strong transition measures are present.
4. If unemployment is above 9, public_sentiment_to_ai usually falls; if unemployment is above 12, the negative effect on sentiment strengthens.
5. public_sentiment_to_ai should not drift automatically upward each turn; outside major positive developments, it tends to move slowly and can revert toward neutral.
6. If ai_capability rises much faster than ai_adoption_sweden for 2 consecutive turns, public_sentiment_to_ai decreases due to perceived exclusion and insecurity.
7. Significant strikes or labor conflict usually slow ai_adoption_sweden growth in the same turn and can increase unemployment in the next turn.
8. Major supply-chain shocks (e.g., Taiwan blockade) reduce ai_capability growth and can dampen adoption momentum until de-escalation or adaptation is established.
