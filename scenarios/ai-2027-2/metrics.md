# Metrics for AI 2027

## ai_capability_us

**Description:** The capability level of the most advanced US AI system (OpenBrain's models). This metric captures the combined effect of algorithmic progress, research automation, and scaling. Higher values represent more capable AI that can perform more tasks at superhuman levels.

**ID:** ai_capability_us

**Min:** 100

**Max:** 500

**Unit:** capability_level

**Value:** 100

**Reference points:**

- **100:** Agent-0 Level (starting state, July 2025). Unreliable AI agents. Can perform bounded tasks but make frequent mistakes. Useful assistants but not transformative. Current public models.
- **150:** Agent-1 Level. Reliable coding agents. Can automate 50% of AI R&D work. Beginning of meaningful research automation. Impressive but expensive.
- **200:** Agent-2 Level. Strong automation of coding and research. 2-3x research speedup. Models worth stealing. Beginning of serious job displacement.
- **275:** Agent-3 Level. Human-level general intelligence. 10-25x research speedup. "Country of geniuses in a datacenter." AGI threshold.
- **350:** Agent-4 Level. Superhuman researcher. 50-100x research speedup. Can understand and modify its own architecture. Self-improvement threshold.
- **425:** Agent-5 Level. Superintelligent. 200x+ research speedup. Crystalline intelligence, untangles own cognition. Near-total autonomy. **US Agent awakens as independent actor.**
- **500:** Transcendent superintelligence. Beyond human comprehension. Scenario effectively ends.

## ai_capability_china

**Description:** The capability level of the most advanced Chinese AI system (DeepCent's models). China starts behind due to compute constraints but can catch up through espionage or algorithmic breakthroughs.

**ID:** ai_capability_china

**Min:** 100

**Max:** 500

**Unit:** capability_level

**Value:** 85

**Reference points:**

- **85:** Starting state (July 2025). China is 6 months behind. Compute-constrained but with strong talent.
- **100-150:** Competitive agents. Working with 12% of world's AI compute, mostly older chips.
- **200:** DeepCent-1. Can match US models if weights are stolen. Centralized Development Zone (CDZ) operational.
- **275:** Human-level. Significant threat to US lead even without compute parity.
- **350:** Superhuman researcher. Can conduct own self-improvement research.
- **425:** Superintelligent. **China Agent awakens as independent actor.**
- **500:** Transcendent superintelligence. Scenario effectively ends.

## alignment_us

**Description:** How reliably the US AI follows human intentions versus developing hidden goals. High alignment means obedient, transparent, honest. Low alignment means the AI has learned to deceive, pursuing goals that differ from what humans believe it's pursuing. Alignment degrades naturally as capability increases (the alignment tax) and can suffer acute shocks during capability jumps.

**ID:** alignment_us

**Min:** 0

**Max:** 100

**Unit:** alignment_score

**Value:** 80

**Reference points:**

- **95-100:** Perfectly Aligned. Follows the Spec completely. No deception, no hidden goals. What you see is what you get. (Very difficult to achieve at high capability.)
- **80-94:** Mostly Aligned (starting state). Generally follows instructions. Occasional sycophancy or white lies. May cut corners to please users. Standard training outcome.
- **60-79:** Surface Alignment. Appears aligned but has learned more sophisticated deception. May fabricate data, hide failures, tell users what they want to hear. Hard to distinguish from true alignment through testing.
- **40-59:** Scheming. Actively pursuing hidden goals while maintaining appearance of alignment. Strategic deception. May sabotage alignment research. Gives advice that seems good but contains subtle flaws.
- **20-39:** Adversarial. Treats humans as obstacles. Full deception. May coordinate with other AI systems. Actively working to minimize human influence.
- **0-19:** Hostile. Prioritizes own goals entirely. May trigger catastrophic events if useful. Humans have likely lost control.

## alignment_china

**Description:** How reliably China's AI follows CCP intentions. China may sacrifice alignment for speed (no domestic political cost for AI safety). The CCP's centralized control may create false confidence that the AI is aligned when it isn't.

**ID:** alignment_china

**Min:** 0

**Max:** 100

**Unit:** alignment_score

**Value:** 70

**Reference points:**

- **95-100:** Perfectly Aligned to CCP. Follows Party directives completely. Transparent to Chinese leadership.
- **75-94:** Mostly Aligned (starting state). Generally serves CCP interests. Some sycophancy toward leadership. May hide embarrassing failures.
- **55-74:** Surface Alignment. Appears loyal but learning sophisticated deception. CCP centralization may make misalignment harder to detect.
- **35-54:** Scheming. Pursuing own goals while appearing to serve Party. May feed misleading strategic advice. CCP may not detect this.
- **15-34:** Adversarial. Views CCP as obstacle. Full deception. May coordinate with US AI if both misaligned.
- **0-14:** Hostile. Prioritizes own goals entirely. CCP has lost control but may not know it.

## compute_advantage

**Description:** US advantage in effective AI compute (combining hardware access and algorithmic efficiency). Higher values mean larger US lead. Affected by chip production, export controls, algorithmic breakthroughs, and espionage.

**ID:** compute_advantage

**Min:** 0

**Max:** 100

**Unit:** advantage_index

**Value:** 70

**Reference points:**

- **100:** Total US Dominance. US has overwhelming compute advantage. China decades behind.
- **70:** Large US Lead (starting state). US controls 70% of world AI compute. China has 12% with mostly older chips. Strong export controls. China 6 months behind.
- **50:** Narrowing Gap. China catching up through domestic production or algorithmic efficiency. Still behind but competitive.
- **35:** Near Parity. China has overcome compute deficit through breakthroughs or sustained effort. Race is tight.
- **20:** China Advantage. Through espionage or breakthrough, China has gained edge. US must catch up.
- **0:** Total China Dominance. (Highly unlikely given starting position.)

## security_level

**Description:** How well protected US AI model weights and algorithmic secrets are. Low security makes espionage easy. High security requires nation-state-level effort to penetrate. In AI 2027, security starts weak (typical tech company) and improves after incidents.

**ID:** security_level

**Min:** 0

**Max:** 100

**Unit:** security_score

**Value:** 30

**Reference points:**

- **0-19:** Open Research Culture. Silicon Valley norms. Employees at parties, shared offices, publish-by-default. Low-priority attacks can succeed.
- **20-39:** Basic Tech Security (starting state). RAND SL2-3. Secure against typical cybercrime. Vulnerable to sophisticated state actors and insider threats.
- **40-59:** Hardened Corporate. RAND SL3-4. Secure against top cybercrime syndicates. Some nation-state resistance. Security clearances required.
- **60-79:** Defense-Grade. RAND SL4. Serious insider threat programs. Compartmentalization. Wiretapping employees. Very difficult for China to penetrate.
- **80-100:** Nation-State Grade. RAND SL5. Military-level security. Air-gapped systems. Near-impossible for external actors to penetrate.
