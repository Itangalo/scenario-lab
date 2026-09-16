# Things to fix in the story tree

Standing list of known problems in the built tree that are worth correcting, kept separate from `README.md`'s "Known faults", which records faults accepted as they are. An entry here is something we intend to act on. Each entry says what is wrong, what the evidence is, which nodes are affected, and what the fix is and is not.

Re-running is not an option for anything already built: a Stage-1 node is parent to most of the tree, so every fix here has to be a change to the catalogue, to the prose, or to both, with the resulting prose/run drift noted under the "liberty with the record" rule.

## The rung below the frontier is missing when access is cut (ECHO 2026-09-16)

Status: identified, not yet scoped. Next session finds every affected passage; the rewrite comes after.

**What is wrong.** When the Union loses access to the leading model, the story goes straight from the frontier to European-hosted open models and to paper. It skips the rung that would actually catch the fall: the previous generation of the same commercial models, still on sale, still hosted in EU regions, and still far more capable than anything with open weights at that date. Being cut off from the frontier is treated as being cut off from the tier.

The real-world case is the one the event itself cites. When the United States restricted Fable and Mythos in the spring of 2025, the rest of the world still had Opus. Losing the top rung is not losing service.

**Where it comes from.** The root is the event catalogue, not the writing. `eu_frontier_access_denied` in `../events.md` contradicts its own referent: the condition is "What happened with Fable and Mythos in June 2026 happening again, on the same notice", while the description asserts that "the immediate practical effect lands on hospitals, ministries and firms that had built on it". The condition describes a model-specific withholding; the description describes an outage. The Game Master followed the description.

The jump is therefore already in the runs, not only in the prose. The world state behind `turn-03-A1` (`runs/run-20260910-223510/turn-03/4-world-state.md`) has access going dark, waiting lists stalling overnight, staff returning to paper forms, and the fallback going directly to models hosted in the Union. The prose transcribed it faithfully. This means the prose cannot be corrected without drifting from its run, and the drift has to be recorded where the next writer on the path will find it.

`turn-01/opening.md` is precise and is not affected: it has Washington ordering a laboratory to switch off "its most capable models", singular laboratory, lifted a fortnight later. The opening states the case correctly and the later turns escalate it.

**The 21 nodes where `eu_frontier_access_denied` fired.** Not all of them make the turn about it, and some already carry the right idea – `turn-13-P111` writes "Staff fall back on older EU-hosted systems and on paper", where "older" does the work on its own. Scoping means reading all of them and finding the passages that actually claim a cliff.

- Stage 1: `turn-02-A2`, `turn-02-V2`, `turn-03-A1`, `turn-04-P2`
- Stage 2: `turn-06-P11`, `turn-06-P12`, `turn-08-P21`, `turn-09-V11`
- Stage 3: `turn-10-V211`, `turn-10-V212`, `turn-11-P112`, `turn-11-V112`, `turn-12-A111`, `turn-12-A221`, `turn-12-P121`, `turn-12-P221`, `turn-12-V122`, `turn-13-A122`, `turn-13-P111`, `turn-13-P212`, `turn-13-V212`

`turn-03-A1` is the most exposed case and the one to judge the fix on.

**Everything downstream has to be checked.** This is the larger half of the job, and it is what makes the fix expensive rather than the rewriting itself. A cut-off is a thread, and later turns refer back to it – to what was lost, to what the Union had to build because of it, to what the fallback cost. Changing how the loss is told at a Stage-1 node changes what every later node on that path is allowed to assume. The counts, measured over the tree's own `next_node` and `next_choice` links:

| node | nodes downstream |
|---|---|
| `turn-02-A2` | 33 |
| `turn-02-V2` | 33 |
| `turn-03-A1` | 32 |
| `turn-04-P2` | 31 |
| `turn-06-P11`, `turn-06-P12` | 13 each |
| `turn-08-P21` | 11 |
| `turn-09-V11` | 10 |
| `turn-10-V211`, `turn-10-V212` | 3 each |
| `turn-11-P112`, `turn-11-V112` | 2 each |
| turn-12 nodes | 1 each |
| turn-13 nodes | 0 |

166 of the 207 nodes lie downstream of at least one affected node. That is a read-check, not a rewrite-count: most of those nodes never mention the cut-off again and need nothing. But they have to be read before that can be asserted, and the four Stage-1 nodes are where the cost sits – each of them carries about a third of the tree behind it.

`check_tree.py --continuity` helps here and is not sufficient. It walks all 24 reader paths and reports references to threads with no lead-up, but it matches in-world phrases, so it will catch a dangling reference and will not catch a later turn that still assumes the wrong severity. The reading is manual.

Practical order for the rewrite session: fix the catalogue first, then take the four Stage-1 nodes one at a time and walk each one's descendants before moving to the next, rather than rewriting all the affected passages and checking downstream afterwards.

**What the fix is.** Two parts, and the first stands on its own even if the prose is never touched.

