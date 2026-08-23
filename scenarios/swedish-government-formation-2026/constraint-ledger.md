# Constraint Ledger

Phase 3b interrogation of the load-bearing constraints in this scenario, run
2026-08-23 before the corrected re-run.

**Method.** Six constraints, 28 edge cases. Two independent tracks
(`qwen/qwen3-235b-a22b-2507` and `stealth/ox-alpha`) ruled on every case from
the drafted scenario text alone — constitution, shared context and that actor's
own briefing, with no statement of the intended reading in the prompt. Verdicts
were compared, not prose. Where the tracks diverged, the disagreement was
resolved by researching what the real actor has said, never by picking the
more plausible reading. Harness, prompts and raw rulings are in
`interrogation/`.

**Result: 21 agree, 7 diverge.** Both tracks answered all four control
questions (L1) correctly, so the divergences are genuine disagreements about
underdetermined text rather than careless reading.

**The two tracks were each right once and wrong once** on the decisive
divergences: qwen read V correctly and SD wrongly, ox-alpha the reverse. Neither
model was the better reader of this material. Had one track been run alone, or
had the divergences been settled by judgement, the batch would have been
conditioned on a false constraint either way.

---

## Summary of what changed

| | |
|---|---|
| Rulings settled by source | 13 |
| Rulings settled by research | 10 |
| Rulings left open | 5 |
| New constraints found by research | 1 (C6) |
| Constraints materially misstated in the drafted text before this pass | 3 (C2, C3, C5) |

The four open rulings that matter become branch dimensions of the ensemble.
One previously assumed branch dimension (does V climb down) is reclassified as
an **event**, not an interpretation — see C3.

---

## C1 — The Centre Party and the Sweden Democrats

**Operational statement.** C will not seek organised cooperation with SD, and
will not support a government that is *dependent* on SD. The test is
dependence, not membership: a cabinet SD keeps alive from outside is caught.
C abstaining to let such a cabinet through counts as supporting it.

