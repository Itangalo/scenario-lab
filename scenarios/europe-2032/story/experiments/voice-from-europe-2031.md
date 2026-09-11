# Language guidelines drawn from Europe 2031

[`europe2031.ai`](https://europe2031.ai/) – "What getting AI wrong means for us", by Daan Juijn, Stan van Baarsen, Judith Dada, Maximilian Negele, Lily Stelling, Philip Fox, Alex Petropoulos and Michiel Bakker. The full text is in [`../../source-material/What getting AI wrong means for us.md`](../../source-material/What%20getting%20AI%20wrong%20means%20for%20us.md). It is the document this scenario was seeded from, and `scenario.yaml` still names its central claim as the thing the metric design exists to keep testable.

These are guidelines for a telling, not for the scenario. They describe how that document gets its effects, and what carries over to material produced by simulation rather than by authorship. They were written for `character-telling.md`, and since 2026-09-11 they also govern the story tree's prose, adapted as set out under *Applied to the story tree* below. (ECHO 2026-09-11)

## What the source actually does

Europe 2031 is 18 500 words covering January 2025 to March 2031, with a 2034 epilogue. Roughly the first half is real history told as narrative; the speculative part starts at a marked break, and the break is announced in italics rather than smuggled. It is worth separating what makes it readable from what makes it *believable*, because they are different techniques and only one of them is about prose.

### It watches from below, not from the chair

The protagonist is a mid-level official at DG TRADE who is never in the room where anything is decided, and in the one scene where she is near the room, she is in the corridor. She writes a memo about building leverage in 2026; her director calls it "a thoughtful contribution" and promises to pass it up the chain; two years later, when the thing she warned about happens, she thinks about his friendly face. That is the engine of the whole document. The reader is not asked to identify with power. They are asked to identify with someone who can see what is coming and cannot make it matter.

This is the single biggest departure from our interactive story, where the reader *is* the Union and every half-year is theirs to spend. Both are legitimate. They are not compatible in the same telling.

### The foil says the thing the institution will not

A second character – an old friend who founded a company in San Francisco – exists almost entirely in chat logs. He is not a device for exposition. He is a device for *register*: he can say "it's fucked up" and "that's more than every european ai company combined ever raised" in a document whose other voice is careful. Every uncomfortable truth the narrative needs stated flatly gets stated by him, so the narration never has to editorialise.

The two voices are typographically distinct and consistently so. He is lowercase, unpunctuated, several messages in a row, no capital letters even on proper nouns. She replies in full sentences with terminal punctuation, usually one line, often just "I know." The contrast does characterisation with zero description.

### Numbers are rhetoric, not evidence

The figures are chosen for the ratio they express, and placed so the ratio lands: "The largest AI supercomputer in the US runs at 1,250 megawatts. The largest in Europe runs at eighty-three." Two sentences, no comment. Elsewhere: a funding round "twenty times smaller", then later "150 times smaller", so the reader feels the trend without being told there is one. Nothing is rounded into vagueness and nothing is piled up. One or two numbers per scene, load-bearing.

### The analytic move is ironic juxtaposition

"In Brussels, civil servants are banned from using frontier AI tools to draft memos; in Washington, they're being used to plan military operations." The document almost never argues. It puts two facts next to each other in one sentence and lets the reader do the work. This is also how it handles its own thesis: rather than claim Europe is dependent, it shows a bank engineer copying files onto a personal laptop because the sovereign tool is worse, and adds "Everyone knows this is happening, but no one says it out loud."

### It explains without condescending

The Foreign Direct Product Rule, EUV lithography, what model weights are, why a scratchpad mattered – each gets a clause or a sentence, in the flow, never a box-out and never an apology. The test it seems to apply: a reader who already knows should not feel slowed down, and a reader who does not should not have to look anything up.

### Institutions have psychology

Rooms are polite. "The room moves on." Doubts are "left unsaid". Elites are "tired of negativity". Nobody is a villain and nothing is stupid; things fail because a plausible institutional incentive pointed the wrong way. This is what keeps a decline story from reading as contempt, and it is the hardest thing on this list to imitate.

### Scenes have bodies in them

Coffee at Place du Luxembourg. A tie loosened. Hands shaking at a sink, and a slice of Washington sky through a high window. The macro material – sovereign spreads, export controls – is anchored roughly once a chapter to something physical, and once to something domestic: her brother, unemployed, moved back in with their parents. The private consequence is never the point of the scene and always the thing the reader remembers.

### Sections end on a hard flat line

"Christian: it's a lagging indicator." "She suspects it will not." "Nobody is quite sure what the strategy is." No summing up, no signalling that a beat has landed. The last sentence is usually short and usually declarative.

## How long the sections are (ECHO 2026-09-11)

Measured on the full text in `source-material/`: 18 513 words in 23 sections, each headed by a month and a title.

| part | sections | words per section | median |
|---|---|---|---|
| real history, January 2025 – June 2026 | 8 | 358–1 044 | 549 |
| scenario, August 2026 – August 2030 | 13 | 381–832 | 615 |
| climax, "March 2031 – Between giants" | 1 | 1 832 | – |
| epilogue, "June 2034 – Project Inheritance" | 1 | 3 131 | – |

The ordinary section is about 600 words and almost never passes 850. Leaving out the two exceptions, the median is 614 and the mean 627. Only two sections break the pattern, and both do something no other section does: the climax is the one extended scene in the document, and the epilogue is a short story of its own, set three years later. The length is a budget the document keeps, not an average it drifts around.

Inside an ordinary section there are 3–14 paragraphs of narration (median 9), plus 0–13 lines of chat. The narrative paragraphs are long, 66 words on average, and the chat lines are what make the page feel quick. Sentences average 17 words, a little shorter in the scenario part (16.6) than in the history part (17.6).

Each section is pinned to one month, and usually to one development, with a few months of background folded in. It can run to 600 words because it tells one thing.

What this means for the story tree:

- One section per stage, aimed at 600–850 words, with a ceiling of about 1,000. This replaces the old budget of 250 words per turn, which came to 1,000 per stage, so the new aim is 15–40 per cent shorter – and a stage covers two years, where a Europe 2031 section covers a month.
- The compression has to come from selection, not from tighter sentences. `merged-blocks-tight.md` already found that the 2031–2032 blocks give up named actors before they give up words. Each section therefore needs one through-line, and events off it get a clause rather than a scene.
- A section may run to the ceiling when its events need the room – a war and a strike with casualties take more space than a stalled permit. None should borrow the climax's length: 2032 is where the scenario stops, not a finale.

## What carries over, and what has to change

Our material is not authored. It comes out of simulation runs, and that changes four things.

**Invented private actors are fine; invented public facts are not.** The source anonymises the labs into Atlas, Helios and Zimo at the point where it starts speculating, and says so in italics. We should do the same for anything the runs leave unnamed – a firm, a city, a person – while every event, measure, sum, member state and outcome must come from the run artifacts. A character may be invented whole. What happens to them may not.

**The characters are ours, not theirs.** Take the technique, not the cast. A Commission official with an American founder friend is *their* pairing, and reusing it would be imitation rather than derivation. Pick a vantage the run actually supports, and pick the foil the run's own material makes interesting.

**The narrator still knows only what the Union knows.** The interactive story's rule holds here for the same reason it holds there: this is a scenario, not a novel, and foreshadowing would let the telling assert things the simulation never produced. Europe 2031 obeys this too, almost everywhere – the reader learns about the compute crunch when Brussels does.

**Dates, marked now and then.** (ECHO 2026-09-11) Europe 2031 heads every section with a month, and the reader always knows when they are. Ours should too, now and then precisely: "in March 2028", "during the summer of 2031", "by the spring". A section opens with a time anchor, and so does each subsection that moves the calendar on. A named month must lie inside the half-year the run resolves in, and where the run's own world state names a month – many do ("In September, access … went dark") – that month is used. For an extreme event, an exact date and even a clock time signal significance: "At 03:40 on 11 March 2032, missiles meant for someone else's war come down on European soil." That precision is invented, the way a private character is, and it is spent sparingly: at most once per section, and only on something the reader should feel as a before and after. This replaces the earlier rule, which allowed seasons but no months.

## Applied to the story tree (ECHO 2026-09-11)

The interactive story keeps its settled rules from [`../README.md`](../README.md), and two of them pull against the source. What carries over and what changes:

- **Close to power, not below it.** (Revised 2026-09-11, after `form-trials.md`, where Trial A was chosen.) The story follows Sofia Brandt in the President's cabinet. She writes the options, and the reader's choice is her recommendation. Europe 2031 watches from the corridor; we watch from the room, without the vote.
- **The foil sits below, not at the frontier.** Europe 2031 sets its protagonist low and her foil at the frontier. We invert that: Claire, a triage nurse in Lyon, texts from where the decisions land. Her register is short and lowercase, and Sofia's is full sentences, often one line. Voices quoted out of the world state ("healing by permission", "burial money") still serve as the flat register in clippings.
- **Channels.** Each half-year gets a mood sub-header, one scene with room, two to four dated clippings, and texts where they earn their place. Clippings carry the events that need only a clause, and they carry the dates.
- **Present tense**, as in the source.
- **Everything else carries over:** numbers used sparingly and for the ratio they express, juxtaposition instead of argument, a term explained in a clause, institutions with psychology, a physical and a domestic detail, and sections that end on a short declarative line.
- **Sub-headers are allowed** and need not carry dates. The page header already gives the two years.

## The rules, compressed

For anyone writing or judging a telling in this voice:

- Third person, present tense, close on one person who is not in charge.
- One foil in chat logs, typographically distinct, who says what the narration cannot.
- Two numbers a scene at most, chosen for the ratio they express, placed without comment.
- Argue by putting two facts in one sentence, not by explaining what they mean together.
- Explain a term in a clause, never a box-out.
- No villains. Every failure gets a plausible institutional reason.
- One physical detail and one domestic consequence per chapter, neither of them the point.
- End each section on a short declarative line.
- Everything public comes from the runs. Everything private may be invented, and is.
- No arm names, no branch ids, no metric names or dial values, no turn numbers – the standing rules from [`../README.md`](../README.md) still apply to anything a reader sees.
- (ECHO 2026-09-11) A time anchor at the start of each section, and of each subsection that moves the calendar on. Months inside the run's half-year. At most one exact date and time per section, kept for an extreme event.
- (ECHO 2026-09-11) In the story tree, one section per stage: 600–850 words, ceiling about 1,000.
