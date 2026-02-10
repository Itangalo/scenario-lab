# External Events – Sweden and AI 2030

## AI Incident in Sweden

**ID:** ai_incident_sweden

**Condition:** Requires ai_adoption_sweden >= 30

**Probability:** 8 percent per round when ai_adoption_sweden is 30-49, 12 percent when 50-69, and 18 percent when 70 or higher.

**Can repeat:** Yes

**Description:** A severe harm case linked to intensive use of an AI companion gets national attention. Public debate shifts toward AI safety and youth protection. Political pressure for regulation rises. public_sentiment_to_ai should drop, and short-term adoption growth should slow.

## Strike Against AI Implementation

**ID:** strike

**Condition:** Requires unemployment >= 9

**Probability:** 8 percent per round when unemployment is 9-9.9, 12 percent when 10-11.9, 20 percent when 12-14.9, 30 percent when 15-19.9, and 45 percent when 20 or higher.

**Can repeat:** Yes

**Description:** Trade unions initiate strikes against AI implementation at one or more major workplaces. Productivity decreases temporarily, tensions between unions and business increase, and media attention intensifies. public_sentiment_to_ai should typically fall in the short term.

## AI Breakthrough

**ID:** ai_breakthrough

**Condition:** No conditions

**Probability:** 4 percent per round when ai_capability is below 50, 7 percent when 50-149, and 10 percent when 150 or higher.

**Can repeat:** Yes

**Description:** A new architecture or training method significantly improves AI performance and efficiency. ai_capability should make a notable jump in the same turn, and expectations in public debate should rise.

## AI Development Plateaus

**ID:** ai_stall

**Condition:** Requires ai_capability >= 50

**Probability:** 4 percent per round when ai_capability is 50-149, 7 percent when 150-299, and 9 percent when ai_capability is 300 or higher.

**Can repeat:** No

**Description:** AI development hits temporary bottlenecks (data, compute, integration, regulation, or energy). ai_capability growth should slow for at least 1 turn unless a later AI breakthrough occurs.

## Taiwan Blockade

**ID:** taiwan_blockade

**Condition:** Turn is 3 or later

**Probability:** 5 percent per round

**Can repeat:** No

**Description:** China initiates a blockade of Taiwan. Global chip supply is disrupted, creating immediate compute constraints and uncertainty. ai_capability growth should slow sharply for this turn and likely the following turn unless a de-escalation event occurs.

## Taiwan Blockade De-escalation

**ID:** taiwan_blockade_deescalation

**Condition:** Requires that the Taiwan Blockade event has occurred previously

**Probability:** 35 percent per round

**Can repeat:** No

**Description:** Diplomatic pressure and economic costs force a partial de-escalation around Taiwan. Chip supply chains begin recovering and geopolitical pressure eases somewhat. ai_capability growth constraints from the blockade should weaken over the next 1-2 turns.

## AI Bubble Collapse

**ID:** ai_bubble_collapse

**Condition:** No conditions

**Probability:** 15 percent per round in turns 1-2, 12 percent in turns 3-4, and 6 percent in turns 5 and later.

**Can repeat:** No

**Description:** The AI investment bubble bursts. Startup valuations are written down, weaker firms fail, and hiring freezes spread. Unemployment should rise, and ai_adoption_sweden and ai_capability growth should slow for 1-2 turns.

## Parliamentary Election 2026

**ID:** general_election_2026

**Condition:** September 2026 is included in the turn being covered

**Probability:** 100 percent

**Can repeat:** No

**Description:** New parliamentary election leads to government negotiations and possible change of government. In case of government change, the government's goals can change radically.

## US Presidential Election 2028

**ID:** usa_election_2028

**Condition:** November 2028 is included in the turn being covered

**Probability:** 100 percent

**Can repeat:** No

**Description:** When a new president is elected in the USA, the country's policy on AI can change drastically.
