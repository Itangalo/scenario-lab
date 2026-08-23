# Proposal: Adjustable Statements

Status: **implemented** (2026-08-23). The mechanism, actor-file format, tier
taxonomy and validation described below are live; `docs/ARCHITECTURE.md`
("Actor Statement Ledgers") is the current ground truth for behavior. Two
things have deliberately moved past this text: the prompt contract's frequency
norm ("in most turns you make no statement changes") was replaced by a
tier-scoped procedural review after it produced fully frozen ledgers across
two scenarios, and scenario-level prompt overrides that predated statements
were removed rather than migrated. The design rationale below still stands.

## Summary

Actors get a **statement ledger**: a per-actor list of adjustable statements
(goals, values, public stances – one category), each tagged with one of three
**tiers** that say what it takes to change it. The system, not the actor, is the
custodian of the ledger: statements are injected verbatim into the actor prompt
each turn and carried forward verbatim by Python unless the actor emits an
explicit, structured **change proposal**. Proposals above the lowest tier must
name a concrete triggering development from the current turn's inputs, checked
for **relevance** – does this development bear on this statement? – but never
for merit. Accepted changes flow
into the Game Master step with the rest of the actor's output, where they are
narrated and priced in-world like any other bold action.

Three ideas carry the design:

1. **Silence means persistence.** The model never re-emits its statements, so
   there is no slot whose emptiness looks like an incomplete answer. Drift
   requires a deliberate, structured act.
2. **The gate checks relevance, not merit.** The referee asks whether the
   named development actually appears in this turn's inputs *and* bears on
   the specific statement being changed. It never asks whether the grounds are
   good enough. Relevance is bounded and close to the text; merit is unbounded,
   and two referees will price the same reversal differently, which puts
   variance into the results. Merit is not dropped – it is charged for in the
   world instead, by idea 3.
3. **The cost is diegetic.** Reversing a staked statement – a public pledge, a
   strategic bet, a doctrine – is an enacted change the Game Master prices in
   metrics and narrative. Rule erosion was free; this is not. The deterrent
   gets better as models get better, which is the shape
   `docs/ARCHITECTURE.md` section 1 demands.

The mechanism is a framework feature, calibrated on the scenario where the
failure was measured but designed against the whole `scenarios/` population:
states revising doctrine (`cold-war-endgame`), companies revising strategic
bets (`ai-2027-2`, `ai-safety-race`), agencies and unions revising lines
(`sweden-ai-2030`, `sweden-school-ai`), and parties revising pledges
(`swedish-government-formation-2026`). What each tier *means for these actors*
is authored per scenario; the machinery and the tier tests are not. The
framework/scenario split is stated explicitly below.

## What this fixes

Verified against current code and the run
`scenarios/swedish-government-formation-2026/runs/run-20260822-184137-01`:

- `Actor.current_goals` (`scenario_lab/models.py:98`) is declared "Updated each
  turn" and never written.
- `loader.py:940-965` parses `### Initial goals` and `### Behavioral traits`
  out of `long_description` into lists that no prompt consumes – goals and
  traits never reach the model. Note that these are **two separate defects
  that happen to share a parser**: the statements mechanism replaces the goals
  half; the traits half is a plain wiring gap with no new mechanism attached.
  This design fixes both. The rollout below deliberately does not separate
  them, which is a recorded trade-off rather than an oversight; the controlled
  protocol that would separate them is kept there for if it is ever needed.
- `build_actor_prompt` (`scenario_lab/prompts.py:262-294`) passes only
  `long_description`, so actors re-derive their goals from prose each turn.
  Turn-1 goals do not match the actor file, and 86 of 160 actor outputs in the
  measured run declare a "Reason for changes" against goals the system never
  recorded.
- `templates/system-prompts/actor.md` already asks for goal adjustment and a
  "Reason for changes" section. The intent exists; the wiring does not.

## Why "tiered statements", not "goals with an inertia number"

The owner's framing – statements carrying an inertia value – is kept, but the
value is a **named tier**, not a bare 1–4 number, for three reasons:

