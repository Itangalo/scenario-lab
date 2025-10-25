# AI Safety Summit 2025: International Standards Negotiation

A realistic multi-stakeholder simulation of international AI safety governance negotiations.

## Overview

This scenario simulates a high-stakes international summit in London, May 2025, where major stakeholders attempt to negotiate binding international standards for advanced AI systems. Six months after the previous AI Safety Summit, urgency has increased following serious AI incidents and rapid capability advances.

## Scenario Design

**Setting:** 8 turns, each representing 2 weeks of intensive negotiation

**Core Question:** Can the international community reach meaningful consensus on AI safety standards despite competing interests around innovation, security, sovereignty, and public safety?

## Actors (6)

### National Governments (4)

1. **United States**
   - Goals: Maintain AI leadership, protect US tech industry, prevent Chinese advantage
   - Constraints: Congressional politics, tech sector influence, limited appetite for binding commitments
   - Style: Pragmatic, coalition-building, prefers voluntary frameworks

2. **European Union**
   - Goals: Establish EU AI Act as global standard, protect rights and values
   - Constraints: 27 member states consensus, limited domestic AI capabilities
   - Style: Principled, comprehensive, advocates for binding standards

3. **People's Republic of China**
   - Goals: Protect strategic autonomy, ensure sovereignty respected, prevent Western constraints
   - Constraints: Party-state control imperatives, military-civil fusion concerns
   - Style: Strategic, cautious, emphasizes national sovereignty

4. **United Kingdom**
   - Goals: Establish UK as indispensable safety leader, leverage AI Safety Institute
   - Constraints: Medium power, must maintain US and EU relationships
   - Style: Diplomatic, technically credible, honest broker

### Non-State Actors (2)

5. **TechFuture AI** (Frontier AI Company)
   - Goals: Prevent heavy regulation, protect IP, maintain investor confidence
   - Constraints: Cannot expose proprietary info, competitive pressures, public expectations
   - Style: Sophisticated, emphasizes voluntary commitments and implementation challenges

6. **Global AI Safety Coalition** (Civil Society)
   - Goals: Strong binding standards, public interest over profits, independent oversight
   - Constraints: Limited formal power, coalition diversity, resource constraints
   - Style: Principled, evidence-based, public pressure advocacy

## Key Negotiation Issues

1. **Compute Thresholds** - At what FLOPS should international oversight begin? (10^25 to 10^27 range)
2. **Pre-Deployment Testing** - Mandatory requirements, who conducts, pass/fail criteria
3. **Incident Reporting** - What must be reported, timeline (24h to 30 days), detail level
4. **International Coordination** - New institution vs. existing bodies, enforcement powers
5. **Verification & Auditing** - Compliance verification without IP exposure

## Strategic Dynamics

**Key Tensions:**
- Innovation vs. Safety
- Competition vs. Cooperation (especially US-China)
- Sovereignty vs. International Standards
- Industry vs. Regulation
- Speed vs. Thoroughness

**Potential Coalitions:**
- Democratic nations (US-EU-UK)
- Pro-regulation bloc (EU-UK-Civil Society)
- Innovation-focused (US-Industry)
- Sovereignty-focused (China + developing nations)

## Expected Outcomes

This scenario is designed to explore whether consensus is achievable and what factors determine success/failure:

**Possible endpoints:**
- **Strong consensus:** Binding standards with broad support
- **Weak consensus:** Voluntary principles with limited enforcement
- **Fragmented outcome:** Multiple competing frameworks
- **Deadlock:** No agreement, countries pursue unilateral approaches

**Research Questions:**
- What coalition dynamics emerge?
- Do private negotiations enable compromise?
- How do actors balance competing domestic and international pressures?
- What role does technical complexity play in political decisions?
- Can bridge-builders (UK) facilitate agreement?

## Running This Scenario

From the project root:

```bash
python src/run_scenario.py scenarios/ai-safety-summit-2025
```

**Estimated costs:** ~$0.10-0.20 per turn with gpt-4o-mini (6 actors + validation)

**Runtime:** ~5-10 minutes per turn depending on API latency

## Output Files

Each run produces:

**Markdown documentation:**
- `world-state-000.md` through `world-state-008.md` - Negotiation evolution
- `[actor]-001.md` through `[actor]-008.md` - Each actor's decisions and reasoning
- `bilateral-*.md` - Private bilateral negotiations
- `coalition-*.md` - Coalition communications
- `validation-*.md` - Consistency check reports

**Structured data:**
- `metrics.json` - Quantitative tracking of consensus, thresholds, coalitions
- `costs.json` - Cost breakdown by actor and turn
- `scenario-state.json` - Complete state for resumption

## Metrics Tracked

- Consensus level (%)
- Compute threshold agreed (FLOPS)
- Incident reporting timeline (hours)
- Number of coalitions formed
- Standards strength (1-10 scale)
- Testing/auditing requirements (boolean)
- Enforcement mechanisms (boolean)
- US-EU alignment
- China participation level
- Industry compliance willingness
- Transparency requirements
- Breakthrough/deadlock status

## Validation

Quality assurance checks validate:
- **Actor consistency:** Do positions align with national interests and constraints?
- **Negotiation realism:** Do coalition dynamics and reactions make sense?
- **Information access:** Do actors only use information they should have?

## Calibration and Realism

This scenario is based on:
- Real AI Safety Summit dynamics (Bletchley Park 2023, Seoul 2024)
- Actual regulatory frameworks (EU AI Act, US executive orders, China's approach)
- Authentic stakeholder positions from public statements
- Technical debates from AI safety research community

The simulation should be realistic enough to:
- Generate plausible negotiation dynamics
- Identify critical decision points
- Test policy hypotheses
- Train human negotiators

## Analysis Suggestions

After running the scenario:

1. **Track coalition formation:** Who allies with whom and when?
2. **Identify critical turns:** When do breakthroughs or deadlocks occur?
3. **Compare actors:** Which strategies prove most effective?
4. **Measure consensus:** How does agreement level evolve?
5. **Analyze compromises:** What trades are made to reach consensus?
6. **Validate realism:** Do outcomes match expert expectations?

## Variations

Try running with modifications:

- **Different urgency levels:** Add/remove crisis pressure
- **Alternate coalitions:** Pre-form alliances before scenario starts
- **Model changes:** Use stronger/weaker models for different actors
- **Parameter tweaks:** Change number of turns, turn duration
- **Branching:** Branch from critical decision points to explore alternatives

## Research Applications

This scenario supports investigation of:
- International governance negotiation dynamics
- Coalition formation patterns
- Technical complexity's impact on policy
- Role of civil society in multilateral negotiations
- Effectiveness of different diplomatic strategies
- Conditions for successful international cooperation on emerging technology

## Notes

- This is a simulation, not a prediction
- Actor behavior reflects typical positions, not official policy
- Outcomes depend on prompting, models, and stochasticity
- Use for hypothesis generation and pattern exploration, not definitive forecasts
