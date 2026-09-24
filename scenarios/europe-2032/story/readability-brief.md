# Readability brief (ECHO 2026-09-24)

A reader found the story demanding: too much has to be known or remembered to follow it. This brief governs a pass that lowers that demand without making the story longer or thinner. It is written for the agents that read, edit and verify, and it is the thing Johan approves before any of them run.

## The reader to write for

Someone who reads the news, but does not follow EU affairs or AI policy. They know what the EU, the Commission, a data centre and a hospital are. They do not know what ENISA, a "cabinet", "inference", "the frontier" or "an envelope" are, and they do not remember a measure's name from three sections back.

## What to fix, in order

1. Institutions and acronyms that are not explained where the reader first meets them on their path (ENISA, EIB, HERA, EuroHPC, the Council formations, DGs). Explain once, briefly, at the first mention on the path, and never again.
2. Jargon from AI, policy or finance: "failover", "envelopes", "inference", "near-frontier", "anchored supply", "tiered access". Replace it with plain words, or explain it in a few words.
3. Measures named but not explained. On first mention, say what the measure does before or instead of its full name. After that, use a short handle ("the Shield", "the pact"). When a measure comes back after several sections, add a few words of reminder ("the Shield, the programme hardening hospitals and grids").
4. Noun-chain officialese: sentences whose subject is a programme and whose verb is administrative ("X circulates draft options for Y with possible targets on Z"). Rewrite them with people doing things.
5. References that lean on something several sections back: "the contest", "the capital", "the site". Add the two or three words that bring it back.
6. Where the prose means one of the dials, use the dial's words: "political capital", "resilience", "sovereignty", "public sentiment". The panel then explains the prose, and the prose explains the panel.

## What must not change

- Length: substitute rather than add. Net growth per node at most 5%. Most edits should be length-neutral; cutting is welcome.
- Facts: nothing added, nothing dropped. No new figures – `check_tree.py`'s numbers rule applies, as do the calendar rules in `README.md` (no "turns", no "half-years" as such).
- Voice: the text messages with Claire, the dated event lines, the notes to the President, the section headings and the dry register stay as they are. Plainer is not chattier.
- Comments (`<!-- -->`), front matter and the `record.md` and `data.json` files are not touched.

## Calibration

Two samples, edited by this brief. Word counts are for the passage shown.

### turn-01, the running programmes (88 → 99 words)

Before:

> Two programmes were already running when Sofia took the file. The InvestAI gigafactories: twenty billion euros, from a wider two-hundred-billion investment drive, for four to five sites. The tech sovereignty package, a separate effort: a target of another two hundred billion euros in private money for AI data centres by 2036, and zones where permits come faster. Both tie up the Commission's standing for as long as they run – funding, legal cover and member-state backing that stay committed until they land – and neither will finish soon.

After:

> Two programmes were already running when Sofia took the file. The first, InvestAI, puts twenty billion euros into four or five "gigafactories" – giant AI data centres – as part of a wider two-hundred-billion investment drive. The second, the tech sovereignty package, aims to draw another two hundred billion euros of private money into AI data centres by 2036, with zones where permits come faster. Both tie up the Commission's political capital for as long as they run – money, legal cover and member-state backing that stay committed until the work is done – and neither will finish soon.

This passage grows by eleven words (point 3: "gigafactory" is used throughout and never explained). That is about 1% of turn-01; an edit elsewhere in the node can pay it back. "Political capital" is the dial (point 6).

### turn-03-P1, whole-node sample (paragraphs that change: 192 → 205 words)

Before:

> The priority stays with the Shield. A small ENISA-led team follows up with the hospitals and municipal utilities that failed the spring drills, funded by limited reallocation from existing envelopes. Finance and telecoms stay solid. With staff stretched across the gigafactories, the Shield follow-up and a new procurement effort, only a handful of hospitals pass a re-test on failover. Many smaller operators do not: staff turnover undoes the training, restores still take too long, and interior ministries complain that the paperwork is outpacing the engineers.

After:

> The priority stays with the Shield, the programme to harden hospitals, grids and networks. A small team from ENISA follows up with the hospitals and municipal utilities that failed the spring drills, paid for by shifting money within existing budgets. Banks and telecoms stay solid. With staff stretched across the gigafactories, the Shield and a new procurement effort, only a handful of hospitals pass a re-test of switching to backup systems. Many smaller operators do not: staff turnover undoes the training, recovery after an attack still takes too long, and interior ministries complain that the paperwork is outpacing the engineers.

Before:

> The contest between the three capitals hardens.

After:

> The contest between three capitals over where the gigafactories go hardens.

Before:

> Sofia's new measure is the smallest she can make it. Under the EU Public Benefit AI Deployment, officials draft options for AI tools hosted in the EU that could help hospitals sort patients, speed up permits and tutor pupils, perhaps with targets for shorter waiting times and faster permit decisions.

After:

> Sofia's new measure is the smallest she can make it. Officials are to work out how AI tools run on European servers could help hospitals sort patients, speed up permits and tutor pupils – and how much shorter the waiting times could get.

Before:

> But no contracts are launched and no new money is committed; the services are asked to cost the options and report back, and the work stays preparatory, slowed by the same shortage of staff.

After:

> But no contracts are signed and no new money is committed; the departments are asked what the options would cost, and the work stays on paper, slowed by the same shortage of staff.

Before:

> The capitals count the continuing outflows to factories not yet sited and hardening not yet finished.

After:

> The capitals count the money still flowing to factories without a site and hardening that is not finished.

Net for the node: thirteen words, about 3% of its 460, inside the 5% limit. The measure's official name (EU Public Benefit AI Deployment) is dropped because what it does is what the reader needs; no later node on the P1 branch uses the name.

