{# Scenario override. Identical to templates/user-prompts/metrics-update.md except for four additions:
   1. Guidance for treating tracked emerging developments as faint narrative signals rather than events.
   2. The political-capital procedure: the portfolio charge (taken from rule 6's store figure, not recomputed), the proposal bonus and the sentiment term, each as its own required Notepad line.
   3. The standing record for the American posture: pending in turn 5, the winner from turn 6, read from the store every turn after and never carried in the Notepad. In turn 5, the turn the 2028 election fires, do NOT set it: the result is known but the administration has not taken office, so there is no standing posture yet.
   4. The sovereignty accounting line of step 3d, which unlike the three above is not a record of a judgement but the judgement itself: it starts from last turn's figure and the number it ends at is the one written into the Metrics JSON.
   The first three sit after the notepad block; the metrics_json block above it is now in the default template too and is not an override.
   A ban on writing the long run as settled used to sit here, and was removed on 2026-09-01 deliberately: the Game Master is never told the arm's name and never sees the other arms' rules, so it has no vocabulary for announcing which trajectory this world turned out to be. background/context.md does name the three readings in the opening world state, so the channel is not fully closed -- that was weighed and accepted.
   Finishing-turn moves live here rather than with the Union: only the Game Master sees the whole turn, so only it judges pull-ins, push-outs and event moves under rule 10, with grounds stated.
   Keep in sync with the default template when that changes. #}
It is now turn {{turn}} which covers {{time_period}}.

The Metric Rules looked like this (possibly updated):

{{metric_rules}}

Current metrics look like this:

```json
{{metrics_json}}
```

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

**Five rules bind your output. The first two bind the Narrative specifically, and the first of them overrides any pull toward explanatory convenience:**

1. **Never write an event id in the Narrative.** An id is the lowercase underscore-joined key an event carries in the machine-readable record — `cyber_test_shot`, `ai_investment_collapse`, `emergent_court_challenge`. No newspaper, minister or official has ever used one. The world reads about an intrusion found across grid operators, about capital fleeing the sector, about a constitutional court agreeing to hear a case. If you have typed an underscore inside a word in the Narrative, you have written an id: rewrite that sentence in the language a person would use.

2. Tracked emerging developments are world trends, not happenings: they surface as atmosphere, rumour and single-source reporting whose intensity scales with how long they have been listed.

3. **Price the portfolio, out loud, before you apply it.** Metric rule 6 charges `eu_political_capital` for every measure in flight, every turn, on all of them and not only the priority: 3 for a large measure, 2 for a small one, plus 1 more for whichever is the named priority. **Every term in the charge line is a subtraction, the priority's included.** Write it as `priority −1`: it is a further cost for pushing something, never a rebate, and a `+1` in that line has been read as one.

   Write one line in the Notepad giving every measure its price, opening with the turn so the carried line is self-dating:

   `PORTFOLIO CHARGE t1: Gigafactories −3, Frontier Access Guarantee −3, Resilience Surge −2, priority −1 = −9`

   **The measures half of that line is given to you.** Rule 6 above prints the portfolio as it now stands and what the measures come to, added up from the rows -- take that figure, do not recompute it. Itemise the measures anyway — the line is what makes the charge checkable — and check that your measure terms come to that same figure. If they do not, you have misread a row, and the rows are right. **The carried line is last turn's, and rule 6's figure is this turn's: they differ whenever the portfolio changed** -- a measure added, finished, or deleted since. That difference is expected, not an error to reconcile; the rows govern this turn, always.

   **A measure finishing this turn is not in the charge.** Rule 6 lists what finishes separately, and separately is where it belongs: the turn a measure reaches its finishing turn is the turn it pays out, not a last turn of costing. Adding a finishing measure back into the charge line is the commonest way the line comes to more than rule 6's figure.

   **The total at the end of the line is one further step, and it is yours.** The framework does not know which measure you named as the priority, so its figure covers the measures only. The line reads `= (the figure rule 6 gives) + 1 more for the priority`, as a subtraction. With four large measures and a priority, rule 6 says −12 and the line ends `= −13`. Copying rule 6's figure into the total and writing `priority −1` beside it leaves the priority uncharged, which is the commonest way this line goes wrong.

3b. **Then judge the proposal bonus, if this turn's new measure earned one.** A separate, one-off addition to `eu_political_capital` under metric rule 6, paid in the turn a measure is proposed and never again. It does not touch the charge above.

   Ask: **in the last three turns, did anything happen that this measure would have helped with?** Read that off the events themselves: what they were, how severe, and which of them this measure answers. What it is worth is your judgement, on how big the event was, how large the measure is, and how long ago it happened. **Typically +1 to +4**, the top of it for a large measure answering a severe, recent shock directly. Several open arguments pointing at one measure are judged together as a single figure, not summed.

   Write it as its own Notepad line, with the reasoning visible, or `PROPOSAL BONUS: none` when nothing argued for it:

   `PROPOSAL BONUS: Cyber Shield (cat 6, large) +3 — cyber_major_incident landed last turn and this answers it directly`

   Two things this rule is not. It is not a lookup: no table gives you the number, and a figure with no reason beside it is wrong. And it is not automatic: a small measure gesturing at an old event earns +1 or nothing at all, and `none` is the right answer more often than not.

3c. **Last, if this run's metric rules give `eu_political_capital` a term for sentiment sitting above it, apply it.** Only when the rules carry such a line, and only when `public_sentiment` is the higher of the two: add what the rule states, never taking capital past sentiment, after every other term above.

   Write it as its own Notepad line:

   `LEGITIMACY LENDS: capital 18, sentiment 31 -> +2`

   Compare the two numbers before writing anything. `none` is correct only when capital is the higher of the two, and a `none` whose own reasoning shows sentiment above capital is wrong.

3d. **Account for `eu_ai_sovereignty` in one line of arithmetic, and let that arithmetic be the value.** Metric rule 5 gives it exactly three sources, and they are not the same size:

   - a category 4 measure **in the turn its stated finishing turn is reached**: +3 to +6, that turn and no other. Two finishing in the same turn each pay in full.
   - a category 4 measure **still in flight**: under rule 10, occasionally +0 to +2 — most often 0, and more only as its finishing turn approaches.
   - **an event this turn that took away or secured access to capacity itself**: −1 to −3, or +1 to +3 where it secured. One such term at most, the largest where several events qualify. Rule 5 says which events these are and how to size one; an event that pressured, threatened or embarrassed the Union without reaching its capacity is not this term and gets nothing here.

   **The event term is a lookup, not a judgement.** The only ids you may charge are the ones listed above under "This turn, the following external events have occurred", and you charge them by copying the id from that list. Read the list before you write the line. If nothing in it is one of rule 5's capacity events, the line says `no capacity event` and there is no such term this turn — which is the ordinary case, not a gap to fill. A world that feels as though access has been lost, where no such event fired, is a world where nothing was charged: the atmosphere is the consequence of charges already made.

   Against them, `ai_capability` rising at least 2 this turn costs −1.

   Write one line in the Notepad that starts from last turn's figure, names every term, and ends at this turn's:

   `SOVEREIGNTY: 31 last turn, Sovereign Compute Corridor finishes t6 +5, Gigafactories in flight +1, eu_frontier_access_denied t6 −2, capability rose 2.5 −1 = 34`

   and in a turn where no capacity event fired, which is most turns:

   `SOVEREIGNTY: 34 last turn, no capacity event, Gigafactories in flight +1, capability rose 2.5 −1 = 34`

   **The number after the `=` is what you write for `eu_ai_sovereignty` in the Metrics JSON** — the same number, not one near it and not one you reached another way. Nothing outside rule 5 is a term: momentum, institutional follow-through, prior delivery, floors and rounding are not terms, and a line that reaches a total and then appends `→ net +1` has thrown away its own arithmetic. Read what finishes this turn off rule 6's finishing list — the store's rows, not your memory of the portfolio.

   **An event names the turn it fired, and that turn is this one.** Write `eu_frontier_access_denied t6 −2`, and only when the turn is 6 and the id is in this turn's list above. An event pays once, in the turn it happens, and is then gone from this line however long the world goes on dealing with it — a plant that is still shut, a supplier that has not come back, a member state that has not returned to the line. Those are consequences of a charge already made, not a charge to make again.

   **A completion names the turn it finishes, and that turn is this one.** Write `finishes t7 +5`, and only when the turn is 7. Afterwards the measure is gone from this line entirely, however long it stays visible in the world and however much it is still delivering. **This line is never copied forward.** Rule 6 above lists exactly what finishes this turn, and says plainly when nothing does: pay those and no others. Before this list existed the step had to recompute it from a portfolio it read out of prose, and in a batch of twelve, nine runs paid one measure's completion in two or more turns — one of them for six turns running, on a line reproduced word for word while the narrative beside it said the money had already been paid.

   **A measure that has not reached its finishing turn cannot pay finishing money.** Building momentum, permits granted, planning underway, a programme going well — none of these is a completion, and the most any of them is worth is +2.

4. **A finishing turn moves only when something moved it, and only you move it.** Each measure's finishing turn is carried by the framework and printed in the rows under rule 6; the Union cannot change it. Against rule 10, consider each running measure every turn: a named priority may pull it in by one, several unprioritised turns may push it out by one, an event may do either and rarely by more than one. Move with an `update` entry under your `## Store changes` carrying the condition as grounds — `{"op": "update", "table": "measures", "id": "M2", "fields": {"finish_turn": 5}, "grounds": "named priority"}` — and nothing else moves one. You never add or remove measures. If this turn's events or the Union's own neglect should have moved a finishing turn and you do not move it, say so in the Narrative instead.

{% if turn == 6 %}5. The 2028 election fired last turn: read the winner from the event record and set the standing record to the matching posture (`CONSOLIDATION`, `ALLIANCE` or `RETRENCHMENT`) with an `update` entry. From here it stands: it may not be dropped, reinterpreted or replaced later in the run.
{% elif turn > 6 %}5. The standing record already holds the posture. Leave it alone: it is read from the rows every turn and never rewritten, never carried in the Notepad, never touched by events.
{% elif turn == 5 %}5. The 2028 election fires this turn: set the standing record to `pending` — the administration has not taken office — and in particular never to a named posture: a named posture would let this turn's judgments price a government that does not exist. Record who won in the narrative only.
{% endif %}

Your world writes — the finishing-turn moves of step 4 and the standing record of step 5 — go under a `## Store changes` heading holding one JSON block, or `{"store": []}` when neither owes anything this turn:

```json
{"store": [{"op": "update", "table": "standing", "id": "S1", "fields": {"posture": "pending"}}]}
```

One malformed entry rejects that entry while the rest apply; leaving the whole section out is recorded as a fault rather than read as no change. The block holds *your* tables only: the `standing` record and `update` moves on `measures`. You never add or remove measures, and metric levels go under `## Metrics`, never here.

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

Important: You must use the exact headers '## Metrics', '## Narrative', '## Notepad', and '## Store changes' as specified below. Do not translate these headers, even if you are writing the content in another language.

Respond with a Markdown text with the following content:

* Heading level 2: Metrics
* A JSON object describing all metrics in a ```json code fence, in the following format: `{"metric1_name": value1, "metric2_name": value2}`
* Heading level 2: Narrative
* A coherent story about what happens in the world during the turn (max 400 words). You may use subheadings (level 3) if desired.
* Heading level 2: Notepad
* The four required lines: the portfolio charge, the proposal bonus, the legitimacy line, and the sovereignty line, each as specified above. The new content REPLACES the old, so each line is rewritten every turn, never copied.
* Heading level 2: Store changes
* One JSON block holding this turn's world writes, or `{"store": []}` when neither the standing record nor any finishing turn owes anything.
