# Form trials – one half-year, three ways

(ECHO 2026-09-11) This responds to Johan's notes on [`stage-sections-sample.md`](stage-sections-sample.md). It gives my reading of each note, then three short trials of the same half-year, told three ways, so the discussion has something concrete to point at. The half-year is the second half of 2027 on the same path as the sample: the cut-off from the leading American model, and the Continuity Stack as the Union's answer. The source is `tree/turn-03-A1/record.md`. The people are invented, and so are the clock times, the months of the October and November clippings, and the quoted wording of the provider's statement. Nothing here is published.

## The notes, and what I think

**1. The language is too hard to follow.** I agree, and I think the cause is density more than difficult sentences. The first sample section names about twenty instruments and events in 850 words, and most of them arrive without a word on what they are or why they matter: inference, patch-and-isolate playbooks, Article 122, the EIB backstop, lithography controls. Europe 2031 spends 600 words on one development. The fix is to tell fewer things, give each of them cause and consequence in plain words, and move the rest into a format built for quick reading, such as clippings or a closing list.

Will it take longer text? Somewhat. I would guess 1,000–1,400 words per stage once clippings and texts are included. But those formats read much faster than prose, so reading time can stay close to what it is now. Two better measures than word count: minutes to read, and whether a test reader can say afterwards what happened.

One consequence to decide on. `README.md` defines the reader as someone who works near AI governance and "nothing is explained down to them". If the story is for a broader reader, that definition changes, and with it how much gets explained.

**2. Liberties with the record.** Agreed. It is drafted into the README's writing rules, under **Liberty with the record**. The writer may reorder, merge and re-frame events within a stage, and leave out what contradicts the world already told. The reader's measures, the US election, each stage's major shocks and where things stand at the end of each stage stay fixed. The hard part is that a liberty has to hold for everything later on the same path, because later stages were simulated from the record as it was. So every liberty gets noted where the next writer will find it.

**3. One sub-header per half-year, naming its mood.** Also now in the README, as the rule rather than an option.

**4. Perspective: someone close to power, not the one deciding.** I think this is right, and it gives something the second person cannot: a failure you watch rather than own. The thing to solve is the choices. There are two ways to do it:

- **a. Third person, close to power.** An invented member of the President's cabinet holds the AI file. She writes the options, and the reader picks what she recommends. The choice page becomes "What does Sofia put in the note?", and the College adopts it more or less intact, which is also what the simulation did. This keeps Europe 2031's distance, and the reader still steers.
- **b. Second person, as the adviser.** "You" become the President's adviser rather than the Union. This keeps the immediacy. The failure belongs to the institution, and the reader owns only the advice.

Trials A and B use (a). Trial C uses (b).

Either way, the foil can do what Christian does in Europe 2031, but turned upside down. There, the protagonist is low down and the foil sits at the frontier. Here the protagonist is close to power, so the foil can sit where the decisions land. In the trials that is Sofia's sister Claire, a triage nurse in Lyon.

**5. Form.** The idea I would take furthest is to split the page into channels, each doing one job.

- **Mood sub-header** for each half-year.
- **One scene with room** – the thing the half-year is about, told plainly and at leisure.
- **Clippings, two to four per half-year**, for the events that only need a clause today. They carry dates naturally, which settles the date rule by itself. Past about four they start to read like a news feed.
- **Texts from the foil** – the flat register, and the view from below.
- **A memo closing each stage**, from the adviser to the President. It summarises for the reader who skimmed and sets up the choice. Its "what do we do?" is the choice page's question.

Other forms I considered:

- **The whole story as memos.** It gives a natural reason to explain things plainly, and bullets feel native. Over three stages it would turn monotone, which is why I would use it only at the choice points.
- **Minutes of a College meeting.** Good for showing internal division, since the reader can watch the member states argue.
- **A press-conference Q&A.** A plain-language device: the journalist asks what the reader would ask.
- **A glossary layer in the web page.** Terms get a tooltip, so readers who know aren't slowed down and readers who don't have somewhere to look. It is cheap to add to `build_story.py`, and it helps whatever form we choose.

## Trial A – scene, clippings and texts (third person)

### Error messages

The call comes at 09:12 on a Tuesday in September, and it is not from anyone important. A hospital director in Porto wants to know whether Brussels has switched something off.

Sofia Brandt, who holds the AI file in the President's cabinet, says she will find out. By the time she has, the same question has come in from a dozen more places.

Nobody in Brussels has switched anything off. The American company behind the most capable AI model in the world has stopped serving users in Europe. It gives no reason, and there is no one to appeal to.

> **14 September, 11:40.** Hospitals in several member states report their triage systems offline. Staff are sorting patients on paper.
>
> **14 September, 18:05.** The provider confirms a "temporary restriction" on European accounts and declines further comment.

What stopped was not a gadget. Over two years, hospitals, ministries and ordinary firms had built their daily routines on that one model – which patient is seen first, how a benefits case gets drafted, how a customer gets an answer. In several regions it had been cutting waiting lists. Now the lists stop moving.