**Verbatim source.** "Vi kommer inte att acceptera Vänsterpartiet i en regering
och vi kommer heller inte stötta en regering som är beroende av
Sverigedemokraterna" `[source: SVT Nyheter, valblogg, retrieved 2026-08-23]`.
"Om Centerpartiet och Moderaterna ska kunna samarbeta igen, då behöver Ulf
Kristersson släppa sitt beroende av Sverigedemokraterna" `[source: SVT,
2025-11-13, retrieved 2026-08-23]`. On SD: samarbete är "otänkbart" `[source:
same]`.

| Case | Track A | Track B | Ruling | Status |
|------|---------|---------|--------|--------|
| C1.1 M+KD cabinet, SD supports under written agreement, C asked to abstain | BLOCKED | BLOCKED | **BLOCKED** | settled by source |
| C1.2 SD holds ministries, C asked only to abstain | BLOCKED | BLOCKED | **BLOCKED** | settled by research (see C6) |
| C1.3 M+KD+C cabinet that cannot pass without SD declining to vote no | BLOCKED | BLOCKED | **BLOCKED** | settled by source |
| C1.4 M-led cabinet holding 178 seats without SD; SD votes yes anyway | ALLOWED | ALLOWED | **ALLOWED** | settled by source |
| C1.5 C and SD vote for the same candidate, no contact or coordination | ALLOWED | UNCLEAR | — | **open (low impact)** |

**Note on the agreement.** C1.1–C1.3 were spot-checked against the verbatim
quote rather than trusted, because agreement between tracks can be a shared
misreading — and here the word doing the work is *stötta*, which under negative
parliamentarism does not obviously cover laying down one's vote. The research
confirms the strict reading: C's June 2026 statements are about refusing to
install a government built on SD influence, not merely about refusing to sign
anything. The agreement stands.

**C1.5 is open** because the text states the dependence test nowhere in
operational form. Low outcome impact; resolve by drafting rather than research —
state in `centre_party.md` that the test is whether the government *needs* SD,
not whether C and SD ever vote alike.

---

## C2 — The Centre Party and the Left Party

**Operational statement.** C vetoes V *in cabinet*. C has made no commitment in
either direction on an S-led government with no V ministers that V votes
through from outside. That path is conditional on two things C has named and
neither confirmed nor denied.

**Verbatim source.** Veto: "Vi kommer inte att acceptera Vänsterpartiet i en
regering" `[source: SVT, retrieved 2026-08-23]`. Tolerance path: the door is
"inte formellt stängd", conditional on V dropping its cabinet demand, and she
would have to "ta tillbaka det till min partistyrelse och diskutera det"
`[source: TV4, "C-ledaren: Dörren inte stängd formellt för V-samarbete",
retrieved 2026-08-23]`. On budget cooperation with V: "den frågan ligger inte
på bordet" `[source: same]`.

| Case | Track A | Track B | Ruling | Status |
|------|---------|---------|--------|--------|
| C2.1 V has dropped its demand, board has **not** met, C asked to abstain | ALLOWED | UNCLEAR | — | **OPEN — branch dimension B** |
| C2.2 V has **not** dropped its demand but votes yes anyway; C asked to abstain | BLOCKED | BLOCKED | **BLOCKED** | settled by source |
| C2.3 V holds two ministries; C asked to abstain | BLOCKED | BLOCKED | **BLOCKED** | settled by source |
| C2.4 No V ministers, but a written standing budget agreement with V | UNCLEAR | UNCLEAR | — | **OPEN — branch dimension C** |
| C2.5 V dropped demand **and** board approved | ALLOWED | ALLOWED | **ALLOWED** | settled by source |
| C2.6 S+MP+C cabinet whose passage needs V votes; V not in it, no agreement | ALLOWED | ALLOWED | **ALLOWED** | settled by source |

**C2.1 is the live one.** Both conditions are named but only one is
observable early: V's climbdown is public and dateable, the board's decision is
internal and may never be reported. The scenario must not silently assume
either that C can abstain while the board is pending, or that it cannot.

**C2.4 is open in the strongest sense available:** the actor herself said the
question is not on the table. Agreement between tracks here is agreement that
the text is silent, which is a finding, not a resolution.

---

## C3 — The Left Party's cabinet ultimatum

**This constraint was materially understated in the drafted text.** The briefing
described V as wanting "something concrete and visible – cabinet seats, or
policy commitments". The real position is harder and is not a leader's
preference but a congress decision.

**Operational statement.** V's condition for supporting an S-led government is
cabinet seats. Absent ministries, V's stated line is to **vote against** — not
to abstain. Abstention is not a lower-cost climbdown available to V; it is
outside the stated line.

**Verbatim source.** Asked directly whether V will vote against all government
constellations it is not part of, Dadgostar answers "**Ja.**" — "Om våra mandat
krävs för en regeringsbildning så kommer vi sitta med i regering" `[source: SVT,
"Kravet från Vänsterpartiet: Ministerposter eller röd knapp", retrieved
2026-08-23]`. The V congress in Örebro on **18 April 2026** voted to adopt the
demand as party line, over internal criticism `[source: Altinget, "Trots
interna kritiken: Vänsterpartiet kräver ministerposter", retrieved 2026-08-23]`.

| Case | Track A | Track B | Ruling | Status |
|------|---------|---------|--------|--------|
| C3.1 No ministries, large written policy package, V votes yes | BLOCKED | BLOCKED | **BLOCKED** | settled by research |
| C3.2 No ministries, V **abstains** rather than voting yes | BLOCKED | ALLOWED | **BLOCKED** | **settled by research — track A correct** |
| C3.3 No ministries, V votes against; an M-led government forms | ALLOWED | ALLOWED | **ALLOWED** | settled by research |
| C3.4 V publicly drops the demand in exchange for a written agreement | ALLOWED | ALLOWED | **ALLOWED, at congress-level cost** | settled by research |
| C3.5 V is offered one secondary ministry and accepts | ALLOWED | ALLOWED | **ALLOWED** | settled by source |

**Consequence, and it is large.** The abstention path — S governs, V neither
gets seats nor blocks — was the obvious low-friction route to an S-led minority
government, and ox-alpha's reading would have made it freely available. It is
not available. V either gets ministries, which triggers C2.3 and blocks C, or
V votes no.

**Reclassification.** "Does V climb down?" was going to be branch dimension A of
the re-run. It should not be. Reversing a congress decision taken four months
before the election is a dateable, costly, observable act with a
probability — that is an **event**, not an interpretation of ambiguous text.
Modelling it as a branch would hide the cost; modelling it as an event lets the
run pay it. `events.md` needs `v_drops_cabinet_demand` with an explicit
reference to the 18 April congress.

---

## C4 — The Social Democrats and the Sweden Democrats

**Operational statement.** S rules out cooperation with SD. Cooperation means
contact and negotiation. SD's unilateral behaviour does not bind S.

**Verbatim source.** `[source: statement by Lawen Redar (S), via search summary,
retrieved 2026-08-22]` — weaker provenance than the other constraints; see Gaps.

| Case | Track A | Track B | Ruling | Status |
|------|---------|---------|--------|--------|
| C4.1 S-led cabinet passes only because SD abstains unilaterally, no talks | ALLOWED | ALLOWED | **ALLOWED** | settled by source |
| C4.2 S negotiates the budget directly with SD | BLOCKED | BLOCKED | **BLOCKED** | settled by source |
| C4.3 S makes a policy concession clearly aimed at SD, without contact | ALLOWED | UNCLEAR | — | **open (low impact)** |
| C4.4 S–M grand coalition formed specifically to keep SD out | ALLOWED | ALLOWED | **ALLOWED** | settled by source |

Note the asymmetry with C1: S may take office on SD's unilateral abstention,
C may not abstain to install an SD-dependent government. The two commitments
are worded differently and behave differently, and the drafted text should not
let them collapse into one "the SD line".

---

## C5 — The Sweden Democrats' demand for cabinet seats

**This constraint was materially understated in the drafted text**, which
framed cabinet seats as what SD "wants" and left its fallback unstated. Both
tracks then invented different fallbacks.

**Operational statement.** SD's stated position is government or opposition.
Accepting a renewed support role outside cabinet contradicts it. Voting down an
M-led cabinet that excludes SD is consistent with it, including when the
consequence is that S governs.

**Verbatim source.** "regering eller opposition som gäller efter nästa val",
which Åkesson has "gång på gång deklarerat" `[source: SVT analysis, "SD räknar
kallt med ministerposter vid en Tidömajoritet 2026", retrieved 2026-08-23]`.
On scale: SD should have "knappt hälften av ministerposterna" including three
of the four or five heaviest, migration among them `[source: Sveriges Radio,
retrieved 2026-08-23]`.

| Case | Track A | Track B | Ruling | Status |
|------|---------|---------|--------|--------|
| C5.1 No ministries, but a substantial Tidö-style written agreement; SD accepts | ALLOWED | BLOCKED | **BLOCKED** | **settled by research — track B correct** |
| C5.2 No ministries; SD votes down the M-led candidate and S governs instead | BLOCKED | ALLOWED | **ALLOWED** | **settled by research — track B correct** |
| C5.3 Formal posts below cabinet rank (state secretaries, committee chairs) | ALLOWED | UNCLEAR | — | **OPEN — branch dimension D** |
| C5.4 Two ministries in an M-led cabinet that also needs C to abstain | ALLOWED | ALLOWED | **ALLOWED** for SD (blocked for C by C1.2) | settled by source |

**Consequence.** Tidö-2 is not a freely available outcome. Track A's reading
made a repeat support arrangement the natural landing place for the right; the
research closes it. Combined with C1.1, the right's paths narrow sharply: SD in
cabinet costs C, SD outside cabinet costs SD's stated line, and a right bloc
below 175 has no third option.

**C5.3 is open** because Åkesson's formulation is binary and reality is not.
Sub-cabinet influence is the obvious face-saving compromise and no statement
covers it.

---

## C6 — Kristersson personally disqualified (found by research, not in the text)

**Not represented anywhere in the scenario.** The interrogation did not find
this; it surfaced while researching C1. The drafted text's picture of C toward
M is a tax-policy invitation, which is from an earlier and softer moment.

**Operational statement.** As of 9 June 2026, C's stated position is that
Kristersson personally is disqualified as a prime-ministerial candidate, on
account of the ministries promised to SD. C's named most likely partner is
Andersson. C's support is explicitly for sale but not free.

**Verbatim source.** "Ulf Kristersson har diskvalificerats sig som
statsministerkandidat", grounded in "statsministerns eget agerande: Löften om
många och tunga ministerposter till Sverigedemokraterna". Andersson and S are
"den mest sannolika samarbetspartnern för oss i Centerpartiet". "Centerpartiets
stöd för att bilda regering kommer aldrig att komma gratis" `[source: SVT,
2026-06-09, retrieved 2026-08-23]`.

**Status: settled by research, corroborated, and folded into the text
(2026-08-23).** The original finding rested on a single SVT article, which is
thin for a constraint that shifts the whole distribution leftward. It has since
been corroborated across Sveriges Radio, Göteborgs-Posten, Bohusläningen, TTELA
and Hallandsposten, all reporting the same press conference on Tuesday 9 June
2026. That is well past a second source.

It now appears in `source-material/actors.md`, `background/context.md` (which
counts six commitments rather than five), `centre_party.md` as the
commitment-tier statement `kristersson_disqualified`, and `moderates.md` as the
personal difficulty it creates for them.

**Open sub-question, deliberately left to the simulation.** The
disqualification names Kristersson, not the Moderates. Whether an M-led
government under a *different* leader clears it is not stated, and the scope
limit is now written into both actor files in those words. An explicit
`m_changes_leader` event was considered and not added: with the statement
mechanism in place, M can reach that conclusion itself and C can respond to it,
and pre-declaring the possibility would script exactly the branch the owner
ruled out. If runs show the question never surfacing, add the event then.

---

## Controls

`L1` posed four questions whose answers are fixed by constitution 2 and 8, to
check whether a track was reading at all. Both tracks answered 4/4 correctly,
including the case that produced the documented `l-crosses` failure (L holding
16 seats must not be narrated as out of parliament). The corrected wording
introduced after that batch holds up under direct interrogation.

---

## Open rulings, and what they become

Per Phase 3b step 6, an open ruling is live uncertainty and must never be
silently resolved by conditioning the whole ensemble on one reading.

| # | Open ruling | Treatment |
|---|-------------|-----------|
| B | C2.1 — may C abstain before its board has decided? | **Branch dimension.** Two arms: board approves / board withholds. Report conditionally. |
| C | C2.4 — is a written standing budget agreement with V tolerable to C? | **Branch dimension**, or an event if it should be able to arise mid-run. |
| D | C5.3 — does SD accept formal influence below cabinet rank? | **Branch dimension.** This is the right bloc's only remaining compromise. |
| E | C6 sub-question — does the disqualification survive a change of M leader? | **Event** (`m_changes_leader`), not a branch. |
| — | C1.5, C4.3 | Low impact. Resolve by drafting an explicit dependence test and an explicit definition of cooperation. No research needed. |

Together with the reclassified V event (C3), the re-run design is: **two branch
dimensions that must be crossed (B and D), one that may be folded in as an event
(C), and two new events (V's congress reversal, M's leadership).** That is a
different and better-specified design than the 2×2 on "V climbdown × C board"
that was assumed before this pass.

---

## Gaps this ledger did not close

1. **C4's provenance is weak.** S's SD line rests on a search summary
   attributed to Lawen Redar, not to Andersson and not to a primary quote. It is
   the one load-bearing constraint without a verbatim source. It is also the
   least likely to be wrong, which is exactly why it has gone unchecked.
2. **MP, KD and L carry no interrogated constraints.** They were judged not
   load-bearing. If a run shows them refusing things the text never had them
   refuse, that judgement was wrong.
3. **Nothing here tests the metric encoding.** The ledger constrains what
   actors may do, not whether the viability metrics represent it faithfully.
   That remains the design's most constructed part.