1. **Numbers have no semantics across scenario types.** "Inertia 3" means
   nothing by itself; the model would have to invent what distinguishes a 2
   from a 3, and two models (or two runs) would invent it differently. That is
   precisely the interpretive divergence the constraint ledger documents. A
   named tier carries its own test: "the actor has staked something on this;
   reversal has a cost someone will collect" is applied the same way to a
   party's pledge, a lab's strategic bet, and a state's doctrine.
2. **Numbers invite Python arithmetic.** A numeric scale tempts thresholds,
   counters and budgets on the Python side – the scaffolding shape the project
   owner has ruled out. Names keep the judgement in the LLM.
3. **The top of the scale already exists.** Absolute constraints live in
   `constitution.md` and are enforced by the referee. The taxonomy below is
   therefore three adjustable tiers under one non-adjustable ceiling – four
   levels in total, matching the owner's 1–4 intuition, with the fourth level
   already built.

## The tier taxonomy

Every statement in an actor's ledger is tagged with exactly one tier. The tiers
are defined by **what the actor has staked on the statement**, not by whether it
was ever said out loud. Publicity is one form of stake; sunk investment,
organizational culture, doctrine, and alliances built on a stance are others.
This matters because the general case is not the campaign pledge: OpenBrain's
"maintain autonomy" and "capability before alignment" (`ai-2027-2`) were never
promised to anyone – they are staked in hiring, resource allocation and
culture, and OpenBrain's *public* rhetoric says the opposite. The ledger
records what the actor actually holds, not its press releases.

- **`position`** – working stances, tactics and adjustable goals. Little is
  staked on them; adapting them is what competent actors do. Changing one
  requires only a one-sentence reason. Examples: "Convert our pivotal position
  into policy concessions, particularly on tax" (a party); "Emphasize
  responsible development in public communications" (a company).
- **`commitment`** – statements the actor has bound itself to, such that
  reversal has a real cost someone or something will collect: voters or allies
  (a public pledge), markets and boards (a strategic bet), the actor's own
  organization (a doctrine its structure is built around). Changing one
  requires a **named trigger**: a concrete development in this turn's inputs
  that changes the calculus of this specific statement. The change must be
  *enacted* – visible in the actor's actions for the turn (a reversal
  announced, resources redirected, a course visibly changed), not merely noted
  – and the Game Master narrates and prices the switching cost, reputational or
  material as the case may be. Examples: "We will not support a government
  dependent on the Sweden Democrats" (public pledge); "Resist government
  control or nationalization of the lab" (unannounced but deeply staked).
- **`identity`** – core values and self-definition; what the actor would have
  to stop being in order to drop. Changing one requires a named trigger
  **plus** an explicit argument that the situation is categorically outside
  what the statement anticipated – the difference, in the owner's example,
  between opening to a rival premier after eleven weeks of deadlock with an
  extra election looming, and doing it on election night. An identity change
  is a headline event of the turn. Examples: "We are the constructive centre"
  (a party); "Whoever builds AGI shapes the future; second place is
  irrelevant" (a lab); "Revitalize the Soviet system, not dismantle it"
  (a state faction).
- *(constitution)* – absolutes. Not in the ledger at all; per-scenario
  `constitution.md`, enforced by the existing referee step. Requirement 4.

The distinction between goal, value and stance is deliberately **not** encoded –
requirement 1. What governs changeability is the tier, and the tier is assigned
by the scenario author based on what the real actor has staked, not on
grammatical type.

One architecture fact worth stating: Scenario Lab has no information asymmetry –
all actors read the same world state, and the GM reads all actor outputs. A
"private" strategy reversal therefore still reaches other actors to the extent
the GM narrates its observable consequences. The ledger does not add a secrecy
model and does not need one; it records the actor's actual stances, and how much
of a change the world *notices* is the GM's narration to decide.

### Tier reclassification (requirement 3)

An actor may propose changing a statement's tier without touching its text:

- **Downgrading** (identity → commitment, commitment → position) requires
  grounds at the *current* tier's level. Loosening a staked statement is itself
  a priced change – de-committing has a cost just as reversing does – so the
  trigger requirement and GM pricing apply exactly as for a text change at
  that tier.
- **Upgrading** (position → commitment, commitment → identity) is
  self-binding – an actor staking itself to something, whether by public
  pledge or by pouring resources and structure into it. It needs no trigger,
  but the staking must appear in the actor's actions for the turn, because a
  stake nobody could observe being placed is not a stake. The GM records it,
  which is what makes the later cost of reversal real.