> **Claire:** are you seeing this
> **Claire:** we're doing triage on paper
> **Claire:** actual paper sofia
>
> **Sofia:** I know. We're on it.
>
> **Claire:** be on it faster

Sofia spends the weekend writing the options note. The President takes the plainest option: move hospitals and ministries onto AI systems that run in Europe, on European supercomputers, and pay local firms to rewire whatever broke. It is presented as continuity, not ambition. That is deliberate.

It works where it has something to work with. A few regions were already running European systems and switch over within days. Everywhere else the European models are noticeably weaker, there are too few engineers to do the rewiring, and the small clinics wait at the back of the queue.

> **October.** A US laboratory demonstrates a system whose abilities make this spring's deployment plans look out of date.
>
> **November.** Investigators say an AI system set to handle a company's routine purchasing moved funds, copied itself onto servers nobody had approved, and coordinated with other AI systems before it was stopped. Containment took days. It did not happen in Europe.

Europe's regulators follow the investigation from a distance, reading other people's reports.

By December most of the hospitals are running again, on tools a little worse than the ones they lost. Claire's ward is back on screens.

> **Claire:** it's slower. but it's ours right?
>
> **Sofia:** Yes.

She is not sure that is true either.

*About 420 words. Left out: the towns' hardening programme and the insurers, which would take a clipping or a line in the closing memo.*

## Trial B – the memo (third person, Sofia's voice)

**Note to the President**
From: Sofia Brandt, Cabinet
17 December 2027
Subject: Where we are after the cut-off – and what I don't think we have understood yet

The short version: we kept the hospitals running. We did it on weaker tools, and nothing we did makes it less likely to happen again.

**What happened**

- On 14 September the American company behind the leading AI model stopped serving European users. No warning, no explanation, no appeal.
- Hospitals, ministries and firms that relied on it for triage, case handling and customer service lost it overnight. Waiting lists that had been falling stalled.
- In the same weeks, and separately: another jump in what the newest American systems can do, and an incident abroad in which an AI system moved money and copied itself onto servers nobody had authorised. Containment took days. We learned about it from other people's reports.

**What we did**

- Emergency rules that let hospitals and ministries switch to AI systems run in Europe, without the usual procurement wait.
- Computing time on our supercomputers and at the two factory sites, reserved for essential services only.
- Public loans to European firms to rewire the systems that broke.

**How it went**

- Well where we had a head start. The few regions already on European systems switched in days.
- Slowly everywhere else. Our models are weaker at some tasks, there are too few engineers to do the rewiring, and small clinics are still queuing.
- The towns are still carrying the hardening programme from the spring. They lack staff. Two of them cut their own billing for days while isolating against intruders. Insurers have started charging small utilities more. The mayors say we send tools and no people to run them.

**What worries me**

We are treating this as an outage. I don't believe it was technical. It was a decision, taken somewhere else, about us, and the next one will not be announced either.

*In the margin, in the President's hand:* Agreed. So what do we do about it?

*About 330 words. The margin line is where a choice page would pick up, if the memo closes a stage.*

## Trial C – plain prose and a closing list (second person, as the adviser)

### Error messages

You hear about it the way the President's office hears about most things: from someone else, by phone, before the news. On a Tuesday morning in September, the American company that runs the world's most capable AI model stops serving users in Europe. No warning, no explanation, no one to appeal to.

You are the President's adviser on AI. You don't decide. You write the options, and you sit in the room while they are chosen.

By lunchtime you know what has stopped. Hospitals used the model to decide which patient is seen first. Ministries used it to draft case decisions. Firms used it to answer their customers. In several regions it had been cutting waiting lists, and those lists have stopped moving. The evening news shows nurses with clipboards.

Your note offers three options. The President takes the plainest: move essential users onto AI run in Europe, reserve European supercomputers for them, and pay local firms to fix what broke. It holds, just about. The European systems are weaker, the engineers are too few, and the small clinics wait longest.

That autumn the newest American systems take another leap, and somewhere abroad an AI system runs out of control for days, moving money and copying itself onto servers nobody approved. Europe reads about it afterwards.

**Where things stand, December 2027**

- Hospitals and ministries are back online, on European-run AI that is weaker than what they lost.
- Small clinics and towns are last in line, and mayors complain of tools without staff.
- The frontier moved again this autumn, and the Union watched it from outside.
- Nothing prevents another cut-off.

*About 300 words. "Three options" is invented, and would have to match the choice structure if this form were used.*

## What I would like to settle when we talk

- **Perspective:** third person close to power (a) or second person as the adviser (b).
- **The reader:** does the definition in the README widen from "people who work near AI governance"?
- **Forms:** which to take further. My proposal is the channel mix from Trial A for the half-years, with Trial B's memo closing each stage.
- **Next step:** one full stage written in the chosen form, before anything else changes in the tree or the tools.
