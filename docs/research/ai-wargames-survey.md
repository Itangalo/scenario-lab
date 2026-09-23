# AI scenarios and wargames worth emulating in Scenario Lab (ECHO 2026-09-23)

Web survey of published AI wargames, tabletop exercises and scenario families, with notes on how each maps onto Scenario Lab constructs (actors, metrics, events, variants, live mode). Researched 2026-09-23; links verified live that day. Next step already decided: frame and build an Intelligence Rising analogue (see last section). (ECHO 2026-09-23: built the same day as `scenarios/intelligence-rising/` – emulated, not yet verified, see item 1.)

## Ranked candidates

### 1. Intelligence Rising (CSER/FHI) – top pick, emulated 2026-09-23 (ECHO 2026-09-23)

Status: emulated as `scenarios/intelligence-rising/` (4 actors, 6 metrics, 14 events, validated + smoke-tested + prompt sign-off generated), but not yet verified against the original – no TSG review, no batch comparison, Johan has not inspected the hand-off documents. Treat emulation fidelity as unconfirmed until then.

The original AI strategy roleplay (Avin et al. 2020): 4+ stakeholders (US, China, Google, Microsoft, Baidu, Tencent) racing up a four-level tech tree to radically transformative AI (RTAI – either agentic AGI or Drexlerian Comprehensive AI Services). Mechanics cover R&D investment, product deployment, safety research, espionage/sabotage, and policy-making including international agreements. Later versions added a "Policy Tree" of frontier-AI governance policies (games with it were excluded from the analysis below) and an online adaptation.

Facilitator analysis of 43 games / ~200 hours of play (Gruetzemacher, Avin, Fox, Saeri – *Futures*, March 2026... 2025, vol. 167; also arXiv 2410.03092):

- Races are destabilising; the recurring nightmare is the "bad loser": the runner-up (often a bloc such as China+Tencent or USA+Alphabet/Microsoft) launches a preventive attack – cyber or kinetic – when a rival's RTAI deployment looks imminent, perceiving it as an existential threat without a pre-existing autonomy treaty.
- Race shapes vary: company-vs-company, states racing by proxy (backing, funding, procurement, public-private partnerships – the common US pattern), and direct state-vs-state races (usually requiring nationalisation, a large minority of games).
- Endgame negotiations under time pressure usually fail or produce hastily drafted agreements that defect into cyber/hard-power conflict in the closing minutes; outcomes often hinge on dice.
- Policies enacted in play are mostly reactive ("a band-aid on a wound that needs stitches"); even proactive ones lag rapid RTAI progress.
- An agreement assuring the autonomy of democratic and non-democratic governments alike is flagged as critical to any good outcome.
- Origins: unstructured exercise at FHI Oxford / CSER Cambridge (July 2017, Cotton-Barratt, Page, Avin), iterated at CSER, first tabletop version from a September 2019 design sprint at FHI.

Scenario Lab mapping: actors = states + labs (proxy-race dynamics suit per-actor statement ledgers); metrics = capability level, safety investment, geopolitical tension, agreement strength; events = breakthroughs, leaks, cyberattacks, summits, elections; termination = DSA-equivalent (decisive strategic advantage) or loss-of-control. Strong live-workshop candidate (proven in facilitated play; player count fits the 90-minute format).

Sources: https://doi.org/10.48550/arxiv.2410.03092 and https://www.sciencedirect.com/science/article/pii/S0016328725000254

### 2. RAND Day After AGI series (Infinite Potential platform)

Nine two-hour crisis tabletop exercises, 52 runs, 1 400+ player hours with policymakers, researchers, technologists and industry leaders. Published after-action reports so far: Robot Insurgency (simulated NSC Principals Committee responding to a global rogue-AI cyberattack; RRA4231-1, Oct 2025) and Two Moonshots (China announces a $200B twelve-month AGI moonshot while a US company claims it already crossed the threshold and asks Washington for support). Forthcoming reports cover Cyber Surprise and others, then cross-scenario synthesis.

Scenario Lab mapping: short 1–3 turn crisis scenarios with heavy pre-scripted event injects; the live mode's "menus already reflect this turn's shocks" mechanic fits these well.

Sources: https://www.rand.org/pubs/research_reports/RRA4231-1.html and https://geopoliticsagi.substack.com/p/when-the-future-doesnt-wait

### 3. RAND eight AGI-geopolitics scenarios (RRA3034-2)

Eight vignettes on two axes – centralization of AGI development × geopolitical power shift (empowers US / empowers adversaries / disempowers both / halted). Named scenarios include Cold War 2 (bifurcated US–PRC rivalry with militarized AGI), Wild Frontier (decentralized development empowers non-state actors) and Corked Bottle (multi-actor halt). Key structural assumption to reuse: development stays capital-intensive (data centers, chips, power), so only large firms and states play unless diffusion happens.

Scenario Lab mapping: one scenario family with a vignette per variant/initial-state draw; the centralization axis is nearly a metric already. Cheap to build, good for batch comparison.

Source: https://www.rand.org/content/dam/rand/pubs/research_reports/RRA3000/RRA3034-2/RAND_RRA3034-2.pdf

### 4. CIGI + Privy Council Office Canada: five AI-2030 national-security scenarios

