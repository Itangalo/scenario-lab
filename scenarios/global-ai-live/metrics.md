# Metrics for Global AI Live

All metrics use 0–100 index scales so workshop participants can read them at a glance. Direction is stated per metric: for `labor_displacement`, `eu_us_dependence`, and `us_china_tension`, HIGH means worse (more displacement, more dependence, closer to conflict). The four `*_capital` / `*_resources` metrics are spendable pools owned by one actor each: HIGH means more left to spend. Teams spend by describing what they do; the Game Master deducts the price.

## frontier_capability

**Description:** General frontier AI capability level across leading labs, relative to mid-2026 systems. HIGH = more capable systems.

**ID:** frontier_capability

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 30

**Reference points:**

- 10: Roughly 2024-level systems dominate deployment.
- 30: Mid-2026 frontier: strong agents for coding and knowledge work, still brittle outside checked domains.
- 60: Reliable autonomous agents across most cognitive work; AI researchers partly automated.
- 90: Systems that independently drive large R&D programs with minimal human direction.

## scientific_progress

**Description:** Pace at which AI accelerates real scientific and technical breakthroughs (medicine, computer science, natural sciences, mathematics). HIGH = faster breakthroughs reaching the world.

**ID:** scientific_progress

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 35

**Reference points:**

- 10: AI contributes little beyond literature search and data processing.
- 35: Mid-2026: real but scattered wins (protein design, materials screening, maths assistance) alongside hype.
- 60: AI-driven breakthroughs arriving yearly in several fields, some reaching clinics and factories.
- 90: Continuous pipeline of cures, materials, and proofs visibly raising living standards.

## labor_displacement

**Description:** Scale of AI-driven job loss and labor-market disruption. HIGH = more displacement and disruption (direction is worsening upward).

**ID:** labor_displacement

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 30

**Reference points:**

- 10: AI assists workers; hiring steady, gradual role change.
- 30: Mid-2026: entry-level hiring frozen in exposed white-collar roles; graduate market strained.
- 60: Broad layoffs across sectors; mid-career workers affected; retraining systems overwhelmed.
- 90: Mass structural unemployment; welfare and social order under severe strain.

## public_trust

**Description:** Public trust in AI systems and the institutions governing them. HIGH = more trust.

**ID:** public_trust

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 50

**Reference points:**

- 15: Broad backlash, protests, demands for bans.
- 40: Skeptical majority, trust concentrated in narrow uses.
- 50: Divided public, cautiously open.
- 70: Broad confidence in AI benefits and oversight.

## information_integrity

**Description:** Health of the shared information landscape: can citizens tell real from synthetic, and do elections and public debate run on trustworthy information. HIGH = healthier information environment.

**ID:** information_integrity

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 55

**Reference points:**

- 15: Synthetic content dominates; elections fought over fakes; no trusted verification.
- 40: Frequent deepfake scandals; verification tools partial and unevenly used.
- 55: Mid-2026: AI fraud and synthetic media already common, but mainstream channels mostly hold.
- 80: Provenance and detection widely deployed; public can check what is real.

## eu_us_dependence

**Description:** Europe's dependence on the United States for frontier AI (models, compute, supply chain). HIGH = more dependent, less sovereign room to act (direction is worsening upward).

**ID:** eu_us_dependence

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 60

**Reference points:**

- 20: Europe trains and serves competitive models on its own compute.
- 40: Competitive deployments, but frontier training still needs US infrastructure.
- 60: Mid-2026: Europe holds ~5% of world AI compute vs ~80% in the US; frontier access on US terms.
- 85: Frontier cut off or rationed at short notice; European deployments degrade without US supply.

## governance_strength

**Description:** Strength and coverage of effective AI governance: rules in force, oversight capacity, and compliance across blocs. HIGH = stronger governance.

**ID:** governance_strength

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 35

**Reference points:**

- 10: Voluntary pledges only, no enforcement.
- 35: Patchwork rules (EU AI Act partially enforced, US executive measures, Chinese licensing) with gaps.
- 60: Coordinated cross-bloc standards with real audits and incident reporting.
- 90: Binding international regime with verification.

## us_china_tension

**Description:** Level of US-China confrontation over AI and its flashpoints (compute chokepoints, Taiwan-adjacent incidents, military uses). HIGH = closer to hot conflict (direction is worsening upward; replaces the old cooperation-framed metric, reversed).

**ID:** us_china_tension

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 45

**Reference points:**

- 15: Stable rivalry with working safety dialogue and incident hotlines.
- 45: Mid-2026: export controls biting, thin dialogue, routine military signaling around Taiwan.
- 70: Direct confrontations (interdictions, collisions, cyber exchanges) with crisis management strained.
- 90: Open shooting between the powers; AI infrastructure a military target.

## us_gov_capital

**Description:** Spendable political capital and budget room of the US federal government. The team spends it by announcing programs, subsidies, and interventions; HIGH = more left to spend.

**ID:** us_gov_capital

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 60

**Reference points:**

- 0: Broke – ambitious moves stall or fail for lack of backing.
- 30: Tight – one flagship program crowds out everything else.
- 60: Comfortable – a flagship plus smaller moves in one year.
- 90: Dominant – back-to-back flagships without breaking stride.

## us_labs_resources

**Description:** Spendable resources of the US frontier labs: compute, talent, and cash. The team spends them by training runs, releases, and safety programs; HIGH = more left to spend.

**ID:** us_labs_resources

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 70

**Reference points:**

- 0: Tapped out – no major training run or release possible this year.
- 30: Tight – one frontier run consumes the year.
- 60: Strong – a frontier run plus product and safety work side by side.
- 90: Overflowing – several frontier-scale bets in parallel.

## china_resources

**Description:** Spendable resources of the Chinese state AI drive: funds, chip stockpiles, and mobilized talent. The team spends them by build-outs, subsidies, and programs; HIGH = more left to spend.

**ID:** china_resources

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 65

**Reference points:**

- 0: Strained – build-out stalls, programs shrink to Seed size.
- 30: Tight – one national priority at a time.
- 60: Solid – parity drive plus domestic deployment together.
- 90: Surge – crash programs on several fronts at once.

## eu_capital

**Description:** Spendable political capital and budget room of the European Union. The team spends it by enforcement pushes, subsidies, and joint programs; HIGH = more left to spend.

**ID:** eu_capital

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 55

**Reference points:**

- 0: Spent – enforcement without funds, announcements without backing.
- 30: Tight – one serious program (enforcement or capacity, not both).
- 60: Workable – a capacity program plus credible enforcement in one year.
- 90: Flush – EU-scale compute fund and full enforcement together.
