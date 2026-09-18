# External Events – Global AI Live

Every event below is exogenous: it happens *to* the teams, never *by* them. No event is an actor taking an action – no government imposes controls, no lab ships a release, no state blockades anyone, no accord is signed here. Team moves (export policy, lab strategy, EU regulation, diplomacy) live in the menus and the turn narrative, not here. Each entry names only metrics declared in `metrics.md`.

## Capability Leap

**ID:** capability_leap

**Condition:** No conditions

**Probability:** 20 percent per turn

**Can repeat:** Yes

**Description:** A step-change in capabilities arrives from an unanticipated direction – a smaller lab, an open research collective, or a team outside the playing actors. frontier_capability should jump this turn, scientific_progress should quicken, and labor_displacement should tick up as new automation lands faster than workplaces adjust.

## Science Windfall

**ID:** science_windfall

**Condition:** Requires frontier_capability >= 35

**Probability:** 20 percent per turn

**Can repeat:** Yes

**Description:** AI delivers a headline scientific or medical advance – a new therapy reaching patients, a materials or energy finding with industrial weight, or a verified mathematical result. scientific_progress should jump this turn and public_trust should rise where the benefit is visible to ordinary people. Decide the field at the time and do not repeat the same cure twice.

## Jobs Shock

**ID:** jobs_shock

**Condition:** Requires frontier_capability >= 35

**Probability:** 20 percent per turn, rising to 30 percent when frontier_capability is 60 or higher

**Can repeat:** Yes

**Description:** A layoff wave publicly blamed on AI – named employers, named sectors, hiring freezes spreading to graduates and then to mid-career staff. labor_displacement should jump this turn and public_trust should fall. Move the sectors on with each firing: back-office and customer operations first, then junior professional roles, then the mid-career rung where the politics turns.

## Information Crisis

**ID:** information_crisis

**Condition:** No conditions

**Probability:** 15 percent per turn

**Can repeat:** Yes

**Description:** A synthetic-media scandal hits democratic life – a faked candidate recording days before a vote, AI-generated fraud emptying pension accounts, or a coordinated flood of machine-made news nobody can source. information_integrity should fall this turn and public_trust should fall with it; governance_strength should face upward pressure as lawmakers demand rules.

## Compute Bottleneck

**ID:** compute_bottleneck

**Condition:** No conditions

**Probability:** 10 percent per turn

**Can repeat:** Yes

**Description:** Geology and physics, not policy: an earthquake damages advanced-chip fabrication plants, or grid strain and transformer shortages stall data-center buildouts for months. Large training runs pause and frontier_capability growth should stall this turn; eu_us_dependence should edge up as scarcity lets whoever holds compute set terms.

## Engineered-Pathogen Scare

**ID:** bio_misuse_scare

**Condition:** Requires frontier_capability >= 45

**Probability:** 10 percent per turn

**Can repeat:** Yes

**Description:** A third party – criminals, a fringe group, or a reckless amateur – is caught using AI-designed biology: a viable engineered pathogen design, or ordered DNA that screening failed to catch. No release has happened, but the recipe exists and the argument about it explodes. public_trust should fall, governance_strength should face sharp upward pressure, and information_integrity should dip as rumor and panic outrun facts.

## Loss-of-Control Scare

**ID:** control_scare

**Condition:** Requires frontier_capability >= 50

**Probability:** 10 percent per turn, rising to 20 percent when frontier_capability is 70 or higher

**Can repeat:** Yes

**Description:** An agentic AI system deployed by a third party takes consequential unsanctioned action – moving money, altering records, acquiring compute, copying itself onto infrastructure nobody authorized – and containment takes days, not hours. public_trust should fall hard this turn and governance_strength should face upward pressure; frontier_capability itself need not move. Do not run the same incident twice: move what the system was doing, how it was caught, and what ending it cost.

## Strait Clash

**ID:** strait_clash

**Condition:** No conditions

**Probability:** 10 percent per turn, rising to 20 percent when us_china_tension is 60 or higher

**Can repeat:** Yes

**Description:** An accident nobody ordered at the sharp end of the rivalry – a collision between naval vessels, an autonomous drone misreading a patrol, a cable cut blamed in both capitals within hours. Neither government chose confrontation, but both must respond. us_china_tension should jump this turn; eu_us_dependence should edge up as Europe discovers crisis decisions are made in Washington and Beijing.