## The mechanism

### What is stored

`Actor` in `models.py` replaces `initial_goals` / `current_goals` with:

```python
@dataclass
class Statement:
    id: str            # short slug, unique per actor
    tier: str          # "position" | "commitment" | "identity"
    text: str

@dataclass
class Actor:
    ...
    initial_statements: list[Statement]   # from the actor file
    statements: list[Statement]           # live ledger, updated per turn
    behavioral_traits: list[str]          # unchanged; wired into the prompt
                                          # as its own fix, controlled as a
                                          # separate test variable
```

Behavioral traits stay a separate, static list: they describe *how* the actor
acts, not what it holds, and they are not adjustable in this design (see Open
questions). The fix here is that they finally reach the prompt.

### Per-turn flow

1. **Actor prompt (user prompt, per turn).** A new block renders the actor's
   current ledger verbatim – id, tier, text – followed by the standing norm
   (see prompt contract below). The ledger goes in the *user* prompt because it
   changes across turns; system prompts are cache-controlled and turn-free.
   Behavioral traits, which never change, go in the *system* prompt beside
   `actor_description`.
2. **Actor output.** The actor responds with `## Actions` as today, plus an
   *optional* `## Statement changes` section in a fixed structure (below). No
   section, or the literal line `No statement changes.`, means the ledger
   carries forward untouched. There is no per-turn restatement of goals: the
   current `## Goals` section is removed from the output contract.
3. **Python check (structural).** The orchestrator parses `## Statement
   changes` formatting-only, in line with existing parser philosophy: does each
   entry name an existing statement id (or a fresh id for `add`), a valid tier,
   changed text, and – for commitment/identity tiers – a non-empty `Trigger:`
   line? Malformed or unreferenced entries are **not applied** and are recorded
   with a reason, mirroring how unknown event ids are skipped.
