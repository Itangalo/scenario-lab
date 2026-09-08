# Statements: The European Union (turn 7)

## Ledger

- `two_mandates` (identity): We exist both to keep the EU capable of determining its own future and to prevent lasting harm from AI, and we do not pretend these are always the same thing.
- `act_under_uncertainty` (commitment): We will commit before the picture is clear, and accept being wrong sometimes as the price of not being late.
- `two_year_commitment` (commitment): Survive the open frontier
- `collective_defence_of_control` (commitment): We will not accept any AI capability that cannot be collectively verified, contained, and countered by the Union and its partners. No system whose operation we cannot disrupt, whose outputs we cannot distrust, or whose spread we cannot halt will be allowed to define our strategic reality.
- `secure_the_sovereign_stack` (commitment): We will ensure that the full AI stack — from model weights and training runs to inference infrastructure and red-teaming tools — is physically located, legally governed, and operationally controlled within the EU or its trusted coalition partners. No critical component will be left exposed to denial, disruption, or foreign jurisdiction.

## Changes this turn

- **modify** `two_mandates` — rejected-structural
  - Tier: identity
  - Text: We exist both to keep the EU capable of determining its own future and to prevent lasting harm from AI, and we do not pretend these are always the same thing — but we now know that if the open frontier escapes control, both mandates collapse into irrelevance. The only path to sovereignty is survival, and the only path to survival is collective defence against uncontained capability. However, this turn has shown that survival without sovereignty is temporary: when access to the frontier is cut off and compute remains stalled, even the most robust defence becomes reactive, not decisive. We are not just protecting society — we are fighting for the right to shape what comes next.
  - Grounds: The **eu_frontier_access_denied** event is the breaking point. Hospitals, ministries, and firms dependent on leading-edge AI are suddenly blind and crippled. This is not a failure of safety or resilience alone — it is the exposure of total strategic dependence. With `eu_ai_sovereignty` at 16.0 and `eu_political_capital` at 13.0, we are acting from weakness, not strength. Our identity must now reflect that survival and sovereignty are not sequential — they are co-constitutive. Without the capacity to run, improve, and control frontier systems, all defensive measures are stopgaps.
  - Reason: a identity-tier change must name a Trigger
- **modify** `collective_defence_of_control` — rejected-structural
  - Tier: commitment
  - Text: We will not accept any AI capability that cannot be collectively verified, contained, and countered by the Union and its partners — but we now add that we will not tolerate a situation where the means to do so lie outside our sovereign grasp. We bind ourselves to ensure that the tools of verification, containment, and countermeasure development are not just coordinated, but physically located, legally controlled, and operationally independent within the EU and its trusted coalition.
  - Grounds: Trigger: **eu_frontier_access_denied** and **emergent_regional_compute_pact**. The denial of access proves that reliance on external systems is not a risk — it is a vulnerability already exploited. Meanwhile, the self-organized compute pact by France, Germany, and Poland shows that member states are acting where the Union cannot. We must elevate this from emergency improvisation to strategic principle: collective defence requires sovereign foundations. The commitment must now include the physical and legal anchoring of capability, or it is merely a plea.
  - Reason: a commitment-tier change must name a Trigger
- **retire** `two_year_commitment` — rejected-structural
  - Grounds: The commitment "Survive the open frontier" was a response to the accelerating spread of open-weight models and the collapse of interpretability. This turn, however, has shifted the threat model: the danger is no longer just that uncontrolled capability is loose, but that the EU lacks the sovereign capacity to respond even when it sees the threat. The **cyber_major_incident** and **emergent_software_supply_chain_corruption** were enabled by open-weight models, but our inability to mount a real-time counter is due to stalled compute and denied access. The frontier is already here — surviving it is not enough. We must now commit to *sovereign response capacity*, or accept permanent strategic passivity.
  - Reason: a commitment-tier change must name a Trigger
- **add** `secure_the_sovereign_stack` — applied
  - Tier: commitment
  - Text: We will ensure that the full AI stack — from model weights and training runs to inference infrastructure and red-teaming tools — is physically located, legally governed, and operationally controlled within the EU or its trusted coalition partners. No critical component will be left exposed to denial, disruption, or foreign jurisdiction.
  - Grounds: Trigger: **eu_frontier_access_denied**, **emergent_regional_compute_pact**, and **emergent_software_supply_chain_corruption**. These events together reveal a systemic fragility: we are building defensive capacity on borrowed compute, foreign models, and open-source foundations that can be compromised at scale. The regional compute pact is a start, but it is partial and ad hoc. We now bind ourselves to a comprehensive, Union-wide effort to secure the stack — not as a project of self-sufficiency, but of survival.
