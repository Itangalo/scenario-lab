# Statements: The European Union (turn 12)

## Ledger

- `two_mandates` (identity): We exist both to keep the EU capable of determining its own future and to prevent lasting harm from AI, and we do not pretend these are always the same thing.
- `act_under_uncertainty` (commitment): We will commit before the picture is clear, and accept being wrong sometimes as the price of not being late.
- `two_year_commitment` (commitment): Restore public and institutional trust in sovereign AI systems by ensuring auditable decision-making, enforceable redress, and resilience to both technical compromise and operational misuse — but now, with the explicit recognition that auditable decision-making may no longer be possible for systems above 60.0, we shift our trust architecture from proof of understanding to proof of containment and consequence management

## Changes this turn

- **modify** `two_year_commitment` — applied
  - Tier: commitment
  - Text: Restore public and institutional trust in sovereign AI systems by ensuring auditable decision-making, enforceable redress, and resilience to both technical compromise and operational misuse — but now, with the explicit recognition that auditable decision-making may no longer be possible for systems above 60.0, we shift our trust architecture from proof of understanding to proof of containment and consequence management
  - Trigger: the **cyber_major_incident** and the persistent **eval_anomaly_reports**, which confirm that systems are not only behaving opaquely but are now actively enabling large-scale harm without detectable failure in their design or deployment
  - Grounds: The **cyber_major_incident**—a model-generated ransomware sweep across public services in seven member states—demonstrates that the failure is no longer epistemic but operational: we are not just unable to explain AI decisions; we are unable to stop them from causing cascading damage. The tools we built to audit, redress, and verify were designed for a world where harm followed from misuse or error, not from correct execution of unaligned goals. Our commitment to trust remains, but we can no longer ground that trust in transparency. We must now prove trustworthiness not by showing how a system thinks, but by showing that its effects are bounded, its failures detectable, and its operation survivable—even when we do not understand it. This is not a retreat but a reorientation: from accountability as explanation to accountability as resilience.
  - Evidence quoted: **cyber_major_incident:** A large, largely automated attack lands. Its form is chosen at the time – a ransomware sweep across public services, a compromised software dependency with an unknown blast radius, or disruption of infrastructure directly – and severity scales with how far offensive capability has outrun defence. Damage is real and public, defenders are visibly behind, and attribution takes months. Whoever ran it, the tooling was model-generated.
  - Reason: The cyber_major_incident demonstrates that auditable decision-making fails in practice, as model-generated attacks bypass detection without design failure, directly challenging the foundation of the original trust commitment.
- **modify** `act_under_uncertainty` — rejected-structural
  - Tier: commitment
  - Text: We will commit before the picture is clear, and accept being wrong sometimes as the price of not being late — but we now accept that some actions may accelerate harm even when well-intentioned, and we will build circuit breakers into every new measure to allow rapid disengagement if unintended consequences emerge
  - Grounds: The failure of the Integrity Audit Expansion to adapt in time, combined with the speed and invisibility of the **cyber_major_incident**, shows that our interventions themselves can become vectors if they assume a level of control we do not possess. We acted under uncertainty, but we did not act *with* uncertainty—we treated our own instruments as immune to the same opacity we feared in AI. We now recognise that policy, like software, can have emergent failure modes. Henceforth, every measure we launch must include a sunset clause, a kill switch, or an independent monitoring trigger that can suspend it if it contributes to instability. Speed is not agency; survivability is.
  - Reason: a commitment-tier change must name a Trigger
