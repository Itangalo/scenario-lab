{# Scenario override. Identical to templates/user-prompts/metrics-update.md except for two additions, both after the notepad block:
   1. A ban on writing the long run as settled in the Narrative. From turn 2 onward the narrative IS the world state the EU reads, so it is the one channel that could tell the actor how fast this world turns out to move — which is the inference the scenario exists to make it work for. There used to be a second, blunter guard here, banning three uppercase labels by name; the labels themselves are gone from every prompt now, so there is nothing left to spell.
   3. The US_POSTURE line, which must be carried in the Notepad from the turn the 2028 election fires onward.
   2. Guidance for treating tracked emerging developments as faint narrative signals rather than events.
   Keep in sync with the default template when that changes. #}
It is now turn {{turn}} which covers {{time_period}}.

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

**Six rules bind your output. The first two bind the Narrative specifically, and the first of them overrides any pull toward explanatory convenience:**

1. **Never write the long run as settled.** Report what happened to capability this turn, and what it plausibly suggests; never characterise the trajectory as established, name which of the futures under debate this world turned out to be, or write as though the question were closed. You apply this run's stated rates; the EU does not have them, and from turn 2 onward the narrative is exactly what the EU reads. Name behaviours, never the pattern: capability growth that slows, accelerates or splits between domains is described by what it did this turn, full stop.
2. **Never write an event id in the Narrative.** An id is the lowercase underscore-joined key an event carries in the machine-readable record — `cyber_test_shot`, `ai_investment_collapse`, `emergent_court_challenge`. No newspaper, minister or official has ever used one. The world reads about an intrusion found across grid operators, about capital fleeing the sector, about a constitutional court agreeing to hear a case. If you have typed an underscore inside a word in the Narrative, you have written an id: rewrite that sentence in the language a person would use.
3. Tracked emerging developments are world trends, not happenings: they surface as atmosphere, rumour and single-source reporting whose intensity scales with how long they have been listed.
4. **Price the portfolio, out loud, before you apply it.** Metric rule 10 charges `eu_political_capital` for every unfinished measure, every turn, on all of them and not only the priority: 3 for a large measure, 2 for a small one, plus 1 more for whichever is the named priority. **Every term in the charge line is a subtraction, the priority's included.** Write it as `priority −1`: it is a further cost for pushing something, never a rebate, and a `+1` in that line has been read as one.

   Then, **before totalling, price each measure against the event record.** Events in the catalogue carry a `Cheapens:` line naming the measure categories they make politically easier, by how much, and for how many turns. This part is a lookup, not a judgement: for each measure, find every event that has fired whose window is still open and whose `Cheapens:` names that measure's category, and subtract. Two stack.

   **Then discount further where the narrative earns it.** Metric rule 13 lets you lower a price with no incident behind it at all — a precursor that frightened people, sustained public pressure, an ally moving first, a rival's failure making the case for you. Judge it from the world as it actually stands, and name the reason in the charge line beside the figure. A measure the world is visibly asking for should not be priced as though nobody had heard of it. There is no floor — a measure can reach zero. Nothing raises a price except being the priority.

   A measure in a category that a recently fired event names, still charged in full, is this rule being skipped. It has been skipped before.

   Write one line in the Notepad, giving every measure its price and every discount its reason:

   `PORTFOLIO CHARGE: Gigafactories −1 (eu_frontier_access_denied cheapens 4 by 2), Frontier Access Guarantee −1 (same), Resilience Surge −2, priority −1 = −5`

   Then apply that total. It is written out because it is the rule most easily skipped in both directions: a turn in which several measures are unfinished and capital did not fall has forgotten the charge, and a turn in which the world plainly made something easier and every measure still paid full price has forgotten the discount.

5. **A finishing turn moves only when something moved it.** The portfolio carries a stated finishing turn per measure, set when the measure was proposed. Copy them forward as they stand. If a measure's finishing turn should change — pushed by being the priority, slipping through neglect, delayed or accelerated by an event — say so in the Narrative in the same breath as the reason, and write the new turn. A finishing turn that drifts with no reason given is an error.
6. Once `us_election_2028` has fired, write the resulting `US_POSTURE: CONSOLIDATION`, `US_POSTURE: ALLIANCE` or `US_POSTURE: RETRENCHMENT` line into the world state for that turn, and carry the same line in the Notepad every turn thereafter. It is a standing condition of the world that metric rule 18 reads each turn, not a one-off narrative beat.

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
