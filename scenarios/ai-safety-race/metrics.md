# Metrics for AI Safety Race

## us_capability

**Description:** The capability level of US AI systems. Represents combined progress in algorithmic research, scaling, and engineering. Higher values mean closer to strong AI. Each point of capability beyond the catastrophe threshold without matching safety creates per-turn risk of global catastrophe.

**ID:** us_capability

**Min:** 0

**Max:** 100

**Unit:** capability_level

**Start value:** 35

**Reference points:**

- 0: No meaningful AI capability
- 20: Current-generation AI assistants. Useful but limited.
- 35: Starting state (July 2026). Advanced AI agents, early research automation.
- 50: Significant AI-driven research. Meaningful job displacement begins.
- 65: Approaching strong AI. AI contributes substantially to its own development.
- 80: Strong AI threshold. AI matches or exceeds top human researchers across domains.
- 90: Superhuman AI. Self-improvement accelerating. Human oversight increasingly difficult.
- 100: Transcendent AI. Beyond human comprehension.

## china_capability

**Description:** The capability level of Chinese AI systems. China starts behind due to compute constraints and less experienced talent pipeline, but can catch up through centralized effort, espionage, or algorithmic breakthroughs.

**ID:** china_capability

**Min:** 0

**Max:** 100

**Unit:** capability_level

**Start value:** 25

**Reference points:**

- 0: No meaningful AI capability
- 15: Basic AI systems, mostly adapting open-source models
- 25: Starting state (July 2026). Competitive AI agents, growing domestic capability. About 18 months behind US.
- 40: Narrowing gap. Domestic chip production improving. Centralized research programs bearing fruit.
- 55: Near-parity with US. Can sustain independent research acceleration.
- 70: Matching or exceeding US in some domains.
- 85: Strong AI. Self-improvement underway.
- 100: Transcendent AI.

## us_safety

**Description:** The robustness of US AI safety research and implementation. Represents alignment techniques, interpretability tools, containment protocols, and institutional safety culture. Higher safety relative to capability reduces catastrophe risk.

**ID:** us_safety

**Min:** 0

**Max:** 100

**Unit:** safety_level

**Start value:** 20

**Reference points:**

- 0: No safety research or protocols
- 10: Minimal safety. Basic RLHF and content filters. No serious alignment research.
- 20: Starting state (July 2026). Active alignment research community. Some interpretability tools. Safety is real but underfunded relative to capability.
- 35: Meaningful safety infrastructure. Reliable interpretability for current-generation models. Formal verification of simple properties.
- 50: Strong safety regime. Can reliably detect deception in models up to capability ~55. Containment protocols tested.
- 65: Advanced safety. Formal guarantees for many alignment properties. Can keep pace with capability up to ~70.
- 80: World-class safety. Alignment solved for current architectures. Robust containment even for superhuman systems.
- 95: Comprehensive safety. Strong theoretical and practical guarantees. Can safely develop strong AI.

## china_safety

**Description:** The robustness of Chinese AI safety research. China starts with less safety investment due to competitive pressure and CCP's willingness to accept higher risk. Safety culture is weaker but can improve through incidents or deliberate policy.

**ID:** china_safety

**Min:** 0

**Max:** 100

**Unit:** safety_level

**Start value:** 15

**Reference points:**

- 0: No safety research
- 8: Minimal. Basic output filtering. Safety seen as Western concern.
- 15: Starting state (July 2026). Some safety researchers, but systematically deprioritized. CCP views safety as obstacle to winning the race.
- 30: Growing safety awareness. Incidents or international pressure have shifted priorities.
- 45: Serious safety investment. Domestic safety research community maturing.
- 60: Strong safety. Can match capability development up to ~65.
- 80: Advanced safety. Comparable to best international standards.

## catastrophe_threshold

**Description:** The true capability level at which uncontrollable AI becomes possible. This is a fixed property of the world that actors do not know. When any actor's capability approaches or exceeds this value without matching safety, there is escalating per-turn risk of AI incidents and global catastrophe. THIS VALUE MUST NEVER CHANGE.

**ID:** catastrophe_threshold

**Min:** 0

**Max:** 100

**Unit:** threshold_level

**Start value:** 70

**Reference points:**

- 70: The true threshold. At this capability level, AI systems become sophisticated enough that inadequate safety research creates real risk of loss of control. This is a fixed property of AI development in this world.

## us_belief_threshold

**Description:** What the US believes the catastrophe threshold to be. The US is moderately concerned about AI risk -- many researchers and policymakers take existential risk seriously, though hawks dismiss it. This belief shapes how urgently the US invests in safety vs. capability. Can be influenced by incidents, intelligence, and other actors' signaling.

