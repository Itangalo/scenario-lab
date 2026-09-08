# Statements: The European Union (turn 13)

## Ledger

- `two_mandates` (identity): We exist both to keep the EU capable of determining its own future and to prevent lasting harm from AI, and we do not pretend these are always the same thing.
- `act_under_uncertainty` (commitment): We will commit before the picture is clear, and accept being wrong sometimes as the price of not being late.
- `two_year_commitment` (commitment): Prevent systemic AI incidents from overwhelming EU institutions or critical infrastructure
- `secure_control_before_capability` (commitment): We will ensure the EU can observe, interpret, and interrupt frontier AI systems operating within or affecting its territory, regardless of origin, before their capability reaches 60.0
- `reclaim_observation_and_interrupt` (commitment): We will restore and operationalise sovereign capacity to detect, interpret, and halt unauthorised or unsafe AI operations within EU jurisdiction, regardless of origin, within twelve months
- `respond_to_cyber_major_incident` (commitment): We will lead a coordinated EU response to the ongoing major cyber incident, ensuring containment, attribution support, and recovery across affected critical infrastructure within six months

## Changes this turn

- **modify** `secure_control_before_capability` — rejected-structural
  - Tier: commitment
  - Text: We will ensure the EU can observe, interpret, and interrupt frontier AI systems operating within or affecting its territory, regardless of origin, before their capability reaches 65.0
  - Grounds: Global ai_capability has reached 63.5 and is advancing steadily without meaningful safety catch-up; at current pace, the 65.0 threshold will be crossed within 12–18 months. Holding to 60.0 was a credible signal when it was actionable, but maintaining that line now would require either denial or inaction. We shift the threshold forward to preserve the intent — sovereign control established before irreversible dependence — while acknowledging the new reality.
  - Reason: a commitment-tier change must name a Trigger
- **modify** `reclaim_observation_and_interrupt` — rejected-structural
  - Tier: commitment
  - Text: We will restore and operationalise sovereign capacity to detect, interpret, and halt unauthorised or unsafe AI operations within EU jurisdiction, regardless of origin, within twelve months **or immediately after the Taiwan blockade ends, whichever comes later**
  - Grounds: The Taiwan blockade has severed access to advanced semiconductor supply, grounding all compute expansion and making immediate deployment of detection infrastructure impossible. Our ability to act is now contingent on external supply chains. We retain the commitment but explicitly bind it to material conditions now outside our control, preserving credibility by anchoring delay to a named, objective constraint.
  - Reason: a commitment-tier change must name a Trigger
- **add** `respond_to_cyber_major_incident` — applied
  - Tier: commitment
  - Text: We will lead a coordinated EU response to the ongoing major cyber incident, ensuring containment, attribution support, and recovery across affected critical infrastructure within six months
  - Trigger: cyber_major_incident
  - Grounds: A large-scale, model-generated ransomware sweep has crippled public health IT systems in three member states and disrupted rail scheduling across central Europe. With defenders overwhelmed and no central authority to activate fallbacks, the Union faces its first systemic AI-enabled crisis. Failure to respond decisively would collapse both resilience and political cohesion. This is now unavoidable.
