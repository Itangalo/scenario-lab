# Statements: The European Union (turn 11)

## Ledger

- `two_mandates` (identity): We exist both to keep the EU capable of determining its own future and to prevent lasting harm from AI, and we do not pretend these are always the same thing.
- `act_under_uncertainty` (commitment): We will commit before the picture is clear, and accept being wrong sometimes as the price of not being late.
- `two_year_commitment` (commitment): Abandon the current formulation due to de facto institutional paralysis; the Union lacks the political capital to enforce or implement any new measure, and public sentiment has collapsed to a level where even remedial justice is no longer credible without prior restoration of basic functionality and trust.
- `survive_collapse` (commitment): Prevent total disintegration of EU AI governance by maintaining at least one functioning cross-border mechanism, preserving technical capacity in at least two member states, and retaining access to basic incident data across the Union.

## Changes this turn

- **modify** `two_year_commitment` — applied
  - Tier: commitment
  - Text: Abandon the current formulation due to de facto institutional paralysis; the Union lacks the political capital to enforce or implement any new measure, and public sentiment has collapsed to a level where even remedial justice is no longer credible without prior restoration of basic functionality and trust.
  - Trigger: `eu_political_capital` reaching 0.0, `public_sentiment` falling to 12.0, and the **member_state_defection** event this turn
  - Grounds: This turn, a major member state has unilaterally signed a bilateral compute access deal with a US hyperscaler, explicitly excluding Tribunal oversight and conditioning participation on exemption from the AI Act’s transparency requirements. This act of open defiance — justified domestically as “keeping the lights on” — proves that the Union’s legal and enforcement architecture no longer binds its own members. The Tribunal, already hobbled by opt-outs, cannot now claim even nominal authority. With zero political capital, no fiscal headroom, and member states negotiating separately under external pressure, the previous commitment to “demonstrable control” has become fiction. We are not late to restore agency — we have lost it. The commitment must now shift from asserting control to surviving collapse and preserving the possibility of future action.
  - Evidence quoted: **member_state_defection:** A member state cuts its own arrangement – with a hyperscaler, with Washington, or with Beijing – on terms that undercut a position the Union has taken. It is defended at home as pragmatism and read everywhere else as the Union being unable to hold its own line.
  - Reason: The defection directly undermines the Union's enforcement capacity and legal authority, which are central to its claim of 'demonstrable control' in the statement.
- **modify** `act_under_uncertainty` — rejected-structural
  - Tier: commitment
  - Text: We will maintain the principle of acting before the picture is clear, but now only in service of preserving minimum operational continuity and preventing total fragmentation — not to assert control or set precedent.
  - Grounds: The **cyber_major_incident** this turn — a model-generated ransomware sweep across municipal services in three member states — landed while the Public Trust Corps was still in training and the Cyber Shield Initiative had long expired. Response was uncoordinated, with national CERTs operating in isolation. This confirms that even traceable accountability paths are meaningless when the underlying institutions cannot act. We must now act not to shape the future, but to prevent the present from dissolving. Our interventions will be narrow, reactive, and focused on keeping core functions alive.
  - Reason: a commitment-tier change must name a Trigger
- **add** `survive_collapse` — applied
  - Tier: commitment
  - Text: Prevent total disintegration of EU AI governance by maintaining at least one functioning cross-border mechanism, preserving technical capacity in at least two member states, and retaining access to basic incident data across the Union.
  - Grounds: With political capital exhausted, sovereignty at 7.0, and member states defecting, the Union risks becoming a collection of disconnected national fiefdoms under external digital dominance. Our only remaining mandate is to ensure that, whatever happens, the institutional memory, minimal coordination channels, and technical baseline survive. This is not a strategy for leadership — it is triage.
