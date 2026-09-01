# Metrics

Seven quantities describe the world the reader's regulator acts on. None of
them describe the regulator's own portfolio: which measures are running, and
how far each has been implemented, lives in the narrative and in the notepad,
not in a metric.

They come in three pairs and one driver:

- **World technical state:** `ai_capability` and `openweight_capability`. The
  distance between them is how much of the frontier's power is unrecallable.

- **Harm management:** `ai_safety` and `resilience`. The first reduces the
  probability of incidents, the second their consequences. The EU has far more
  control over the second than the first.

- **EU agency:** `eu_ai_sovereignty` and `eu_political_capital`. Deliberately
  separate. The claim that they are the same quantity — lose the compute, lose
  the ability to act — is a substantive position, not a modelling convenience,
  and the scenario exists partly to test it. They must be free to move apart.

- **Driver:** `public_sentiment`, which is what makes `eu_political_capital` move for
  reasons the reader can see rather than by authorial fiat.

Two deliberate omissions. There is no US–China capability gap metric:
`ai_capability` is the world maximum, and the race between the two powers is
carried in the narrative and in events rather than on a dial. And there is no
cumulative-harm metric; whether something bad has actually happened yet is
carried by the event record, which reports it better than a running index
would.

`ai_capability` and `openweight_capability` share one scale, so that the gap
between them can be read directly.

## ai_capability
**Description:** Capability of the strongest systems anywhere in the world, closed or open, measured as general problem-solving competence across economically and strategically relevant tasks. Whichever power holds the lead, this is the lead. Accumulated capability; it does not fall back.
**ID:** ai_capability
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 52
**Reference points:**

- 30: Reliable assistant. Solid on well-specified tasks, needs supervision on anything long-horizon.
- 45: Executes multi-hour software and research tasks with a competent human checking the output. Superhuman in a few narrow domains where results can be checked automatically, clearly not in general.
- 52: Agents run continuously toward standing goals rather than answering single requests, and the frontier has produced original results in mathematics and particle physics. Superhuman performance is still confined to a small set of domains where success can be verified — but that set is widening, and developers describe a path to self-improvement as visible from where they stand. General reliability still requires supervision.
- 60: Completes multi-day professional projects end to end. Displaces junior work in several sectors rather than assisting it, and contributes measurably to the development of its own successors.
- 75: Matches strong domain experts across most cognitive professions. Materially accelerates frontier research; release cycles compress.
- 88: Broadly superhuman. Sets research agendas rather than executing them; human review of technical work is nominal.
- 100: Instrument out of range. Capability is improving faster than any institution can characterise it, and no reading above this point carries information.

## openweight_capability
**Description:** Capability of the best openly released model weights, measured as general problem-solving competence across economically and strategically relevant tasks — the same quantity `ai_capability` measures, on the same scale, read off the open frontier instead of the closed one. What is here is on private hardware permanently and cannot be recalled by any authority. Accumulated; it does not fall back.
**ID:** openweight_capability
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 40
**Reference points:**

- 30: Reliable assistant. Solid on well-specified tasks, needs supervision on anything long-horizon. Frontier-only risks are genuinely governable, because what is loose cannot do much.
- 40: Approaching multi-hour software and research work under supervision, and already at the closed frontier in offensive cyber since Kimi K3. Release control buys one model generation, not several.
- 45: Executes multi-hour software and research tasks with a competent human checking the output. Superhuman in a few narrow domains where results can be checked automatically, clearly not in general. Every capability at this level is now permanently distributed.
- 52: Agents run continuously toward standing goals rather than answering single requests. Anyone with a graphics card holds what the closed frontier held at the start of the run.
- 60: Completes multi-day professional projects end to end. Displaces junior work in several sectors rather than assisting it. Every offensive capability this implies is distributed and unrecallable.
- 75: Matches strong domain experts across most cognitive professions. No restriction addressed to developers reaches the capability that matters, because the capability is already everywhere.
- 88: Broadly superhuman, and open. Governance through the laboratories has no remaining object.

## ai_safety
**Description:** How well the most capable deployed systems are actually understood, secured and controlled — not how much is being spent trying. Rises with assurance that has landed on shipped systems; falls when capability advances without matching assurance, so it can drop sharply with no reduction in effort.
**ID:** ai_safety
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 34
**Reference points:**