Full-day Ottawa workshop (March 2025, ~30 participants under Chatham House Rule) on three axes – capability gain (stall/fast/exponential) × controllability × number of actors – selecting five scenarios: AI Stall, Precarious Precipice (advanced sub-AGI, mostly controllable), Hypercompetition (multiple controllable ASIs) and Hyperpower (single controllable ASI), each with narrative, national-security implications and policy suggestions. Notable modelling choice: AGI treated as transitory/unstable – once reached, ASI is immediate or imminent.

Scenario Lab mapping: another variant family; the controllability axis suggests a shared metric reusable across families (items 3 and 4 could share metric definitions).

Source: https://www.cigionline.org/static/documents/AI_National_Security.pdf

### 5. CNAS "When the Chips Are Down" semiconductor game

April 2021 virtual strategy game: US (Blue), China (Red) and Taiwan (Green) teams respond to a TSMC fabrication halt (corrupted leading-edge code, cyber vs. accident ambiguous) and play four year-long turns to 2029 using DIME + civil actions tied to targets and intended effects, adjudicated against five indices (technology level, company health, output, demand, public sentiment) plus random events from unrepresented actors.

Scenario Lab mapping: nearly a literal Scenario Lab spec – indices become metrics, DIME lists become menus, four turns is the standard short format. Also supplies realistic compute/chokepoint events (fab sabotage, export controls, talent poaching) for any AI-race scenario.

Source: https://www.cnas.org/publications/reports/when-the-chips-are-down

### 6. NTI + Munich Security Conference AIxBio TTX (Feb 2025)

Three-move game for 14 senior leaders: an extremist group posing as a synbio startup uses AI-enabled biodesign tools to engineer a "neo-enterovirus" (fictional Ankovia, 850M cases / 60M deaths). Findings: AIxBio lowers barriers for sophisticated actors now and less sophisticated ones soon, while raising the ceiling of harm; participants stressed preserving beneficial science and equity of access against over-restrictive safeguards.

Scenario Lab mapping: a misuse/biosecurity scenario with a non-state actor in the cast; metrics around capability diffusion vs. screening/governance/preparedness.

Source: https://www.nti.org/wp-content/uploads/2025/12/2025-NTI-BIO-TTX-Report-FINAL.pdf

### 7. Superintelligence Strategy / MAIM and its critiques

Hendrycks/Schmidt/Wang's deterrence regime: red line = destabilizing projects (paradigmatically "intelligence recursion", thousands of AIs doing automated AI research); response = maiming attacks up an escalation ladder (covert sabotage, overt cyber, kinetic, broader hostilities). The critiques simulate better than the book: MIRI's four governance postures (coordinated Halt / US National Project / Light-Touch private development / Threat of Sabotage) as variants; the observability problem (milestones in compute/chips/datacenters don't forecast overall progress; rapid spurts shrink the detection window; monitoring implies espionage that accelerates the rival) and game-theoretic instability (sabotage delays rather than denies; existential stakes make racing the lower-risk option) as event conditions.

Sources: https://intelligence.org/2025/05/01/ai-governance-to-avoid-extinction-the-strategic-landscape-and-actionable-research-questions/ and https://ai-frontiers.org/articles/superintelligence-deterrence-has-an-observability-problem

### 8. ControlAI/Conjecture "Modeling the Geopolitics of AI Development"

Game-theoretic treatment at https://ai-scenarios.com/ – states choose Halt / Neutral / Race / Attack postures; predictable leaders get preemptively attacked by laggards facing Takeover-or-Extinction; middle powers play "Vassal's Wager" (ally with a superpower, surrendering agency). Terminal outcomes: Takeover, Loss of control, Major-power war.

Scenario Lab mapping: postures as menus, decisive strategic advantage as a termination condition – a clean minimal core if a lighter build is wanted.

## Already covered in this repo – do not duplicate

- AI 2027 (Kokotajlo et al., Race vs. Slowdown timelines to 2027) – covered by `scenarios/ai-2027-2`.
- Conventional Taiwan-conflict games where AI is garnish (CNAS Dangerous Straits / Bad Blood 2023 congressional TTX; CSIS July 2026 lawmaker TTX with AI-backed logistics cyberattacks, misinformation and prompt injection) – borrow event ideas only (logistics cyberattacks, fab scuttling, prompt injection), not whole scenarios.
- CIA/IQT Snow Globe and NATO JWC "Frontlines of Rasputitsa" – LLMs used *inside* wargames; validates the pure-LLM architecture, supplies no subject matter.
- LessWrong "Wargaming AGI development" (2022) – design notes only (invest-for-advantages + diplomacy mechanics, 6–8 key dimensions elicitation); useful if the Intelligence Rising build needs mechanics inspiration.

## Build brief for the next session: Intelligence Rising analogue

Goal: a Scenario Lab scenario playable both as Monte Carlo batch runs and as a live workshop game (workshop block from the start), reproducing the Intelligence Rising dynamics above – proxy and direct races, preventive-attack temptation for the runner-up, fragile endgame agreements, reactive policy lag.

Suggested starting shape: 4–6 actors (two states + two labs minimum; optionally a middle-power or international-body actor for the autonomy-assurance dynamic), metrics for frontier capability, safety/alignment investment, and bilateral tension, event groups for capability breakthroughs, cyber operations, summits/treaties and domestic politics, and termination conditions for decisive strategic advantage and loss of control. The `frame-scenario` skill owns the research-question + information-bank step; `create-scenario` owns drafting, validation and smoke testing. Avin et al. 2020 (original game description) and Gruetzemacher et al. 2025 (43-game analysis) are the two source documents to ingest first – both open-access via the DOI links in item 1.

