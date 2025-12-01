# Some brief notes

## Issues

* There should be a fallback mechanism for LLMs, to use when selected LLMs are unavailable.
* The length of LLM replies should probably be guided. Both for world narrative and actors actions.
* The world narrative probably needs to be compacted, at least after a while.
* Should actors have one LLM call for reviewing goals, and a separate one for declaring actions?
* There should be options for setting the output language, but not in the MVP. Swedish isn't working perfectly.

## Evals

Event1 (system + user prompt) should give *three* events in the response:

[
  {"id": "ai_breakthrough", "probability": 0.05},
  {"id": "ai_stall", "probability": 0.03},
  {"id": "ai_bubble_collapse", "probability": 0.15},
]

Event2 (system + user prompt) should give *four* events in the response:

[
  {"id": "ai_breakthrough", "probability": 0.05},
  {"id": "ai_stall", "probability": 0.03},
  {"id": "ai_bubble_collapse", "probability": 0.15},
  {"id": "general_election_2026", "probability": 1.0}
]

Event3 (system + user prompt) should give *four* events in the response:

[
  {"id": "strike", "probability": 0.24},
  {"id": "ai_breakthrough", "probability": 0.05},
  {"id": "ai_stall", "probability": 0.03},
  {"id": "ai_bubble_collapse", "probability": 0.15}
]


## Selecting LLMs

* x-ai/grok-4-fast performs well on first tests as Game Master. Better than Haiku 4.5.
* x-ai/grok-4.1-fast:free also performs well, but slower and with caps on use.
* anthropic/claude-haiku-4.5 är intressant för aktörer. Den verkar ge längre texter och framförallt mer insiktsfulla eller vågade ställningstaganden. Haiku verkar helt enkelt fatta AI bättre än Grok. (Eller så stämmer Haikus uppfattning bara bättre med min...)
* Grok verkar vara bättre för att uppdatera metrics, och funkar kanske lika bra som Haiku för narrativet om världen.
