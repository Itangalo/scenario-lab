# Metrics

Seven quantities describe the world the regulator acts on. None of them
describe the regulator's own portfolio: which measures are running, and how far
each has been implemented, lives in the narrative and in the actor's notepad,
not in a metric.

Two capability metrics are deliberately kept as reference poles rather than as
a single "frontier" number, because the gap between them is what drives the
competitive argument against every restriction the regulator proposes.

## us_capability
**Description:** Capability of the strongest closed US frontier systems, measured as general problem-solving competence across economically and strategically relevant tasks. Accumulated capability; it does not fall back.
**ID:** us_capability
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 45
**Reference points:**
- 30: Strong assistant. Reliable on well-specified tasks, needs supervision on anything long-horizon.
- 45: Mid-2026. Executes multi-hour software and research tasks with a competent human checking the output. Clearly superhuman in narrow domains, clearly not in general.
- 60: Reliably completes multi-day professional projects end to end. Displaces junior work in several sectors rather than assisting it.
- 75: Matches strong domain experts across most cognitive professions. Materially accelerates the research that produces its own successors.
- 90: Broadly superhuman. Sets research agendas rather than executing them; human oversight is nominal on anything technical.
- 100: Decisively superhuman across every measured domain.

## cn_capability
**Description:** Capability of the strongest Chinese frontier systems, on the same scale as us_capability. Accumulated; it does not fall back.
**ID:** cn_capability
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 38
**Reference points:**
- 30: Strong assistant, roughly a year behind the US frontier.
- 38: Mid-2026. Behind on the very frontier, ahead on deployment breadth and cost, closing on domestic compute.
- 50: Parity on most deployed applications, still behind on the largest training runs.
- 70: At the frontier. No reliable capability argument remains for treating the US as the sole source of the strongest systems.
- 90: Broadly superhuman.

## openweight_gap
**Description:** How far the best openly released model weights sit behind the strongest closed frontier model. High means dangerous capability is concentrated in a few auditable organisations; low means it is everywhere and unrecallable.
**ID:** openweight_gap
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 30
**Reference points:**
- 0: Open weights are at the frontier. Every capability the frontier has is on a laptop somewhere, permanently, and no release control means anything.
- 15: Roughly six months behind. Restrictions bite for one model generation and then evaporate.
- 30: Mid-2026. Around a year to eighteen months behind on general capability, closer than that in code.
- 55: Two to three years behind. Frontier-only risks are genuinely governable through the closed labs.
- 80: A wide structural gap; frontier capability requires compute and know-how no open release comes near.

## incident_pressure
**Description:** Current level of realised and near-miss harm from AI systems — cyber, bio, infrastructure, large-scale fraud — as it registers on decision-makers. Rises with incidents, falls as preparedness and defensive capacity absorb them.
**ID:** incident_pressure
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 20
**Reference points:**
- 10: Isolated misuse, handled by ordinary law enforcement. No political salience.
- 20: Mid-2026. Recurring model-assisted cybercrime and fraud, several serious near-misses documented, nothing that has broken through as a crisis.
- 40: A significant incident with real casualties or a major sector disrupted. AI harm becomes a standing agenda item rather than a foresight topic.
- 60: Repeated large incidents, or one severe enough that emergency powers are used. Emergency legislation passes in weeks rather than years.
- 85: Sustained crisis. Attribution is uncertain, defences are visibly behind, and normal policy-making has stopped.

## regulatory_capacity
**Description:** The regulator's combined political capital, institutional bandwidth and technical competence — how much it can push at once and how credibly. Rises with visible successes and with capacity-building measures that have landed; falls with failures, with overreach, and with every measure still under implementation.
**ID:** regulatory_capacity
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 50
**Reference points:**
- 15: Discredited or exhausted. Nothing new can be started; existing measures decay unenforced.
- 30: Can sustain one measure at a time, and only if it is uncontroversial.
- 50: Mid-2026. Real legal instruments, thin technical capacity, contested legitimacy. Two or three measures can run at once before something slips.
- 70: Trusted and competent. Can carry several parallel measures and be taken seriously outside its own jurisdiction.
- 90: The reference authority on AI governance. Its standards are adopted elsewhere because they are the standards, not because of market access.

## economic_context
**Description:** The AI investment climate: capital availability, valuations, and the willingness of governments to accept costs on AI development. High means an expansionary boom in which restriction is politically expensive; low means a bust in which capability growth slows on its own and safety arguments get cheaper.
**ID:** economic_context
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 65
**Reference points:**
- 15: Deep AI-sector bust. Capital has fled, build-out has stopped, and restrictions cost nothing because nobody is expanding.
- 35: Correction. Funding is selective, the weakest labs are gone, growth continues at the two or three best-capitalised.
- 65: Mid-2026. Abundant but nervous capital; datacentre build-out at record scale; open argument about whether revenues justify it.
- 85: Full boom. Any measure that slows deployment is attacked as economic self-harm and usually loses.

## public_sentiment_to_ai
**Description:** How AI is regarded and accepted by the public in the regulator's own constituencies. Feeds political capital in both directions: high acceptance makes restriction expensive, low acceptance makes adoption and infrastructure expensive.
**ID:** public_sentiment_to_ai
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 42
**Reference points:**
- 15: Broad hostility. Protest action against AI infrastructure is regular and occasionally physical; boycotts bite; visible job losses in named sectors dominate local news; politicians run openly anti-AI and win on it.
- 30: Anxious and sceptical. Job losses and fraud dominate coverage; trust in AI-mediated information is low; the first organised protests target datacentre siting and AI products, mostly petitions and hearings rather than streets.
- 42: Mid-2026. Ambivalent. Widely used, widely resented, sharply divided by age and sector.
- 60: Broadly positive. Visible public benefit, tolerable disruption; restriction requires an argument.
- 80: Enthusiastic. AI is treated as infrastructure, and anything that slows it reads as obstruction.
