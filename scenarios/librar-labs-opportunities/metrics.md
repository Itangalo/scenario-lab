# Metrics for Librar Labs – US Market Opportunities

## librar_us_market_reach

**Description:** Librar Labs' penetration of the addressable US K-12 school library market. Approximately 130,000 K-12 schools in the US are considered addressable. A value of 1 means roughly 1,300 schools are active Librar users.

**ID:** librar_us_market_reach

**Min:** 0

**Max:** 100

**Unit:** percent

**Start value:** 1

**Reference points:**

- 1: Very early stage; Librar is essentially unknown in the US market.
- 5: Librar has become a recognized name in early adopter circles; pilot programs underway in several districts.
- 15: Meaningful market presence; Librar is regularly evaluated alongside established vendors.
- 30: Librar is a top-three choice in a significant share of procurement processes.
- 60: Dominant player; Librar has displaced traditional ILS vendors as the default in many states.

## school_digital_readiness

**Description:** The degree to which US K-12 schools have the digital infrastructure, budget, and staff capacity to adopt modern AI-powered library software. Encompasses device penetration, internet connectivity, IT support staffing, and administrative willingness to change.

**ID:** school_digital_readiness

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 42

**Reference points:**

- 20: Most schools lack infrastructure; cloud software is impractical for many.
- 42: Uneven landscape; urban and suburban schools are often ready, rural schools significantly less so.
- 60: A clear majority of schools can onboard new digital library tools with modest support.
- 80: Digital readiness is near-universal; technology barriers are no longer a significant adoption obstacle.

## competitive_pressure

**Description:** The intensity of competitive activity targeting Librar Labs' addressable market. High values mean well-resourced incumbents and new entrants are actively blocking, undercutting, or acquiring their way into Librar's space.

**ID:** competitive_pressure

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 35

**Reference points:**

- 15: Incumbents are passive; market is fragmented and slow-moving.
- 35: Standard competitive dynamics; vendors compete on price and features without aggressive tactics.
- 55: Competitors begin bundling or pricing aggressively to defend accounts; Librar faces increased churn risk.
- 75: Hostile competitive environment; major players acquire competitors or lock in districts with multi-year contracts.
- 90: Near-consolidation; one or two incumbents control procurement in most states, making entry extremely difficult.

## content_platform_integration

**Description:** The degree to which school library systems in the US are integrated with digital content platforms (e-books, audiobooks, podcasts, music). High values mean students can seamlessly access digital content from within their library system; low values mean content is siloed.

**ID:** content_platform_integration

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 20

**Reference points:**

- 10: Content is almost entirely physical; digital content is accessed through separate, disconnected apps.
- 20: Early integrations exist (e.g., OverDrive/Libby linked from some ILS), but are clunky and rarely used.
- 45: Unified discovery across physical and digital content is common; students expect one search interface.
- 70: AI-powered recommendations across all content types are the norm; content platforms compete to be inside library systems.
- 90: Library systems have become the primary discovery and access layer for all educational content – physical and digital.

## literacy_impact_evidence

**Description:** The strength and visibility of the evidence base linking modern school library systems (especially AI-powered ones) to measurable student literacy improvements. High values mean Librar's impact claims are backed by published studies, government endorsements, and district case studies.

**ID:** literacy_impact_evidence

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 15

**Reference points:**

- 10: Only internal case studies and anecdotal reports; procurement committees are skeptical.
- 15: A handful of district case studies published; 67% reading increase claim is known but not independently verified.
- 35: Several peer-reviewed studies or government-commissioned reports confirm library system quality correlates with literacy.
- 60: Librar specifically is cited in state or federal policy documents as an evidence-based intervention.
- 85: Strong research consensus; Librar's outcomes data influences national literacy policy and spending.

## us_education_funding

**Description:** The availability of US federal and state funding streams that schools can direct toward library technology. Encompasses E-Rate program scope, Title I allocations, ESSA funding, and state-level literacy initiatives.

**ID:** us_education_funding

**Min:** 0

**Max:** 100

**Unit:** index

**Start value:** 45

**Reference points:**

- 20: Budget cuts dominate; schools are in austerity mode and library tech is deprioritized.
- 45: Baseline availability; some funding exists but procurement is slow and competitive.
- 60: Meaningful funding expansion; new federal or state programs specifically include library software.
- 80: Significant tailwind; library technology becomes a named priority in multiple funding streams, shortening procurement cycles.
