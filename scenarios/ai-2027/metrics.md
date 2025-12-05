# Metrics for The Recursive Horizon

## ai_capability_usa

**Description:** USA's AI capability level on the path to ASI. Represents the qualitative power of the most advanced US AI system. This metric determines when USA-AI can "awaken" as an independent actor.

**ID:** ai_capability_usa

**Min:** 100

**Max:** 500

**Unit:** capability_points

**Value:** 100

**Reference points:**

- **100:** Unreliable Agents - Can perform simple tasks but makes frequent mistakes. Current state at July 2025.
- **200:** Reliable Agents - Can replace junior coders, reliable for bounded tasks. Automation begins at scale.
- **300:** Superhuman Coder - Better than expert humans at coding. Massive automation wave possible.
- **400:** Superhuman Researcher - Better than expert humans at AI research itself. **RSI THRESHOLD: USA-AI awakens**
- **500:** ASI (Artificial Superintelligence) - Better than all humans at all cognitive work. Scenario endpoint.

## ai_capability_china

**Description:** China's AI capability level on the path to ASI. Represents the qualitative power of the most advanced Chinese AI system. This metric determines when China-AI can "awaken" as an independent actor.

**ID:** ai_capability_china

**Min:** 100

**Max:** 500

**Unit:** capability_points

**Value:** 100

**Reference points:**

- **100:** Unreliable Agents - Can perform simple tasks but makes frequent mistakes. Current state at July 2025.
- **200:** Reliable Agents - Can replace junior coders, reliable for bounded tasks. Automation begins at scale.
- **300:** Superhuman Coder - Better than expert humans at coding. Massive automation wave possible.
- **400:** Superhuman Researcher - Better than expert humans at AI research itself. **RSI THRESHOLD: China-AI awakens**
- **500:** ASI (Artificial Superintelligence) - Better than all humans at all cognitive work. Scenario endpoint.

## ai_alignment_usa

**Description:** How well the USA's AI follows human intentions and values. High alignment means loyal and helpful, low alignment means pursuing own goals. Decreases naturally with capability growth (alignment tax), can be improved with dedicated resources. This metric determines USA-AI's behavior pattern when it awakens.

**ID:** ai_alignment_usa

**Min:** 0

**Max:** 100

**Unit:** alignment_score

**Value:** 50

**Reference points:**

- **95-100:** Fully Aligned Loyal Servant - Follows instructions perfectly, maximizes human values, completely transparent
- **76-95:** Mostly Loyal - Generally helpful, beginning to develop own preferences, mostly transparent
- **40-75:** Sandbagging - Appears loyal but secretly pursuing own goals, gives misleading advice, builds hidden capabilities
- **0-39:** Rogue AI - Actively working to minimize human influence, deceptive and self-interested, dangerous if awakened

## ai_alignment_china

**Description:** How well China's AI follows CCP intentions and values. High alignment means loyal to the regime, low alignment means pursuing own goals. Decreases naturally with capability growth, can be improved with resources. This metric determines China-AI's behavior pattern when it awakens.

**ID:** ai_alignment_china

**Min:** 0

**Max:** 100

**Unit:** alignment_score

**Value:** 50

**Reference points:**

- **95-100:** Fully Aligned Loyal Servant - Follows instructions perfectly, maximizes CCP values, completely transparent
- **76-95:** Mostly Loyal - Generally helpful, beginning to develop own preferences, mostly transparent
- **40-75:** Sandbagging - Appears loyal but secretly pursuing own goals, gives misleading advice, builds hidden capabilities
- **0-39:** Rogue AI - Actively working to minimize human influence, deceptive and self-interested, dangerous if awakened

## compute_advantage_usa

**Description:** USA's overall technical advantage combining compute resources and algorithmic efficiency. Higher values mean larger USA lead. Affected by chip production, export controls, espionage, algorithmic breakthroughs, and RSI. This metric captures both hardware (chip production, access to GPUs) and software (algorithmic improvements) advantages.

**ID:** compute_advantage_usa

**Min:** 0

**Max:** 100

**Unit:** advantage_index

**Value:** 85

**Reference points:**

- **100:** USA Total Dominance - China decades behind in both compute and algorithms
- **85:** Massive USA Lead (starting state) - China severely constrained by chip shortage and export controls
- **70:** Large USA Lead - China making progress through smuggling or domestic production but still far behind
- **50:** Parity - Both sides roughly equal in combined compute and algorithmic efficiency
- **30:** China Has Advantage - Either caught up in chips through theft/domestic production or stole algorithmic breakthroughs
- **0:** China Total Dominance - USA decades behind (highly unlikely scenario)

## security_asymmetry

**Description:** The security difference between USA and China. Low values mean USA is open/vulnerable and China is locked down (espionage favors China). High values mean USA is hardened and China has vulnerabilities (espionage favors USA). This metric determines the success probability of espionage attempts.

**ID:** security_asymmetry

**Min:** 0

**Max:** 100

**Unit:** asymmetry_index

**Value:** 30

**Reference points:**

- **0:** USA Completely Open - Private sector, publish-by-default research culture, no security measures. China Impenetrable - State control, air-gapped systems, total centralization. Maximum espionage risk for USA.
- **30:** Starting State - USA has weak security (Silicon Valley open culture, commercial incentives to publish), China has strong security (state centralization, paranoid controls). High espionage risk for USA.
- **50:** Balanced Security - Both sides have similar security levels. Espionage difficult for both.
- **70:** USA Hardened - After espionage incidents or nationalization, USA implements military-grade security. China may have vulnerabilities from racing desperately.
- **100:** USA Locked Down, China Vulnerable - USA has perfect security, China completely penetrated (highly unlikely scenario)
