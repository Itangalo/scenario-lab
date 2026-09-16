# Notes for next major version of Scenario Lab

This document contains human-written notes on base architecture and main choices for the next version of Scenario Lab (version 5).

## Things to keep

Most principles and architectural decisions in Scenario Lab 3 and 4 should be kept. Most important of these are "lean into LLM". We should let LLMs make a lot of decisions, rather than creating custom code.

## Important improvements

### Improve ledger use

Version 4 introduced a ledger ("the store") for persistent notes. This should be improved on, and the metrics should be a special case of things to keep in the ledger.

- Like version 4, there should be world and actor scopes. There should be room for multiple tables, description of data types, validation checks, and how errors/warnings should be reported.
- Like version 4, there should be syntax for adding, updating and removing things from the Ledger. It should always be placed under a particular header.
- Like version 4, there should be replacement patterns to use for inserting information from the Ledger. The possibilities for filtering and getting aggregated results should probably be improved.
- There should be methods for mass-reading selected data from ledgers over multiple turns, to generate data for analysing completed simulations.
- It is quite possible that world state and generated prose should be stored in the Ledger.
- It is quite possible that the list of potential events should be stored in the Ledger.

### Options for negotiations

Before actors describe their actions, there should be optional room for negotiations. Negotiations consists of actors writing short notes to one or more other actors, only viewable by them. The notes are appended to the world description, used when the actors decide their actions.

It should be possible to have negotiations in multiple rounds, allowing reacting to proposals in one way or another (including leaking confidential information to a third actor). It should be possible to restrict whom an actor can write notes to, and it should be possible to dynamically change the number of negotiation rounds – also per actor.

### Simplified phase order

The phases used in version 3 and 4 can and should be reduced to three:

- Events.
  - Input is the previous world state.
  - Events are drawn and evaluated. Potentially also created by the game master.
  - Output is a list of triggered events, possibly with prose attached to them.
- Actor actions.
  - Input is the previous world state + the triggered events.
  - Any rounds of negotiations.
  - Actors react to the world.
  - Output is descriptions of actions from each actor.
- World update.
  - Input is the list of triggered events, the actor actions, and the world rules.
  - Actions are evaluated; whether they are successful and what their effects are on world Ledger data.
  - The world Ledger data are updated based on the events.
  - The world Ledger data is updated based on the world rules.
  - There is room for adjusting the world rules, in rare cases.
  - Output is a new world state, and a narrative.

We should evaluate whether there should be an option to change the order of events and actor actions.

Resuming and branching should be possible after each phase, not just at the end of each turn. In general, these phases should be seen as a cycle, not a start-to-end procedure.

### Improved scenario building

- Better guidelines for how scenario files should be built. In particular, keeping files short is good. Separating descriptions from reasoning in world rules (currently "metric rules") is probably also a good principle.
- Sign-off documents should be a part of the scenario generation process; created one at a time during the creation process.

### Other improvements

- It should be possible to put output data from simulation runs in subfolders.
- The syntax in Markdown files should be more standardized, to give more stable parsing. One suggestion is to always have H2 headers to separate parsing segments, and nothing more.
- We should evaluate whether it should be possible to run Scenario Lab in "AI agent mode": Instead of calling LLMs at OpenRouter or whatever, subagents called from within Claude Code/OpenCode/similar are used. They are fed with the proper data and prompts, and keep their information between turns, not being used as one-off calls. (This might not be possible to do, but could be worth investigating.)
- Better and more formalized procedures for benchmarking how well LLMs do as actors, game master or other parts of Scenario Lab.
- Potentially using Jev (or other System One-type models) for parts of the evaluations in Scenario Lab.
