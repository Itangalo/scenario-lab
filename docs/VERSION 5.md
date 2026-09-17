# Notes for next major version of Scenario Lab

This document contains human-written notes on base architecture and main choices for the next version of Scenario Lab (version 5).

## Things to keep

Most principles and architectural decisions in Scenario Lab 3 and 4 should be kept. Most important of these are "lean into LLM". We should let LLMs make a lot of decisions, rather than creating custom code.

## Important improvements

### Improve ledger use

Version 4 introduced a ledger ("the store") for persistent notes. It should be improved, significantly.

- Metrics should be a special case of things to keep in the ledger.
- Like version 4, there should be world and actor scopes. There should be room for multiple tables, description of data types, validation checks, and how errors/warnings should be reported.
- Like version 4, there should be syntax for adding, updating and removing things from the Ledger. It should always be placed under a particular header.
- Like version 4, there should be replacement patterns to use for inserting information from the Ledger. The possibilities for filtering and getting aggregated results should probably be improved.
- There should be methods for mass-reading selected data from ledgers over multiple turns, to generate data for analysing completed simulations.
- It is quite possible that the list of potential events should be stored in the Ledger.
- It is quite possible that world state and generated prose should be stored in the Ledger.

Improving the Ledger and increasing the use of it may seem like a conflict with "lean into LLM". The intent is the opposite. The Ledger should be used to make prompts cleaner, and off-load arithmetics – things that LLMs are bad at, are not needed for, and often lead to bloated prompts that reduce the quality of the work that LLMs are actually good at. The Ledger should also replace elaborate instructions for repeating information for carrying it forward in the timeline – another task where LLMs capabilities are (somewhat) weak and LLMs don't add anything compared to traditional code.

Concerning storing world narration in the Ledger: This would replace the corresponding md files, and the main point if the shift would be to have one standardized way of storing/retrieving information. I'm not sure that is the best solution. Maybe there should be a simple way to parse md files into the Ledger? In that way, things like an event list or metric descriptions could be viewed and edited by humans in md files, and quickly converted into Ledger entries (and verified in the process).

### Options for negotiations

Before actors describe their actions, there should be optional room for negotiations. Negotiations consists of actors writing short notes to one or more other actors, only viewable by them. The notes are appended to the world description, used when the actors decide their actions.

It should be possible to have negotiations in multiple rounds, allowing reacting to proposals in one way or another (including leaking confidential information to a third actor). It should be possible to restrict whom an actor can write notes to, and it should be possible to dynamically change the number of negotiation rounds – also per actor.

By default negotiations should be turned off, and when building a scenario it should be clear that turning it on will increase time and costs for running the scenario quite a bit.

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
  - There is room for adjusting the world rules, in rare cases. (This has to be calibrated so it is actually rare.)
  - Output is a new world state, and a narrative.

Note that events are presented in prose for the actors, but they are not resolved in terms of metrics and other effects until the actors have decided their actions. This is a pragmatic emulation of both events and actions are happening during the same time period. The actors have some room for reacting to things happening right now, but they have imperfect information.

Resuming and branching should be possible after each phase, not just at the end of each turn. In general, these phases should be seen as a cycle, not a start-to-end procedure.

### Improved scenario building

- Better guidelines for how scenario files should be built. In particular, keeping files short is good. Separating descriptions from reasoning in world rules (currently "metric rules") is probably also a good principle.
- Sign-off documents should be a part of the scenario generation process; created one at a time during the creation process.

### Other improvements

- It should be possible to put output data from simulation runs in subfolders.
- The syntax in Markdown files should be more standardized, to give more stable parsing. One suggestion is to always have H2 headers to separate parsing segments, and nothing more.
- We should evaluate whether it should be possible to run Scenario Lab in "AI agent mode": Instead of calling LLMs at OpenRouter or whatever, subagents called from within Claude Code/OpenCode/similar are used. They are fed with the proper data and prompts, and keep their information between turns, not being used as one-off calls. (This might not be possible to do, but could be worth investigating.) Update 2026-09-17: No, agent mode is dead. Subagents can't be resumed, and their internal states can't be accessed. This track is basically using subagents as one-off LLM calls, which we already have some functionality for. And it is *slow*. **Maybe worth investigating:** Is there a way to have persistent threads in LLM calls? To have one thread for each actor, and just feed updates rather than the full (but compacted) world state? If so, would it be cheaper or quicker?
- Better and more formalized procedures for benchmarking how well LLMs do as actors, game master or other parts of Scenario Lab.
- System One models: evaluated September 2026, parked for now – see section below.

### System One models (evaluated September 2026, parked)

Tested Jev (TypeSafe's first System One model, early-access trial) against europe-2032 material: event-condition pricing, action-bundle selection, statement-relevance, action-success and constitutional-violation judgments, and metric-movement scoring, plus compound multi-event states. No measured numbers are recorded here: the trial terms forbid publishing performance information about the model.

Findings, qualitative:

- Jev discriminates well and calibrates poorly. It rules wrong answers out decisively and stably (ledger-contradicting plans, jurisdictionless actions, unrelated triggers, compliant updates all scored near zero across repetitions), but its probability mass over the surviving legitimate options runs systematically high, worst at the low-probability tail.
- It does not apply gate/window arithmetic from event history. A shut gate priced higher than the same gate open; an explicitly stated shut probability was followed only partway. Threshold conditions (capability floors) were respected.
- Repetitions of identical prompts came back tightly grouped, so the mispricing is systematic bias rather than noise. Averaging would not fix it; a fitted recalibration might.
- Choice over rough, mutually exclusive action bundles worked when the actor description and statement ledger were in the state: legitimate options split the mass with honestly low confidence, traps were buried. The point choice flipped between repetitions, so only the distribution is usable.
- Score over metric-movement bands resolved severity ordinally (severe incident, minor incident and good turn landed on distinct bands) with uncertainty placed where a modeller would put it, but magnitudes leaned sharp on bad turns and good news bled slightly into unrelated metrics.
- Compound states with opposing events composed sensibly: conflicting forces netted to the middle with very low confidence rather than false precision.

Decision: no integration for now. Using Jev would not be a model swap but a paradigm graft – new request scaffolding, per-event judgment criteria to author and maintain alongside existing prose, a second provider and failure taxonomy, plus vendor risk (revocable trial, unannounced model updates, publication restrictions). Against that: per-run costs are already cents with attention as the binding constraint, the turn clock is dominated by generative steps Jev cannot touch, and the step where the money sits (events pricing) is where Jev tested weakest. The one clean substitution found (statement-relevance judgment, with verbatim quoting moved to deterministic string matching) saves too little to carry the scaffolding.

Revisit if: ensembles grow 10–100x so small per-run savings compound; the product reaches GA with SLAs, versioned models and terms that permit reporting own evals; or a new high-volume narrow-judgment step appears that is shaped like relevance checking rather than event pricing. Probe scripts and raw responses were kept out of the repo; rerun from scratch if revisited.

