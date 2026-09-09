# Language guidelines drawn from Europe 2031

[`europe2031.ai`](https://europe2031.ai/) – "What getting AI wrong means for us", by Daan Juijn, Stan van Baarsen, Judith Dada, Maximilian Negele, Lily Stelling, Philip Fox, Alex Petropoulos and Michiel Bakker. The full text is in [`../../source-material/What getting AI wrong means for us.md`](../../source-material/What%20getting%20AI%20wrong%20means%20for%20us.md). It is the document this scenario was seeded from, and `scenario.yaml` still names its central claim as the thing the metric design exists to keep testable.

These are guidelines for a telling, not for the scenario. They describe how that document gets its effects, and what carries over to material produced by simulation rather than by authorship. They govern `character-telling.md` and nothing else. (ECHO 2026-09-09)

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

## What carries over, and what has to change

Our material is not authored. It comes out of simulation runs, and that changes four things.

**Invented private actors are fine; invented public facts are not.** The source anonymises the labs into Atlas, Helios and Zimo at the point where it starts speculating, and says so in italics. We should do the same for anything the runs leave unnamed – a firm, a city, a person – while every event, measure, sum, member state and outcome must come from the run artifacts. A character may be invented whole. What happens to them may not.

**The characters are ours, not theirs.** Take the technique, not the cast. A Commission official with an American founder friend is *their* pairing, and reusing it would be imitation rather than derivation. Pick a vantage the run actually supports, and pick the foil the run's own material makes interesting.

**The narrator still knows only what the Union knows.** The interactive story's rule holds here for the same reason it holds there: this is a scenario, not a novel, and foreshadowing would let the telling assert things the simulation never produced. Europe 2031 obeys this too, almost everywhere – the reader learns about the compute crunch when Brussels does.

**Half-years, not months.** The runs resolve in six-month steps. Europe 2031 dates to the month because it was written that way; we cannot, without inventing precision the material does not carry. Seasons ("that autumn", "by the spring") are the honest equivalent and read almost as well, since a season sits inside a half-year rather than narrowing past it.

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