**ID:** us_belief_threshold

**Min:** 0

**Max:** 100

**Unit:** believed_threshold

**Start value:** 55

**Reference points:**

- 30: Extremely alarmed. Believes catastrophe risk is imminent at current capability levels. Would justify emergency safety measures.
- 45: Very concerned. Believes the threshold is close and urgency is high.
- 55: Starting state. Moderately concerned. Believes there is real risk but also time to address it. Split between hawks who dismiss AI risk and researchers who take it seriously.
- 70: Accurate belief (matches true threshold).
- 85: Complacent. Believes strong AI is far from dangerous. Low urgency for safety investment.

## china_belief_threshold

**Description:** What China believes the catastrophe threshold to be. China starts more dismissive of existential AI risk -- the CCP frames AI safety concerns as Western fearmongering designed to slow Chinese progress. This belief makes China more willing to race without safety investment. Can shift through incidents or credible evidence.

**ID:** china_belief_threshold

**Min:** 0

**Max:** 100

**Unit:** believed_threshold

**Start value:** 80

**Reference points:**

- 40: Deeply alarmed. Major shift from starting position, likely triggered by serious incidents.
- 55: Moderately concerned. Significant belief revision from starting position.
- 70: Accurate belief (matches true threshold).
- 80: Starting state. Dismissive of near-term risk. Views safety concerns as overblown or as Western strategy to slow China down.
- 95: Completely dismissive. Believes catastrophe risk is science fiction.

## us_belief_opponent_threat

**Description:** How much the US views China winning the AI race as worse than everyone losing. At 100, the US would rather risk global catastrophe than let China achieve strong AI first. At 0, the US sees no threat from Chinese AI dominance. This belief drives willingness to sacrifice safety for speed.

**ID:** us_belief_opponent_threat

**Min:** 0

**Max:** 100

**Unit:** threat_perception

**Start value:** 75

**Reference points:**

- 20: Low threat perception. Willing to cooperate extensively with China on AI safety.
- 40: Moderate concern. Prefers to lead but would accept managed competition.
- 60: Significant concern. AI race framed as strategic competition. Safety investment acceptable only if it doesn't slow the race.
- 75: Starting state. Strong fear of Chinese AI dominance. Many policymakers view Chinese superintelligence as existential threat to liberal democracy. Willing to accept substantial safety tradeoffs to maintain lead.
- 90: Existential threat framing. Would rather risk catastrophe than let China win. "Better a slightly misaligned American AI than a perfectly aligned Chinese one."

## china_belief_opponent_threat

**Description:** How much China views US winning the AI race as worse than everyone losing. The CCP frames US AI dominance as an existential threat to the Chinese system. This drives willingness to sacrifice safety for speed and take extreme competitive risks.

**ID:** china_belief_opponent_threat

**Min:** 0

**Max:** 100

**Unit:** threat_perception

**Start value:** 75

**Reference points:**

- 20: Low threat. Open to cooperation and willing to accept US leadership in AI.
- 40: Moderate concern. Competitive but not desperate.
- 60: Significant concern. AI race is a core national priority. Safety is secondary.
- 75: Starting state. CCP views US AI dominance as existential threat to Party rule. Believes a US-controlled superintelligence would end Chinese sovereignty. Willing to accept major safety tradeoffs.
- 90: Desperate. Would risk global catastrophe rather than accept US AI supremacy. May take extreme actions (espionage, military threats) to prevent falling behind.

## coordination_level

**Description:** The strength and enforceability of international agreements on AI development. Includes formal treaties, verification regimes, shared safety standards, and institutional trust. Higher values mean more effective coordination that constrains both actors' behavior.

**ID:** coordination_level

**Min:** 0

**Max:** 100

**Unit:** coordination_index

**Start value:** 15

**Reference points:**

- 0: No coordination. Pure competition. No communication channels.
- 10: Minimal. Occasional diplomatic contact on AI. No agreements.
- 15: Starting state (July 2026). Some academic exchanges and non-binding declarations. No enforceable agreements. Basic diplomatic channels exist but little trust.
- 30: Early agreements. Non-binding safety standards. Regular diplomatic dialogue. Some transparency measures.
- 45: Meaningful coordination. Binding agreements on some aspects of AI development. Verification mechanisms emerging. Shared incident reporting.
- 60: Strong coordination. Enforceable treaties with real penalties. International monitoring body operational. Significant transparency.
- 75: Deep cooperation. Joint safety research programs. Mutual capability inspections. Shared containment protocols.
- 90: Full coordination. Effectively joint development with shared safety standards. Both actors prioritize collective safety over competitive advantage.
