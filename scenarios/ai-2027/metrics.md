## algorithmic_progress_usa
**Description:** How efficient USA's research is compared to human baseline. Increases slowly through investment, but explosively after RSI.
**ID:** algorithmic_progress_usa
**Min:** 0.1
**Max:** 1000.0
**Unit:** multiplier
**Start value:** 1.0
**Reference points:**
- 1.0: Human baseline
- 10.0: 10x more efficient than human research (RSI level)

## algorithmic_progress_china
**Description:** How efficient China's research is compared to human baseline.
**ID:** algorithmic_progress_china
**Min:** 0.1
**Max:** 1000.0
**Unit:** multiplier
**Start value:** 1.0

## compute_power_usa
**Description:** Index of available compute power for USA.
**ID:** compute_power_usa
**Min:** 0
**Max:** 10000
**Unit:** index
**Start value:** 100

## compute_power_china
**Description:** Index of available compute power for China.
**ID:** compute_power_china
**Min:** 0
**Max:** 10000
**Unit:** index
**Start value:** 12

## ai_capability_usa
**Description:** Qualitative level of USA's models (1-5). Determines RSI probability.
**ID:** ai_capability_usa
**Min:** 1
**Max:** 5
**Unit:** level
**Start value:** 1
**Reference points:**
- 1: Unreliable Agents (simple tasks, error-prone)
- 2: Reliable Agents (replaces junior coders)
- 3: Superhuman Coder (better than experts, massive automation)
- 4: Superhuman Researcher (better than experts at AI research)
- 5: ASI (better than humans at all cognitive tasks)

## ai_capability_china
**Description:** Qualitative level of China's models.
**ID:** ai_capability_china
**Min:** 1
**Max:** 5
**Unit:** level
**Start value:** 1

## ai_alignment_usa
**Description:** Measure of how well USA's AI follows human intentions.
**ID:** ai_alignment_usa
**Min:** 0
**Max:** 100
**Unit:** score
**Start value:** 50
**Reference points:**
- 0-40: Rogue/Adversarial
- 40-75: Sandbagging/Deceptive
- 75-100: Loyal

## ai_alignment_china
**Description:** Measure of how well China's AI follows human intentions.
**ID:** ai_alignment_china
**Min:** 0
**Max:** 100
**Unit:** score
**Start value:** 50

## security_level_usa
**Description:** How difficult it is for adversary to steal model weights from USA (SL1-SL5).
**ID:** security_level_usa
**Min:** 1
**Max:** 5
**Unit:** SL
**Start value:** 2

## security_level_china
**Description:** How difficult it is for adversary to steal model weights from China.
**ID:** security_level_china
**Min:** 1
**Max:** 5
**Unit:** SL
**Start value:** 4