1. Rewrite the description of `eu_frontier_access_denied` in `../events.md` so the frontier goes while the previous generation stays available, and so that what breaks is the validated deployment rather than the supply of capability. A triage assistant certified against one model does not fail over by swapping an API key: the clinical validation, the DPIA, the procurement and the accuracy thresholds are all model-specific. That yields paper for a fortnight on re-validation grounds, which is credible, instead of paper because nothing else exists, which is not. Any future rebuild of the tree inherits the corrected text.
2. A clause-level pass on the affected prose, naming what is actually lost and where most users actually land. This is not a rewrite of the arc, and it touches no figures. The sovereign build stays in the story; what changes is that it is no longer the only place to go.

**What the fix is not.** Not a re-run, and not a softening of the consequences. Paper triage stays where a run put it, the fallback programmes stay, every measure and every metric stays. The change is to what the Union lost, not to how badly it went.

**Why it is worth doing.** It makes the reader's dilemma harder rather than softer. If the fallback is last year's commercial model, still excellent and still sold, the case for spending billions on sovereign compute becomes much harder to make, and Sofia has to make it anyway against finance ministers who can point at a working system. As it stands the story hands her the argument for free. The catalogue already knows this and says so elsewhere: `election_alliance` has it that "the case for building its own capacity becomes much harder to fund once the pressure is off". The cut-off events currently keep that pressure artificially on.

**Open question for Johan.** Naming the substitute is adding a world fact rather than reordering one, which sits at the edge of the "liberty with the record" rule in `README.md`. The catalogue does leave the concrete form of this event open, which probably licenses it, but it is a call to make before the rewrite session rather than during it.

## Repeated events read as repetition within a branch (ECHO 2026-09-16)

Status: scanned, passages not yet read. The scan below says where to look; whether it actually reads as repetition is a judgement that needs the prose.

**What is wrong.** Events can repeat, and most of the catalogue's events do. Where the same event fires several times on one reader's path, the danger is that it is described the same way each time – the same cyber attack, the same evaluation finding, the same export-control tightening – so that a reader who is following one branch start to end feels the story circling rather than moving. The event catalogue gives one description per event, and both the runs and the prose drew on it every time it fired.

**Method.** Johan's, and it is the right one: walk the event list for each of the 24 story branches from start to end, note every event that fires more than once and in which turns, then read those turns and vary the descriptions so they do not repeat within the branch. The first half is mechanical and is done – the results are below. The second half is reading.

**The scan.** Walking all 24 reader paths over the `events` field in each node's `data.json`:

- Every one of the 24 branches has repeated events. The count per branch runs from 5 (`P111`, `P112`) to 11 (`A121`, `A122`, `A211`). The A branches are worst, the P branches mildest.
- The events that repeat on the most branches: `adoption_success`, `eval_anomaly_reports` and `cyber_major_incident` on 16 branches each, `bio_uplift_findings` on 15, `taiwan_tension_rise` and `member_state_defection` on 14, `openweight_frontier_release` and `eu_frontier_access_denied` on 12, `capability_jump` on 11, `loss_of_control_incident` on 10.
- Firing three or more times on a single branch is common: `cyber_major_incident` and `eval_anomaly_reports` do it on 9 branches each, `openweight_frontier_release` on 8.
- The worst individual cases, and the ones to read first: `cyber_major_incident` fires seven times on `V212` and on `V211`, `eval_anomaly_reports` seven times on `A222`, `export_control_escalation` six times on `P222`.

**Where it will hurt most.** The same event in two consecutive half-years, which is the case a reader cannot miss. Across the 24 branches this happens 21 times for `cyber_major_incident`, 13 for `eval_anomaly_reports`, 10 for `export_control_escalation`, 7 for `member_state_defection` and 6 for `cyber_defence_breakthrough`. Start here rather than with the highest totals: four cyber incidents spread over six years is a world, two in adjacent half-years told alike is a paragraph the reader has already read.

**What the fix is.** Prose only, node by node. Nothing in the runs changes and no figure moves. A repeated event needs a different concrete form each time it fires on a path – a different sector, a different member state, a different way in, a different thing that broke – and ideally an escalating or at least changing relationship to what the Union has already done about it. `README.md`'s "liberty with the record" rule covers this directly: where the event catalogue leaves the concrete form open, the writer chooses it. This is that, applied deliberately instead of by default.

**When an event repeats on the very next turn, say so.** Back-to-back recurrences are not to be disguised as unrelated incidents. The clipping names it as another one and then says what is new about it: "Another report of unexplained behaviour from AI models. Not only are they *X*, but now also *Y*." The recurrence is the news, and the reader should feel the ground moving rather than the story restating itself. Two of them told as if independent reads as an author who has lost count; told as a sequence it reads as escalation, which is what it is. This applies to the consecutive-turn cases listed above – `cyber_major_incident` 21 times across the branches, `eval_anomaly_reports` 13, `export_control_escalation` 10, `member_state_defection` 7, `cyber_defence_breakthrough` 6.

**Note on scope.** Variation is per branch, not per tree. The same event may be told the same way on two different branches, because no reader sees both. What matters is only that it does not repeat within one path from turn 1 to turn 13. That keeps the work bounded, and it means the shared early nodes – which sit on many paths – have to be varied against everything downstream of them rather than the other way round.

**Worth a script.** The scan is a dozen lines against the `events` field in `data.json` and the `next_node` / `next_choice` links. Committing it next to `check_tree.py` would make it repeatable, and would let the same walk report which of the repeats have already been varied once the rewriting starts.
