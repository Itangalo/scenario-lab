# Exogenous Events: Sweden and AI 2030

Sketch of external events. Edit freely – Echo generates exogenous-events.yaml when you're satisfied.

---

## Background Trends (trends)

### AI Capability Growth

**Base scenario:** METR benchmark doubles every 6 months.
- Turn 1 (H1 2026): ~3 hours
- Turn 2 (H2 2026): ~6 hours
- Turn 3 (H1 2027): ~12 hours
- Turn 4 (H2 2027): ~24 hours (1 day)
- Turn 5 (H1 2028): ~48 hours (2 days)
- Turn 6 (H2 2028): ~96 hours (4 days)
- Turn 7 (H1 2029): ~192 hours (~8 days)
- Turn 8 (H2 2029): ~384 hours (~16 days)
- Turn 9 (H1 2030): ~768 hours (~1 month)
- Turn 10 (H2 2030): ~1536 hours (~2 months)

**Variant scenarios:**
- Slow: Doubling every 12 months (reach ~48 hours by end)
- Fast: Doubling every 4 months (reach ~6 months by end)

### EU AI Regulation

Gradual implementation of AI Act, with possible relaxation of some requirements.

---

## Scheduled Events (scheduled)

### Swedish Election 2026 (Turn 2: H2 2026)

The Swedish general election takes place in September 2026.

**Possible outcomes (for branching):**
1. **Status quo:** AI policy continues to be mostly inactive and for show (even if coalition might have changed)
2. **Active AI agenda:** The government prioritizes AI in one or several areas: sovereignty in computing power, stimulus for getting companies to build on AI, public education on AI, national/EU efforts to build/fine tune AI models, building out power production for AI and more, AI safety, proactive efforts to reduce negative effects of AI-induced unemployment

### US Presidential Election 2028 (Turn 5: H1 2028)

Primary season and election campaign dominate US politics.

**Possible outcomes (for branching):**
1. **Accelerationist:** Continued aggressive pro-AI, anti-regulation stance
2. **Regulatory shift:** More cautious approach, potential international cooperation (even with China)

---

## Conditional Events (conditional)

### Major AI-Driven Layoffs in Sweden

**Condition:** AI capability reaches 24+ hours AND business sector aggressively adopts AI
**Effect:** Large Swedish company announces significant workforce reduction explicitly citing AI automation. Media coverage intensifies. Union pressure increases.

### EU AI Act Enforcement Issues

**Condition:** AI capability outpaces regulation AND major compliance failures occur
**Effect:** EU forced to either strengthen enforcement or relax requirements. Creates uncertainty for Swedish businesses.

### EU AI Act Stops Frontier Models

**Condition:** EU AI Act is not scaled back, while the US does not adopt any significant regulation
**Effect:** A new generation of frontier models are prohibited on the EU market. EU faces protests both from EU companies and AI providers.

---

## Random Events (random)

### AI Safety Incident - Global

**Probability:** 15% per turn (cumulative ~80% over 10 turns)
**Severity range:** Minor to major

**Possible manifestations:**
- Minor: AI system causes financial loss or privacy breach
- Moderate: AI-enabled cyberattack with significant damage
- Major: AI system causes deaths (suicide/mental health, autonomous vehicle, medical, infrastructure)
- Severe: AI system used in military/terrorism context

**Effect:** Shifts public opinion, increases regulatory pressure.

### AI Safety Incident - Sweden Specific

**Probability:** 5% per turn
**Possible manifestations:**
- Suicide linked to AI companion/chatbot
- Attack planned or prepared with the help of AI

**Effect:** Intense Swedish media coverage. Political pressure for regulation. Public opinion shifts negative. Comparisons to social media harms debate.

### AI Economic Bubble Collapse

**Probability:** 20% in turns 1-3, 10% in turns 4-6, 5% in turns 7-10
**Effect:** Major AI investment pullback. Startups fail. Development slows temporarily. Established players consolidate.

### Taiwan Crisis

**Probability:** 5% per turn
**Types:**
- Blockade: China restricts Taiwan trade, chip supply disrupted
- Hot conflict: Military action, severe global disruption

**Effect:** Chip shortage. All production and products involving computer chips are affected. AI development slowed globally. Geopolitical tensions affect all actors.

### AI-Powered Humanoid Robots Become Useful

**Probability:** 10% per turn starting turn 4 (H2 2027)
**Effect:** Physical labor automation becomes viable. Major implications for manufacturing, logistics, elderly care. Accelerates labor market concerns.

### Major AI Capability Breakthrough

**Probability:** 5% per turn
**Types:**
- New architecture (transformer-level impact)
- Recursive self-improvement demonstrated
- Unexpected emergent capability

**Effect:** Either single large jump in METR benchmark OR sustained acceleration of development pace.

### Major Russian Information Operation Targeting Sweden

**Probability:** 15% per turn
**Effect:** AI-generated disinformation campaign targeting Swedish election, NATO membership, or social issues. Media and government forced to respond.

---

## Notes for Implementation

1. **Probability management:** Some events should have cumulative probability (if not triggered, slightly higher chance next turn)

2. **Branching vs. random:** Elections are better handled as manual branch points rather than random events, since outcomes significantly change scenario trajectory

3. **Event interactions:** Some events should influence others:
   - AI bubble collapse reduces breakthrough probability
   - Safety incident increases regulation probability
   - Taiwan crisis affects AI development pace

4. **Scenario variants:** Different exogenous-events.yaml files for:
   - Base scenario (as described)
   - Slow AI development
   - Fast AI development
