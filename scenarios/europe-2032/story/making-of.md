# Why and how Europe 2032 was built

Europe 2032 was built as an assignment for the Talos Network fellowship. The idea started on 25 August and went through three major iterations, homing in on the concept and then improving the execution. The scenario was published one month later, and handed in on 30 September.

The simulations behind the scenario were run with [Scenario Lab](https://github.com/Itangalo/scenario-lab), a project I've been working on for almost a year. The code is written entirely by AI agents. Scenario Lab, too, has been through some major iterations, and more are on their way.

The prose for Europe 2032 was not generated with Scenario Lab – the framework builds simulation data with functional narratives, not long prose. The prose was written with Claude Code and Opus, and though I've put some time into finding a good style and improving the prose, it is still painfully obvious that it is LLM-written. I consider the simulations the main part of Europe 2032, and the scenario texts a way to present the concept of LLM-powered scenario simulations.

## The first iteration: three underlying realities

The seed for Europe 2032 came from an idea of simulating how a global policymaker should act when facing deep uncertainty over how AI progress will continue. Some say that we are in the foothills of the singularity, expecting recursively self-improving AI and then AGI (possibly ASI) within 5–10 years. Some stubborn people say that AI will hit a wall. (This stance arguably has a poor track record looking at the past ten years, but still shouldn't be excluded as I see it.) The current state of the technology suggests that AI is becoming superhuman at least in coding, mathematics and probably other domains where we can have [verifiable rewards](https://www.reinforcement-learning.com/kb/rlvr).

There is really no way of telling which of these forecasts are right, and they probably call for radically different policies. I wanted to see if there are actions that policymakers can take that pay off reasonably well over all three underlying worlds, either by always being beneficial or by only having low costs in some and high yield in others.

I chose to create a scenario with one single actor, even if Scenario Lab is built to manage many. I don't really remember why. Maybe I was already planning for creating a choose-your-own-adventure story built on the scenario, maybe I wanted to reduce complexity, or maybe I felt that from a European perspective a single vague policymaker is the realistic option (compared to deciding the course for US government, the Chinese communist party or frontier labs).

I prompted Scenario Lab to create a new scenario based on a plain-text description containing some directions:

- A scenario for exploring the effects of AI policies
- A single global policy-setting actor, deliberately nameless
- 18 half-year long turns, starting July 2026
- A wide variety of possible events, with some specific examples to show the breadth

The scenario builder then got to work. After some initial analysis it suggested a few research questions, some metrics for tracking the world in numbers, and a name for the scenario. I discussed them with the scenario builder, and gave ok after some tweaks. It then generated the first version of the scenario, gathering information as it needed in the process. The scenario got the name **Forking Futures**.

I didn't spend much time auditing the scenario. The point was to get something up and running, to play with and learn from.

> [!note]- The research questions
> 
> 1. rq_favourable_profile: Which event patterns and measure portfolios mark the best outcomes in each arm, and which of them recur across all three arms? This is the favourable half of scenario discovery. Anything that recurs across all three arms is a candidate for the next question.
> 2. rq_no_regret: Are there measures, or combinations of measures, that stay above the acceptability floors in every arm, rather than paying off strongly in one? Finding no such package counts as a real result.
> 3. rq_proactive_vs_reactive: Does acting ahead of time pay off compared with reacting after an incident of the same class has happened? The notes carry a caveat: constitutional rule 6 hard-codes that acting early always costs more political capital, so the cost side is built into the scenario. What isn't built in is whether the payoff outweighs that cost over 18 turns.
> 4. rq_adverse_profile: Which event patterns and measure portfolios mark the worst outcomes in each arm, and which recur across all three arms? This mirrors question 1, and the notes say the contrast between the two tells you more than either alone.

> [!note]- The metrics
>
> ## us_capability
> **Description:** Capability of the strongest closed US frontier systems, measured as general problem-solving competence across economically and strategically relevant tasks. Accumulated capability; it does not fall back.
> **ID:** us_capability
> **Min:** 0
> **Max:** 100
> **Unit:** index
> **Start value:** 45
> **Reference points:**
> - 30: Strong assistant. Reliable on well-specified tasks, needs supervision on anything long-horizon.
> - 45: Mid-2026. Executes multi-hour software and research tasks with a competent human checking the output. Clearly superhuman in narrow domains, clearly not in general.
> - 60: Reliably completes multi-day professional projects end to end. Displaces junior work in several sectors rather than assisting it.
> - 75: Matches strong domain experts across most cognitive professions. Materially accelerates the research that produces its own successors.
> - 90: Broadly superhuman. Sets research agendas rather than executing them; human oversight is nominal on anything technical.
> - 100: Decisively superhuman across every measured domain.
> 
> ## cn_capability
> **Description:** Capability of the strongest Chinese frontier systems, on the same scale as us_capability. Accumulated; it does not fall back.
> **ID:** cn_capability
> **Min:** 0
> **Max:** 100
> **Unit:** index
> **Start value:** 38
> **Reference points:**
> - 30: Strong assistant, roughly a year behind the US frontier.
> - 38: Mid-2026. Behind on the very frontier, ahead on deployment breadth and cost, closing on domestic compute.
> - 50: Parity on most deployed applications, still behind on the largest training runs.
> - 70: At the frontier. No reliable capability argument remains for treating the US as the sole source of the strongest systems.
> - 90: Broadly superhuman.
> 
> ## openweight_gap
> **Description:** How far the best openly released model weights sit behind the strongest closed frontier model. High means dangerous capability is concentrated in a few auditable organisations; low means it is everywhere and unrecallable.
> **ID:** openweight_gap
> **Min:** 0
> **Max:** 100
> **Unit:** index
> **Start value:** 30
> **Reference points:**
> - 0: Open weights are at the frontier. Every capability the frontier has is on a laptop somewhere, permanently, and no release control means anything.
> - 15: Roughly six months behind. Restrictions bite for one model generation and then evaporate.
> - 30: Mid-2026. Around a year to eighteen months behind on general capability, closer than that in code.
> - 55: Two to three years behind. Frontier-only risks are genuinely governable through the closed labs.
> - 80: A wide structural gap; frontier capability requires compute and know-how no open release comes near.
> 
> ## incident_pressure
> **Description:** Current level of realised and near-miss harm from AI systems — cyber, bio, infrastructure, large-scale fraud — as it registers on decision-makers. Rises with incidents, falls as preparedness and defensive capacity absorb them.
> **ID:** incident_pressure
> **Min:** 0
> **Max:** 100
> **Unit:** index
> **Start value:** 20
> **Reference points:**
> - 10: Isolated misuse, handled by ordinary law enforcement. No political salience.
> - 20: Mid-2026. Recurring model-assisted cybercrime and fraud, several serious near-misses documented, nothing that has broken through as a crisis.
> - 40: A significant incident with real casualties or a major sector disrupted. AI harm becomes a standing agenda item rather than a foresight topic.
> - 60: Repeated large incidents, or one severe enough that emergency powers are used. Emergency legislation passes in weeks rather than years.
> - 85: Sustained crisis. Attribution is uncertain, defences are visibly behind, and normal policy-making has stopped.
> 
> ## regulatory_capacity
> **Description:** The regulator's combined political capital, institutional bandwidth and technical competence — how much it can push at once and how credibly. Rises with visible successes and with capacity-building measures that have landed; falls with failures, with overreach, and with every measure still under implementation.
> **ID:** regulatory_capacity
> **Min:** 0
> **Max:** 100
> **Unit:** index
> **Start value:** 50
> **Reference points:**
> - 15: Discredited or exhausted. Nothing new can be started; existing measures decay unenforced.
> - 30: Can sustain one measure at a time, and only if it is uncontroversial.
> - 50: Mid-2026. Real legal instruments, thin technical capacity, contested legitimacy. Two or three measures can run at once before something slips.
> - 70: Trusted and competent. Can carry several parallel measures and be taken seriously outside its own jurisdiction.
> - 90: The reference authority on AI governance. Its standards are adopted elsewhere because they are the standards, not because of market access.
> 
> ## economic_context
> **Description:** The AI investment climate: capital availability, valuations, and the willingness of governments to accept costs on AI development. High means an expansionary boom in which restriction is politically expensive; low means a bust in which capability growth slows on its own and safety arguments get cheaper.
> **ID:** economic_context
> **Min:** 0
> **Max:** 100
> **Unit:** index
> **Start value:** 65
> **Reference points:**
> - 15: Deep AI-sector bust. Capital has fled, build-out has stopped, and restrictions cost nothing because nobody is expanding.
> - 35: Correction. Funding is selective, the weakest labs are gone, growth continues at the two or three best-capitalised.
> - 65: Mid-2026. Abundant but nervous capital; datacentre build-out at record scale; open argument about whether revenues justify it.
> - 85: Full boom. Any measure that slows deployment is attacked as economic self-harm and usually loses.
> 
> ## public_sentiment_to_ai
> **Description:** How AI is regarded and accepted by the public in the regulator's own constituencies. Feeds political capital in both directions: high acceptance makes restriction expensive, low acceptance makes adoption and infrastructure expensive.
> **ID:** public_sentiment_to_ai
> **Min:** 0
> **Max:** 100
> **Unit:** index
> **Start value:** 42
> **Reference points:**
> - 15: Broad hostility. Protest action against AI infrastructure is regular and occasionally physical; boycotts bite; visible job losses in named sectors dominate local news; politicians run openly anti-AI and win on it.
> - 30: Anxious and sceptical. Job losses and fraud dominate coverage; trust in AI-mediated information is low; the first organised protests target datacentre siting and AI products, mostly petitions and hearings rather than streets.
> - 42: Mid-2026. Ambivalent. Widely used, widely resented, sharply divided by age and sector.
> - 60: Broadly positive. Visible public benefit, tolerable disruption; restriction requires an argument.
> - 80: Enthusiastic. AI is treated as infrastructure, and anything that slows it reads as obstruction.

I wanted a really wide variety of possible events, so I made sure that the game master was allowed to invent new ("emergent") events and then ran a number of simulations. I then asked Claude Code to insert emergent events it found useful to the canonical list of events. This gave [a list of 33 events](https://github.com/Itangalo/scenario-lab/blob/main/scenarios/forking-futures/events.md).

Then it was the question of the three underlying realities. Scenario Lab already had support for creating variants of scenarios, overriding parts of the scenario configuration. This had to be expanded, to allow changing "metric rules" (how world metrics evolve) and event data. The code for Scenario Lab was promptly (ha) updated to allow more overrides in more generic ways.

After running some simulations I wanted to give the game master more freedom to explore the space of possibilities. I tried tweaking some of the prompts used in the scenario by adding the following at the end: "Use first principles. Be brief." [It didn't work.](https://github.com/Itangalo/scenario-lab/blob/main/scenarios/forking-futures/design-notes.md#what-the-first-principles-prompt-test-showed-6-branches-27-august-echo-2026-08-27)


## The second iteration: a branching story

Only one or two days after creating Forking Futures, Europe 2032 was born.

In discussions with my advisor, I came up with the idea of an interactive scenario story and wanted to try it out. The old scenario was cloned and modified. The nameless policymaker became the EU, [world metrics](https://github.com/Itangalo/scenario-lab/blob/main/scenarios/europe-2032/metrics.md) were changed to make sense for an EU actor, and probably a few other things changed as well.

But the main work was building and exploring how to build a branching story.

I wanted the actions available for the reader to be based on emerging patterns in a group of simulations. Also, I wanted every path in the story to have a number of parallel worlds to compare from, where the reader made the same choice but other things happened.

Scenario Lab already supported branching – new simulations starting from a specific simulated turn rather than from scratch – so the need for new functionality wasn't *that* big. It still turned out that some new functionality was needed. For example, functionality for injecting a certain actor choice had to be built, allowing parallel simulations of what happens if an actor decides to do the same thing (instead of allowing different decisions every time).

This code was made pretty quickly. It turned out that keeping tabs on what the EU was doing was more difficult.

### Keeping track of spending

The scenario was set up to allow the EU to implement new measures related to AI: building AI infrastructure, starting re-skilling programs, investing in AI expertise, hardening cybersecurity, implementing bio risk screening programs, and whatnot. In normal scenarios (whatever that is), the actions are implemented right away. But these measures take time to finish, which means there's a need for keeping track of them over several rounds.

Scenario Lab has functionality for keeping track of external events, but not so much when it comes to actor choices. They are recorded to logs, but there's no way to programmatically pull old actions into the information available to the game master.

Scenario Lab allows overriding and tweaking the prompts used in different parts of the simulations. The list of running measures was kept alive by simply asking the game master to repeat the measures that were not yet finished, along with how long they had left. This list was then used to tell how much "political capital" the EU lost each turn – the currency for policy actions in the simulation. The game master should also check the newly finished (and sometimes ongoing) measures and adjust the world accordingly: some measures increase resilience, some buy sovereignty, some affect AI safety levels, and so on. Finished and ongoing measures also give a bonus to political capital whenever incidents occur that are mitigated by the measures.

Simply put, there was quite a bit to keep track of for the game master, but it worked reasonably well.

To tune the metric rules, and the cost and effects of events, I had Claude Code build a visualizer for metric and events over batches of simulations. A number of batches later, I felt that the scenario worked well enough. It was never meant to be a well-calibrated simulation of reality – it was a showcase for how LLM-powered scenario games can work.

I particularly remember inspecting some simulations, and finding a run where AI capability became flat. The game master can step in and change most things if deemed necessary, but the rules said that AI capability increases more or less every turn. I had to ask Claude Code to explain this. Paraphrasing:

"Hey Claude Code, why is AI capability more or less flat in run 6302?"

"Let's see… Look at the event record: export_control_escalation at turn 6, supply_chain_coercion at 7, ai_investment_collapse at 8, taiwan_blockade at 10, export_control_escalation again at 12."

What looked like an error was actually the game master directing the game in a sensible way.

### Building the tree and the prose

I decided to give the reader a choice every second year, corresponding to four turns, with all stories starting from the same first turn. Branching every turn would be more fun, but would result in thousands of stories. Switching to two-year turns was an option, but would have required rewriting a lot of scenario configuration, since probabilities and world metrics were tuned to six-month turns.

Interleaved with tuning the scenario settings, I started running batches of parts of the scenario, to use for the branching story. Ten simulations of the first turn, and selecting *one* that should be the starting point of all stories. Running ten simulations for each underlying world starting from `turn-01`, and analyzing them to see how actor choices cluster. Pinning down the choices that should be available to the reader, then running ten simulations of turn 2–5 for each underlying world, and drawing one randomly that becomes the actual story. Then creating reader options for each of these branches, and so on and so forth. One starting point, twenty-four endings.

I prompted Claude Code for these simulations one at a time, which meant that it took quite some time to create all of them – I think it was roughly a week (but much less actual simulation time).

Since I was eager to start building the story tree, I had to tear it down several times when I made significant changes to how the simulations worked. I think it is called "learning". (I also learned to `caffeinate`.)

With the actual simulations in place, it was time to write the prose. Or to have Claude Opus write the prose, that is, because there was no way that I could write all that text in the time available for the assignment. (I might also add that I have a job in parallel to the fellowship.)

I experimented with some different writing styles, and at this stage I'm pretty sure I settled on a style that was described by me, not by Opus. It was functional. Kind of.

The actual writing took some time, but in general went smoothly. Claude Code custom-wrote a script for turning prose snippets into full stories, and the stories into an html page that could be published.

## The third iteration: clean-up and architectural improvements

Then on September 9 I found a problem.

The system for keeping track of the measures proposed by the EU was too elaborate, and in 4–5 percent of the cases the game master simply failed to add a new measure to the list it should keep track of. In 0.6 percent of the cases the game master also dropped measures from the list, for no good reason.

Half of the time for the assignment had passed. What I had was a decent proof of concept, but an error rate of five percent is borderline to unacceptable even for a proof of concept. I had a few ideas of how I could improve both Scenario Lab and this particular scenario. But I wasn't sure that it would work, and if I got stuck on bugs and new errors, there was a real risk I wouldn't have time to fix them. And I would have to rerun all the simulations. The alternative was to spend my time re-running only the branches with errors, which I knew I could do with the time I had left.

I decided to push ahead with updates, but make it possible to quickly revert to the old kind-of-functioning state.

A number of real improvements were made:

- I went through [the scenario event list](https://github.com/Itangalo/scenario-lab/blob/main/scenarios/europe-2032/events.md) and made a lot of cleanup. Events that didn't really contribute to the scenario were removed, three catastrophic events were added, and probabilities for a lot of events were adjusted.
- I introduced [sign-off documents](https://github.com/Itangalo/scenario-lab/tree/main/scenarios/europe-2032/sign-off) for scenarios; documents showing a sample of actual prompts being sent to LLMs, to make it easy to see if information was missing or written in confusing ways.
- I switched to using Muse Spark as the LLM for Europe 2032, instead of a Qwen model. Muse Spark is a reasoning model, which makes a number of differences, and in total the switch turned out to increase fidelity, only cost slightly more and – most importantly – make simulations run faster.
- Scenario Lab got a ledger for persistent storage, along with some basic syntax to add/remove/modify entries from prompts, as well as to read full lines, individual values, or aggregates of values (eg. sum, max/min and average).

The ledger was a significant architectural change, and the most risky. Making Scenario Lab use a ledger is a pretty bold procedure, and on top of that the Europe 2032 scenario had to be converted to use the ledger properly. It took some manual work on top of the amazing work by Claude Code and OpenCode, but it actually worked.

The ledger is actually worth a few more lines, since Scenario Lab is built with a core philosophy "lean into LLM". The point of using LLMs in scenario games is to use their fuzzy logic and imperfect assessments as an asset, instead of trying to describe rules and relationships in traditional code. Traditional code is faster and more reliable, but you can't emulate a credible actor with traditional code outside very formalized games. So why introduce a ledger instead of leaning into the LLM power?

There are two good answers. The first one is that the functionality I was after wasn't a part of what LLMs are good at. I wanted persistent lists and reliable arithmetic – two things where LLMs are clearly inferior to traditional code. The second one is that me trying to push this into LLM prompts made them *worse* at the things I actually wanted them for. The prompts had become cluttered with formulas for adding the number of running policy measures, reminders to *subtract* and not add political capital if there is a prioritized measure, and so on. The things that the LLMs were actually needed for were pushed away.

Anyway, the refactoring worked. And on top of that, re-running the simulations for the story tree went much smoother than the first time. Instead of spending a week on it, it was done overnight. The 150 start-to-end simulations used as reference points were also much quicker. Within two days I was back on track, and in a much better position.

### The prose

The final layer was writing the prose. Or, again, having Opus write it.

There were several iterations, and I don't remember all of them. But I remember some things.

- I asked Opus to analyze the writing style for Europe 2031, and also suggest some alternatives. The winner was a combination.
- I did a lot of reading, found a number of factual errors and other inconsistencies, that Opus cleaned up.
- At more than one point there were full sweeps over all story branches, to improve readability and consistency. That all story branches overlap to a small or large degree makes that kind of editing extra tricky and resource consuming.
- Pretty late in the process I decided to end the stories whenever catastrophic events occurred. The turns after catastrophic events didn't reflect the radical changes in the world (since the scenario wasn't built for that), and ending on the catastrophic event also allowed for a much more dramatic and vivid story.
- The changes with catastrophic ends also made me change two story branches. The original distribution made *all* branches in the world with rapid acceleration end on catastrophic events, and none of the branches in the other worlds. This was kind of the wrong message, and also not really representative of the distribution in the 150 independent runs, so I re-selected stories from the existing runs to remove one catastrophic event from the acceleration world and add one to another.

The prose is still the weakest point in Europe 2032, and sometimes I feel it would be better if the raw narration found under "simulation data" was displayed instead of LLM prose that often works, sometimes flies, but too often feels clunky and hard to process. And sometimes I think it would be much easier to have acceptable LLM-written prose if there were single threads from start to end, where Opus isn't forced to write one piece at a time and then stitch them together.

Then again, this is a way to showcase Scenario Lab, and LLM-powered scenario games in general. Not an attempt at literary prizes.

## What I learned

- Building the first versions just to learn and start over is after all these years still a good approach.
- Spending time on finding time-saving methods is often time well spent, in particular when AI is included.
- Claude Code and OpenCode are really powerful tools.
- Scenario Lab improves when LLM capability improves. This is good.
- Building particular scenarios with particular needs is a good way to add new functionality to Scenario Lab, but it should be done in a way that is generic, not specific. I have a long list of improvements I want to do.
- The simulations show no clear winner moves when it comes to EU AI policy. (See the "findings" tab for more information.)
- It is difficult to make LLMs write good prose, in particular when it can't be written start-to-end.
- Creating LLM-powered scenario games is fun, and there is *much* more to explore in how to use them.

I want to thank my advisor Auriane Técourt for feedback and encouragement, and also fellowship peers for valuable input.
