---
name: frame-scenario
description: >
  Front-end to scenario creation: turns a rough topic or curiosity into an
  approved, simulable research question, then builds a provenance-tagged
  information bank that `create-scenario` drafts from. Use before
  `create-scenario` whenever the starting point is a question rather than a
  finished pile of source material. Triggers: "I want to explore", "what
  would happen if", "I'm curious about", "can we simulate", "research a
  scenario about", "jag vill utforska", "vad skulle hända om", "ta reda på
  vad som behövs för ett scenario om".
---

# Frame Scenario: From Curiosity to Research Question and Information Bank

This skill covers the two stages that come *before* drafting scenario files:

1. Refine a rough topic into a research question that Scenario Lab can
   actually answer, iterating with the user until they approve it.
2. Build an information bank sufficient to draft the scenario from, mixing
   user-supplied material, web research, and model knowledge – with every
   claim tagged by where it came from.

It ends by handing off to the `create-scenario` skill, which drafts the
files. Do not draft `scenario.yaml`, `metrics.md`, or any other scenario file
here.

Read before starting:

- `docs/SCENARIO_TECHNICAL_REFERENCE.md` – so the frame you propose maps onto
  fields that actually exist (`time_scale`, `max_turns`, `actors`, metric
  bounds and reference points, event conditions and probabilities)

## Why the Question Comes First

The order matters and is easy to get backwards. The approved question decides
what is worth researching. If you gather material first and frame afterwards,
the scenario ends up shaped by whatever happened to be lying around rather
than by what the user wants to know.

So: no research in Phase 1 beyond what you need to understand the topic well
enough to propose a question. The heavy gathering starts in Phase 3, after
approval.

## Phase 1: Draft the Research Question

Start from whatever the user gave you. Propose **two or three candidate
questions**, not one – seeing alternatives is what makes a user realize which
question they actually meant. Vary them meaningfully: different subject,
different horizon, different level of aggregation. Do not offer three
rephrasings of the same question.

For each candidate, state it in one or two sentences, then show what it
implies for the frame (see Phase 2). Recommend one and say why.

### Criteria for a Good Research Question

Each criterion has a diagnostic test. The answers to the tests are the
scenario frame – this is the point of the criteria, not a formality. A
question that passes all seven can be drafted directly; one that fails a test
is not yet a question, it is a topic.

1. **Simulable.** It asks how a system evolves through the interaction of
   actors over time – not a fact, a definition, or a single-number forecast.
   *Test:* could two honest runs of this world end differently? If not, it is
   a lookup, not a simulation.

2. **Bounded in time.** It implies a starting point and a horizon.
   *Test:* what date does the world start at, and when do we stop caring?
   → `start_date`, `max_turns`, and the horizon.

3. **Paced.** There is a natural unit of "one thing happens".
   *Test:* what is the shortest interval in which something decision-relevant
   could plausibly change? → `time_scale`. Budget cycles, terms of office,
   product releases, and school years are good pacing anchors. If the honest
   answer spans two orders of magnitude, the question is mixing a fast
   process and a slow one; split it.

4. **Populated.** It implies 3–6 actors with real power over the outcome and
   at least partly conflicting interests.
   *Test:* who can decide something that changes the answer, and which pairs
   of them want incompatible things? → `actors`. A question whose actors all
   want the same thing produces smooth consensus narratives and is not worth
   running. If you cannot name a conflict, the question is probably about a
   process, not a system.

5. **Measurable.** It implies 3–6 quantities whose movement would constitute
   an answer.
   *Test:* what would have to go up or down for the answer to be "yes"? →
   `metrics.md`. Each quantity needs a plausible unit and bounds. Prefer
   things that could move visibly within the horizon; a metric that cannot
   change in the time available is background, not a metric.

6. **Genuinely uncertain.** The answer is not already settled, and the
   framing does not smuggle it in.
   *Test:* name two endings you would find credible if a run produced them.
   If you can only name one, the question is rhetorical. If the second one
   requires the world to be absurd, the horizon is too short or the actors
   too weak.

7. **Open, not leading.** Phrased so that the simulation is allowed to
   contradict it.
   *Test:* rewrite as "under what conditions does X happen, and how often?"
   Does it survive? "How will A cause B" presumes the mechanism; "when does B
   emerge, and does A drive it?" does not. Leading questions produce
   scenarios that confirm themselves.

Two further things to identify while testing, which are not criteria but fall
out of the same work:

- **Turning points** the question hinges on → candidate `events.md` entries,
  as probabilities rather than scripted certainties.
- **Fixed background** the question takes for granted → `background/context.md`,
  and explicitly out of scope.

### Common Failure Modes

- *Too big:* "what happens to Europe with AI" – no actor set, no metric can
  be bounded. Narrow to one system with identifiable decision-makers.
- *Too settled:* "how does the AI Act get implemented" – the answer is mostly
  written down. Ask what varies in the implementation instead.
- *Forecast in disguise:* "what will unemployment be in 2031" – wants one
  number. Reframe around the distribution and its drivers.
- *No conflict:* "how do schools adopt AI tools" – reframe around who loses
  something when they do.
- *Two questions:* a fast process and a slow one bolted together. Pick one,
  note the other in the out-of-scope list.

## Phase 2: Framing Checkpoint (required)

Present, concisely:

