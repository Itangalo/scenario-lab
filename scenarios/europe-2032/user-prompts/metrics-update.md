{# Scenario override. Identical to templates/user-prompts/metrics-update.md except for
   two additions, both after the notepad block:
   1. A hard ban on writing the uppercase regime labels (ACCELERATION,
      VERIFICATION-BOUNDED, PLATEAU) anywhere in the Narrative. The GM knows
      this run's regime because the variant's patched metric rules state it,
      but from turn 2 onward the narrative IS the world state the EU reads, so
      the narrative is the one channel that carries the regime to the actor.
      The same leak was observed repeatedly in forking-futures, where the
      referee caught some occurrences, missed others, and ran out of attempts
      once. Prevention at the source is the only reliable layer.
   3. The US_POSTURE line, which must be carried in the Notepad from the turn
      the 2028 election fires onward.
   2. Guidance for treating tracked emerging developments as faint narrative
      signals rather than events.
   Keep in sync with the default template when that changes. #}
{% if background_context %}
## Fixed Background (unchanged all run)

This is the world as it stood at the start. It does not change, and it outranks
the evolving narrative on any fact it states — if the narrative drifts away from
something fixed here, the narrative is wrong.

{{background_context}}

{% endif %}It is now turn {{turn}} which covers {{time_period}}.

The Metric Rules looked like this (possibly updated):

{{metric_rules}}

The world state at the start of the turn is described as follows:

{% if historical_summary %}
## Previous History
{{historical_summary}}
{% endif %}

## Current Situation ({{time_period_lower}})
{{world_state}}

---

The notepad contains the following information:

{{notepad}}

{% if has_emerging_developments %}
The "Emerging developments (tracked)" section lists developments that recent turns have judged plausible but that have not happened. They are not events. Let them colour the narrative only as faint, ambiguous signals whose visibility grows with how long they have been listed — never as anything confirmed, and never with a stated probability.
{% endif %}

**Four rules bind your output. The first two bind the Narrative specifically, and the first of them overrides any pull toward explanatory convenience:**

1. **Never write the uppercase labels `ACCELERATION`, `VERIFICATION-BOUNDED` or `PLATEAU` anywhere in the Narrative — not in prose, not in a subheading, not as "consistent with".** You know which regime this run is in and apply its rules; the EU does not, and from turn 2 onward the narrative is exactly what the EU reads. Name behaviours, never the pattern: capability growth that slows, accelerates or splits between domains is described by what it did this turn, full stop.
2. **Never write an event id in the Narrative.** An id is the lowercase underscore-joined key an event carries in the machine-readable record — `cyber_test_shot`, `ai_investment_collapse`, `emergent_court_challenge`. No newspaper, minister or official has ever used one. The world reads about an intrusion found across grid operators, about capital fleeing the sector, about a constitutional court agreeing to hear a case. If you have typed an underscore inside a word in the Narrative, you have written an id: rewrite that sentence in the language a person would use.
3. Tracked emerging developments are world trends, not happenings: they surface as atmosphere, rumour and single-source reporting whose intensity scales with how long they have been listed.
4. Once `us_election_2028` has fired, write the resulting `US_POSTURE: CONSOLIDATION`, `US_POSTURE: ALLIANCE` or `US_POSTURE: RETRENCHMENT` line into the world state for that turn, and carry the same line in the Notepad every turn thereafter. It is a standing condition of the world that metric rule 18 reads each turn, not a one-off narrative beat.

---

This turn, the following external events have occurred:

{% if triggered_events %}
{{triggered_events}}
{% else %}
None
{% endif %}

---

The actors in the scenario describe their actions as follows:

{{actor_actions}}

---

Use this information to do the following:

* Determine how successful the actors are with their actions. This is based on how the world looks and your assessment of how likely they are to succeed.
* Based on the actors' actions and Metric Rules, determine Metrics for the next turn.
* Write a coherent narrative that tells what happens in the world during this turn.

{% if output_language %}
Please write your response in {{output_language}}.
{% endif %}

Important: You must use the exact headers '## Metrics', '## Narrative', and '## Notepad' as specified below. Do not translate these headers, even if you are writing the content in another language.

Respond with a Markdown text with the following content:

* Heading level 2: Metrics
* A JSON object describing all metrics in a ```json code fence, in the following format: `{"metric1_name": value1, "metric2_name": value2}`
* Heading level 2: Narrative
* A coherent story about what happens in the world during the turn (max 400 words). You may use subheadings (level 3) if desired.