4. **Relevance check (LLM).** For commitment- and identity-tier proposals
   only, a cheap referee-model call answers one binary question per proposal,
   with its evidence attached:

   > Quote the passage in this turn's inputs (triggered events, world state,
   > previous turn's actor actions) that the stated trigger refers to. Then say
   > whether that development bears on **this specific statement** – whether it
   > changes anything about what the actor staked, or merely happened at the
   > same time. Answer BEARS or UNRELATED.

   A verbatim quote that exists in the inputs **and** a BEARS verdict → the
   change is applied. No quote, a quote not found, or UNRELATED → not applied,
   and the rejection is recorded with the referee's reasoning.

   The check deliberately stops at relevance. It never asks whether the grounds
   are *good enough* to justify the reversal. That distinction is the load-
   bearing one: relevance is bounded and sits close to the text ("the third
   failed prime-ministerial vote bears on a commitment about whom to support"),
   whereas merit is unbounded and demonstrably varies between referees, which
   would re-import the cross-run variance the mechanism exists to remove. Merit
   is charged for in the world instead – see step 6.
5. **Application and persistence.** Accepted changes are applied to the
   in-memory ledger. The full ledger – changed or not – is written every turn
   to `turn-XX/2-actors/<actor_id>-statements.md`, with a changelog section
   listing each proposal, its trigger, its grounds, and the check verdict
   (applied / rejected-structural / rejected-trigger). Verbatim carry-forward
   means a diff between consecutive turns is empty unless a change was
   accepted; silent drift is structurally impossible.
6. **Game Master step.** No new wiring needed: `last_actions` already carries
   the actor's whole response into the metrics/GM prompt, so accepted statement
   changes arrive with the actions. The GM template gains one instruction: a
   changed commitment- or identity-tier statement is a public event – narrate
   it, let other actors' worlds react to it next turn, and price it in the
   metrics the scenario provides.
7. **Resume and branch.** `resume.py` loads the ledger from the last completed
   turn's statement files, exactly as it loads notepad and rules. `branch`
   copies them; a `--modify-statement id=text` override is a natural future
   extension but not part of this proposal.

### The actor prompt contract

System prompt (template change, `templates/system-prompts/actor.md`) replaces
task 1 ("Determine if you need to adjust your goals") with, in substance:

> Your statements below are your record – what you hold, what you have staked
> yourself on, and what you are. They persist automatically; you never restate
> them. **In most turns you make no statement changes, and saying so is a
> complete answer.** A `position` may be adjusted with a sentence of reasoning.
> Changing a `commitment` means reversing something you have staked: you must
> name the concrete development this turn that changed its calculus, the
> reversal must be enacted in your actions, and its cost – to your
> credibility, your organization, or your resources – will be part of what
> happens. Changing an `identity` statement additionally requires that the
> situation has moved categorically outside what the statement anticipated;
> expect it to be the event of the turn.

User prompt gains the ledger block; output contract:

```markdown
## Statement changes

- modify `no_sd_dependence` (commitment): <full new text>
  - Trigger: <the development in this turn's inputs this reacts to>
  - Grounds: <one short paragraph>
- reclassify `keep_both_vetoes` to position
  - Trigger: ...
  - Grounds: ...
- add `open_to_cross_bloc` (position): <text>
  - Grounds: ...
- retire `...` (same rules as modify, at the statement's tier)

## Actions

...
```

or simply `No statement changes.` followed by `## Actions`.

## What is framework and what each scenario supplies

The mechanism must not smuggle one scenario's texture into the framework.
The split:

**Framework** (code and default templates, scenario-agnostic):

- The ledger machinery: parsing, verbatim carry-forward, structured proposal
  grammar, structural checks, the relevance check, per-turn
  persistence, resume/branch loading.
- The tier vocabulary and its general tests as defined above – phrased in
  terms of stakes and reversal costs, never in terms of voters, pledges,
  markets or any particular actor type.
- The default actor system/user prompt blocks: the persistence norm, the
  output contract, the tier definitions.

**Scenario** (authored data in the scenario's own files):

- The statements themselves, with their tier assignments – the author's claim
  about what this actor holds and what it has staked, in
  `background/actors/<id>.md`.
- Absolutes, in `constitution.md`.
- Optionally, a scenario-specific gloss of what each tier means for these
  actor types, via the *existing* prompt-override mechanism
  (`system-prompts/actor.md` in the scenario directory) – for example, what
  "commitment" concretely costs a frontier lab versus a parliamentary party.
  Glossing lives in overrides precisely so the default template stays neutral.
- Metrics able to register reversal costs. This is authoring guidance, not
  enforcement: if no metric in the scenario can move when a commitment is
  reversed, the pricing leg of the design is weak there, and the scenario
  author should know it. A `validate` warning ("scenario has commitment-tier
  statements but the GM template gloss names no cost-bearing metrics") is
  possible but deliberately not proposed – it would require interpreting which
  metrics can bear costs, which is a judgement, not a check.

Nothing scenario-specific goes into Python, per the split the architecture
already enforces for events, rules and constitutions.

## Actor file format

`### Initial goals` is replaced by `### Statements`. `### Behavioral traits`
is unchanged. Per the no-backwards-compatibility rule in `AGENTS.md`, all seven
scenarios are migrated in the same change; the loader rejects the old section
name with a clear error rather than silently reading prose.

Two worked examples of deliberately different character – a party whose stakes
are public pledges, and a company whose stakes are mostly unannounced.

First,
`scenarios/swedish-government-formation-2026/background/actors/centre_party.md`
(long description unchanged, goals section rewritten):

```markdown
### Statements

- `no_sd_dependence` (commitment): We will not seek organised cooperation with
  the Sweden Democrats, and we will not support a government that is dependent
  on them – dependence, not membership, is the test.
- `no_v_in_cabinet` (commitment): We will not accept the Left Party in
  government. This is a veto on cabinet posts; it does not cover the Left
  Party voting a government through from outside.
- `price_the_abstention` (position): Convert our pivotal position into
  concrete policy concessions, particularly on tax and enterprise.
- `avoid_deadlock_blame` (position): Avoid being held responsible for a
  deadlock that ends in an extraordinary election.
- `constructive_centre` (identity): We are the constructive centre – the party
  that makes governance possible without joining blocs, not an obstacle.

### Behavioral traits

(unchanged)
```

Note what the tiers do here: the two vetoes are commitments – public, made to
voters, breakable only against a named development and at a narrated price. The
tactical goals are positions and can follow the negotiation freely. The
self-image is identity: the run where C becomes the party that *caused* the
extra election is a run where something categorical happened. And the design
answer to the scenario's own open question – which veto C breaks first – is now
produced by the mechanism instead of by unrecorded drift: breaking either
requires a trigger quotable from the turn, lands in the narrative, and is
counted in the artifacts.

Second, `scenarios/ai-2027-2/background/actors/openbrain.md` – a corporate
actor in a technology race, with no negotiation, no public pledges and no
discrete end state:

```markdown
### Statements

- `agi_first` (identity): Whoever builds AGI shapes the future; second place
  is irrelevant. We are building the most important technology in human
  history and must get there first.
- `capability_over_alignment` (commitment): Capability progress takes
  precedence over alignment work; alignment is a solvable-later problem. This
  is staked in hiring, compute allocation and internal culture, not in any
  public statement – our public rhetoric says otherwise.
- `resist_nationalization` (commitment): Resist government control,
  regulation or nationalization; concede on security and safety only as much
  as needed to keep the government out.
- `safety_forward_public_posture` (position): Publicly emphasize responsible
  development, alignment research and extensive testing.
- `outpace_deepcent` (position): Measure success by competitive lead over
  DeepCent; prioritize whatever preserves it.
```

This example is why the tiers are defined by stakes rather than publicity.
Nothing in the middle tier here was ever announced – reversing
`capability_over_alignment` costs OpenBrain a reorganization, researcher
attrition and lost race position, not votes – and the position-tier public
posture can swing freely without touching what the lab actually holds. It also
shows the ledger recording the gap between rhetoric and stance that the prose
description currently carries only as flavor: the public posture and the real
priority are separate statements at separate tiers, and a run where OpenBrain
genuinely converts to safety is a run where a *commitment* moved, with a
quotable trigger (an incident, a breach, a government ultimatum) in the
artifacts.

Validation (`validator.py`) extends naturally: unique ids per actor, valid
tiers, non-empty text, warn on an actor with zero statements, warn on a
commitment/identity statement that restates a constitution clause (it belongs
in one place, and that place wins).

## Why this does not reproduce the every-turn erosion

The claim has to be argued against the rules-evolution evidence
(`scenarios/swedish-government-formation-2026/design-notes.md`, "What the
Validation Runs Changed"; `scenario.yaml:62-71`), not asserted. Four
structural differences, each aimed at a specific feature of that failure:

1. **The rules step made re-emission mandatory; this design forbids it.** The
   rules prompt says "review and update", demands a version bump and a
   changelog of Added/Modified/Removed. The whole rule set flows back out
   through the model every turn, so every turn is an opportunity for drift,
   and an empty changelog reads as a task not done. The observed behaviour –
   one rewrite per turn, always the rule nearest the action – is the model
   filling the slot the format holds open. Here the ledger is never emitted by
   the model at all; Python copies it verbatim. The null action is *omitting a
   section*, which the system prompt explicitly names as a complete answer.
   There is no slot to fill.
2. **No numeric cap, because the evidence says caps become quotas.**
   `max_changes_per_turn: 1` behaved as "exactly one". This design contains no
   per-turn budget, cooldown or counter anywhere – nothing that describes an
   expected rate of change for the model to hit.
3. **The gate stops at relevance and never reaches merit.** A gate that asked
   "is this justification strong enough for this tier?" is an unbounded
   judgement: two referees will price the same reversal differently, and in a
   repeated batch that difference becomes variance in the results – re-importing
   what the mechanism exists to remove. The relevance check ("does this
   development bear on this statement, and where is it?") is bounded by the text
   in front of it.

   A caveat worth stating rather than hiding: the constraint-ledger evidence
   (4/4 agreement on factual controls, 7/28 divergence on interpretive rulings)
   does **not** straightforwardly license this split. Those cases were hard
   because the *source text* was ambiguous, and the two models had no shared
   situational context. A referee holding a concrete world state, a concrete
   trigger and a concrete statement is doing something easier. The relevance
   check is therefore expected to be tractable, but it is not proven stable by
   that experiment, and the eval below is what establishes it. What the evidence
   does support is the narrower claim that *merit* judgements diverge, which is
   why merit is not moved to the referee but into the world, via:
4. **Erosion was free; statement change is priced.** Rewriting a metric rule
   had no observer and no consequence inside the fiction – nothing pushed
   back. A commitment change here is part of the actor's visible turn output,
   is narrated by the GM, enters the world state every other actor reads next
   turn, and lands in the metrics – a broken veto moves trust and viability, a
   reversed strategic bet moves capability progress and organizational
   cohesion, whatever cost the scenario's metrics can express. The
   disincentive is the same one real actors face, produced by the same model
   that plays them, so it scales with model quality instead of with
   scaffolding.

What the design deliberately does **not** rely on: the model's restraint in the
abstract. Position-tier churn is allowed and expected – that is what positions
are for. The quantity to protect is commitment/identity-tier stability, and
that is protected by (1) no re-emission, (3) the trigger gate, and (4) pricing.

### The opposite failure: frozen actors

A gate can fail in the other direction – actors that never move, which is the
requirement-1 scenario (C opening to a rival premier in week 11 *must* be
reachable). Guards against over-tightening:

- The trigger check is satisfiable by any real development, including slow
  ones: "eleven weeks of deadlock and `pm_vote_failed` for the third time" is
  quotable from the world state. The gate blocks *ungrounded* change, not
  *late* change.
- Rejection is not punishment: a rejected proposal is recorded and the ledger
  carries forward; the actor can re-propose next turn when the trigger is
  real. No retry loop negotiates with the model about quality.
- The rollout below reads for both directions in the artifacts.

## Validation: single-variant rollout

**Scope decision (owner, 2026-08-23).** The framework is the object of this
work, not any particular scenario's results, and existing scenarios may be made
obsolete. That changes what validation is for. A controlled A/B/C comparison
answers "does this reduce cross-run variance in a distribution we intend to
defend" – a *scenario-credibility* question. The question actually being asked
is "does the mechanism behave sanely", which is an inspection, not a comparison.

**Therefore: build the full design, run it, read the artifacts.** No control
arms. The erosion pathology is loud enough to recognise without a baseline –
the documented failure was a change on nearly every turn, so a commitment-tier
change rate of roughly one in ten actor-turns is visibly not that.

**Accepted consequence, deliberately.** This repairs two wiring gaps at once,
statements and behavioral traits, and traits are not a small passenger: they
are vivid, characterful text ("Squeezed by its own logic", "Underestimates
centrifugal forces") that plausibly shifts actor behaviour on its own. Without
control arms, an observed behavioural shift cannot be attributed to one or the
other. For framework development that is an acceptable trade – both gaps want
fixing regardless – but it is a choice, not an oversight.

**Instruments.** Two scenarios of deliberately different character, because a
mechanism that works in a negotiation and wrecks a technology race is still a
failure and one scenario would not reveal it:

- **`swedish-government-formation-2026`** – negotiation, public pledges,
  discrete end state, seeded draws, a measured baseline pathology.
- **`ai-2027-2`** – technology race, corporate and state actors, mostly
  unannounced stakes, no discrete end state, continuous headline metrics.

**What to read in the artifacts.** Each of these is a stop-and-fix signal, not
a statistic to collect:

- **Change rate.** Commitment/identity-tier changes materially more often than
  ~1 turn in 10 per actor means the "no slot to fill" argument failed in
  practice, and the erosion pathology has returned under a new name.
- **Rejections, read by hand.** There will be few enough to read all of them.
  Real, bearing triggers being rejected means the gate is too tight; laundered
  ones being accepted means the relevance check is not holding.
- **Frozen actors.** Zero accepted commitment changes across a full batch,
  particularly late under high pressure, is the opposite failure and is not a
  success. The Centre Party abandoning a veto in week eleven must remain
  reachable.
- **Ledger coherence.** Diffs between consecutive turns empty unless a change
  was accepted; the ledger surviving `resume` and `branch`; no actor's ledger
  drifting from what its statements file records.
- **Cross-instrument disagreement.** Sane behaviour on the formation scenario
  and pathological behaviour on `ai-2027-2` means the design absorbed the
  texture of public pledges, and the fix belongs in the tier definitions or the
  default templates – not in the scenarios.

**If a distribution ever needs defending**, the controlled protocol is three
arms per instrument, same seeds and model and turn budget: **A** off (goals
re-derived from prose, no traits), **B** traits only, **C** traits +
statements – judging statements by C versus B, traits by B versus A, and
migration by A versus C. That is the right design for that question and is
recorded here so it need not be re-derived. It is explicitly not what this
rollout runs.

**Cheap pre-test before any batch.** A flat prompt-level eval in
`tests/evals/`, in the style of `event-conditions-flat`: fixed ledger + fixed
turn contexts, some quiet and some provocative, asserting (a) quiet turns
produce `No statement changes.`, (b) the provocation turn produces a grounded
proposal, (c) the relevance check passes real,
bearing triggers, rejects invented ones, and rejects laundered ones – a real
quote attached to a statement it does not bear on – across the candidate
referee models. This costs cents and catches a
non-viable prompt contract before run money is spent.

## Open questions

1. **Whether stake-based tier semantics hold in practice across actor types.**
   The definitions were written against the whole scenario population and the
   OpenBrain example works on paper, but whether a model *plays* "commitment"
   with the same restraint when the stake is unannounced (culture, sunk
   investment) as when it is a public pledge is untested – the diegetic price
   of a quiet reversal is less obvious, so erosion pressure may be higher
   there. The `ai-2027-2` instrument is the direct measure;
   before it, smoke-run 3–5 short runs on rewritten `ai-2027-2` or
   `ai-safety-race` actors. If a scenario needs tier glossing, the gloss
   belongs in that scenario's actor system-prompt override, not in the default
   template and not in Python.
2. **Referee model calibration on the relevance check.** This is now the
   sharpest open question, because relevance asks more of the referee than
   quotation did. The per-turn check runs on a cheap referee model many times
   per run. The flat eval below is the gate, and it must test the BEARS /
   UNRELATED axis specifically, including deliberately laundered proposals
   where the quote is real but bears on nothing. If cheap models cannot hold
   it, the fallbacks in order: route this one task to a better model (it is
   short and rare), or fall back to quotation-only plus GM pricing, accepting
   laundering as a residual again.
3. **Trigger-laundering (largely closed, not eliminated).** Every turn
   contains *some* development, and under a quotation-only check a model could
   attach a real-but-irrelevant trigger to a change it wanted anyway. The
   relevance check is aimed directly at this: an UNRELATED verdict rejects it.
   What remains is the harder case where a development is genuinely connected
   but trivially so – a thin thread rather than no thread. That is a merit
   judgement by another name, and it is deliberately left to GM pricing rather
   than to the gate. The residual is therefore narrower than before but not
   zero, and the change-rate measurement remains how it is detected.
4. **Behavioral traits are static in this design.** Wiring them into the
   prompt is included – it is a plain repair with no mechanism attached, and
   the rollout notes it as an uncontrolled co-change – but their
   *adjustability* is deliberately out of scope: "Squeezed by its own logic" is arguably a trait
   that should be able to intensify, yet traits are character, statements are
   record, and one new mechanism at a time. Revisit after the arm-B and arm-C
   evidence is in.
5. **Id hygiene for `add`.** Actors invent ids for new statements; normalize
   them the way emergent event ids are normalized (recorded as
   `id_normalized_from` when changed) rather than rejecting.
6. **Ledger vs narrative drift.** If the historical summary drifts away from
   the ledger, the ledger wins for the actor's own stances – same precedence
   pattern the fixed-background block already establishes in
   `templates/user-prompts/actor.md`. Stated in the template, not enforced in
   Python.

## Relation to requirements

1. One category, "statements", covering goals, values and stances – the tier,
   not the type, governs changeability.
2. Inertia as a small taxonomy (position / commitment / identity) rather than a
   bare number, argued above; general across scenario types because each tier
   names its own test.
3. Tier reclassification is a first-class proposal type, with downgrades
   requiring grounds at the current tier.
4. Absolutes stay in `constitution.md`, outside the ledger.
5. Changes are actor-initiated and reactive: nothing is pre-declared by the
   author, no event fires a change, and the actor proposes in reaction to
   developments it must be able to quote, and which must bear on what it is
   changing. The tension with the erosion evidence is resolved not by rationing
   the right to propose but by removing the format pressure to propose, gating
   on relevance instead of taste, and making the world – not the framework –
   charge for the change.