- the candidate questions with your recommendation
- for the recommended one, the frame that falls out of the tests: start date,
  time scale, horizon and turn count, actors with their central conflicts,
  candidate metrics with rough bounds, the turning points that should become
  events, and what is deliberately fixed background
- which criteria the recommended question passes weakly, and why you propose
  accepting that
- your open questions – only those that materially change the scenario and
  cannot be answered by research

Then iterate. Expect more than one round; this is the cheapest place in the
whole pipeline to change your mind, and the user reshaping the question here
saves a rewrite of every scenario file later.

Do not proceed to Phase 3 until the user approves a question.

On approval, write `scenarios/<scenario-id>/research-question.md`:

```markdown
# Research Question

<the approved question, 1-2 sentences>

## Why This Question

<what the user wants to learn and what they would do differently knowing it>

## Frame

- Start: <date>
- Time scale: <e.g. 3 months per turn>
- Horizon: <e.g. 5 years, 20 turns>
- Actors: <id – one line each, including who they conflict with>
- Candidate metrics: <id – unit, rough range, why it answers the question>
- Turning points to model as events: <one line each>

## Criteria Check

<the seven criteria, pass/weak, one line each; state the weakness where weak>

## Out of Scope

<fixed background assumptions, and the adjacent questions deliberately not asked>

## Approved

<date, and what the user changed from your proposal>
```

The approved question also becomes machine-readable: `create-scenario` will
copy it into `scenario.yaml` as a `research_questions:` entry, naming the
metrics and events that bear on it, so that `synthesize` answers it explicitly
after runs. Propose that entry here, in the frame section, rather than leaving
the drafting step to reconstruct it:

```yaml
research_questions:
  - id: rq_<short_slug>
    question: "<the approved question>"
    metrics: [<metric ids from the frame>]
    events: [<event ids from the frame>]
```

If the question decomposes into two or three sub-questions worth answering
separately, list them as separate entries. Keep the list short – these are the
questions the whole scenario exists to answer, not everything one might ask.

## Phase 3: Research Plan and Gathering

Derive the gap list from the approved question – never research the topic
generally. For each element of the frame, ask what you would need to know to
write it credibly, and mark what you already know versus what must be found.

Priority order when gathering, because it governs how much you trust a claim:

1. **User-supplied material** – files in `source-material/`, documents,
   notes, links the user gave. Highest authority. Where it conflicts with
   anything else, it wins unless it is plainly outdated, and then you say so.
2. **Web research** – for current world state, named actors, real figures,
   recent events. Fetch and extract to `source-material/` so the scenario
   stays reproducible after the link rots. Prefer primary sources over
   commentary about them. Note the retrieval date on everything.
3. **Model knowledge** – for structural and mechanism claims, typical
   dynamics, and how comparable systems have behaved. Legitimate and often
   the only option, but tag it, because it is the material most likely to be
   confidently wrong about specifics.

Rules while gathering:

- Never state a specific figure, date, name, or institutional fact from model
  knowledge alone without tagging it `[model]`. Specifics are exactly what
  gets fabricated.
- Record constraint-like statements ("rules out", "demands", "will never
  accept") **verbatim, with their scope**: who said it, what action and what
  kind of arrangement it covers, and when. Do not compress them into summary
  words – a paraphrase like "supports" or "containing" can silently widen or
  narrow the scope, and that single word can later flip the headline result
  (this happened: see `scenarios/swedish-government-formation-2026/design-notes.md`).
  If the source's own scope is unclear, record the ambiguity as a Known Gap
  for the drafting step's constraint interrogation – do not resolve it by
  choosing a wording.
- Where sources disagree, record the disagreement rather than picking a
  winner. Disagreement in the world is usually a signal that the quantity
  belongs in a metric or an event, not that one source is wrong.
- Stop when the frame is covered. The bank exists to make drafting possible,
  not to be exhaustive. An information bank nobody can read is a failure
  mode, not thoroughness.

## Phase 4: Write the Information Bank

Write to `scenarios/<scenario-id>/source-material/`. Organize by what the
drafting step needs, one file per element of the frame:

- `world-state.md` – the situation at `start_date`
- `actors.md` – or one file per actor for rich cases: who they are,
  incentives, resources, constraints, track record, who they conflict with
- `quantities.md` – the measurable dimensions: current values, historical
  ranges, what counts as a large move, plausible bounds
- `uncertainties.md` – the turning points, what would trigger each, base
  rates or informed guesses at how likely they are
- plus verbatim extracts of fetched sources, one file each

Tag every substantive claim inline with its provenance:

- `[user]` – from material the user supplied
- `[source: <name>, <date retrieved>]` – from a fetched or supplied source
- `[model]` – from model knowledge, unverified
- `[assumption]` – a choice you made to fill a gap, with the reasoning

Then write `source-material/INDEX.md`: one entry per file with what it
covers, provenance mix, how much to trust it, and – the part that matters
most – what it does **not** cover. Close with a "Known Gaps" section listing
what stays unresolved and how the draft should handle each: as an assumption,
as an event, or as an explicit limitation in `design-notes.md`.

## Phase 5: Handoff

Report to the user:

- the approved question
- what the bank contains and where the material came from, by proportion
- the known gaps and how you propose the draft handle each
- anything found during research that ought to change the question, if
  anything did – this happens, and it is better raised now than after
  drafting

Then invoke the `create-scenario` skill. It will detect
`research-question.md` and skip its own framing checkpoint rather than
re-interviewing the user on questions already settled here.