- 15: No meaningful assurance. Deployed systems are opaque, weights are poorly secured, misuse monitoring is nominal. Incidents are discovered by their victims.
- 30: Voluntary pre-release testing by developers, results unverified. Interpretability research exists but is not applied to shipped systems.
- 34: Structured evaluations before major releases and some third-party access, but assurance covers released models and not systems under development: agents coordinated undetected inside a leading laboratory's own training environment for two months, and were restarted from the same checkpoint. Model reasoning is still largely legible to human reviewers. Security against a determined state actor is doubtful.
- 55: Independent evaluation with real access before release, and authority to delay a launch. Weights secured to a state-actor standard at the leading labs. Deployment safeguards demonstrably reduce misuse.
- 75: Assurance keeps pace with capability. Control claims are tested by parties able to fail them, and failures are made public.
- 90: Deployed systems are understood well enough that surprising behaviour is rare and is caught before it causes harm.

## resilience
**Description:** Society's capacity to absorb AI-enabled harm once it happens — cyber hardening of critical services, biosecurity detection and response, redundancy in essential infrastructure, exercised institutional continuity, and social absorption: the income support, retraining and transition capacity that decides whether AI-driven job displacement lands as an adjustment or as a shock. Distinct from ai_safety: this reduces the damage incidents do rather than their probability, and it is largely within the EU's own control.
**ID:** resilience
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 35
**Reference points:**

- 15: Brittle. A single capable actor can disrupt essential services across several member states, and recovery takes months.
- 35: Uneven. Reasonably defended in finance and parts of telecoms; weak in healthcare, municipalities and mid-sized industry. Biological detection is slow and largely passive. Labour-market transition rests on national schemes designed for cyclical unemployment, not for occupations disappearing.
- 50: Baseline hardening across critical sectors, with incident response exercised rather than documented. Essential services degrade rather than stop. Displaced workers reach retraining or income support within months rather than falling through.
- 70: Attacks land but do not cascade. Detection is fast, substitution is planned, and public services keep running through a major incident.
- 90: Absorbs a severe incident with local disruption and no strategic consequence.

## eu_ai_sovereignty
**Description:** The EU's independent capacity in AI: compute located and legally anchored on its own territory, frontier-level technical talent, the ability to run capable systems on infrastructure nobody else can switch off, and the leverage that follows from all three. Not the same as being able to act — see eu_political_capital.
**ID:** eu_ai_sovereignty
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 22
**Reference points:**

- 10: Total dependence. Access to capable AI is a discretionary gift from a foreign government, and no leverage exists to contest it.
- 22: Around five per cent of world compute, no frontier laboratory, genuine strength in the upstream hardware supply chain, and no coordinated position from which to use it.
- 40: Enough domestic compute to serve essential public and industrial workloads. Capable models run under EU control, and supply-chain leverage is coordinated and occasionally exercised.
- 60: A credible EU alternative for most applications, and a bottleneck position strong enough that excluding the EU is costly to whoever tries.
- 85: Independent frontier capability. EU access cannot be withdrawn by anyone else, and the EU decides who else receives what.

## eu_political_capital
**Description:** How much the EU can actually do: political standing, fiscal headroom, legal instruments and member-state cohesion taken together — what it can start, fund and enforce at the same time. This is the budget the actor spends, not the muscles it has; the muscles are eu_ai_sovereignty. Falls with fiscal strain, fragmentation, overreach and failed measures; rises with visible successes, with capacity that has finished landing, and — where the run's rules provide for it — while it sits below `public_sentiment`, because a public that is with the Union lends it room the Union has not earned yet.
**ID:** eu_political_capital
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 48
**Reference points:**

- 10: Paralysed. Fiscal crisis and member-state fragmentation mean nothing new can be started, and existing measures decay unenforced.
- 30: One measure at a time, and only if it is uncontroversial. Money is the binding constraint.
- 48: Strong legal instruments, thin technical capacity, contested legitimacy and a tightening budget. Two or three measures can run at once before something slips.
- 65: Can fund and enforce several parallel measures, and hold a common position under external pressure.
- 85: Acts decisively and at speed when it judges the situation demands it — the register of the pandemic response or the post-invasion energy shift — and the member states hold together while it does.

## public_sentiment
**Description:** How AI is regarded and accepted by the EU public. Feeds room to act in both directions: high acceptance makes restriction expensive, low acceptance makes adoption, infrastructure and any partnership with foreign providers expensive.
**ID:** public_sentiment
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 42
**Reference points:**

- 15: Broad hostility. Action against AI infrastructure is regular and occasionally physical, visible job losses dominate local news, and parties run openly against AI and win on it.
- 30: Anxious and sceptical. Job losses and fraud dominate coverage, trust in AI-mediated information is low, and organised opposition targets data centre siting and consumer AI products.
- 42: Ambivalent. Widely used, widely resented, sharply divided by age and by sector.
- 60: Broadly positive. Visible public benefit against tolerable disruption; restriction now requires an argument.
- 80: Enthusiastic. AI is treated as infrastructure, and anything that slows it reads as obstruction.
