# Metrics för AI och skolan 2031

Alla metrics använder skala 0–6. Metrics ändras normalt med högst 1 steg per runda – större förändringar kräver exceptionella händelser, ackumulerat tryck över flera rundor, eller tydlig narrativ motivering.

## ai_tech_level

**Description:** Globalt tillgänglig AI-kapacitet relevant för skolan. Stiger över tid utifrån grundprogression. Varje nivå representerar en ny generation av AI-förmågor som blir tillgängliga.

**ID:** ai_tech_level

**Min:** 0

**Max:** 7

**Unit:** generation

**Starting value:** 1

**Reference points:**

- **0:** Pre-ChatGPT-era. AI är fortfarande en teknik för specialister.
- **1:** Generativ AI är allmänt tillgänglig (ChatGPT, Claude, Gemini). AI-administration och dokumentation används brett. Adaptivt lärande börjar dyka upp.
- **2:** Robust AI-tutoring och adaptivt lärande. AI-baserad bedömning används experimentellt.
- **3:** Prediktiv analys av elever. AI-läromedel börjar konkurrera med traditionella läromedel.
- **4:** AI-genererade läromedel dominerar. Autonoma lärassistenter testas.
- **5:** Autonoma lärassistenter används brett. AI tar över delar av undervisningen.
- **6:** AI-robotar börjar användas i arbetslivet. Skolan står inför grundläggande omprövning.
- **7:** AI-system övergår mänsklig nivå inom de flesta kunskapsdomäner.

## public_attitude_ai

**Description:** Allmänhetens inställning till AI i samhället, samlat över medborgare, föräldrar och politiker.

**ID:** public_attitude_ai

**Min:** 0

**Max:** 6

**Unit:** (skala)

**Starting value:** 3

**Reference points:**

- **0:** Stark negativ inställning. AI ses som ett hot mot barn, jobb och demokrati. Demonstrationer och politiska krav på stopp.
- **2:** Övervägande skeptisk. AI omtalas oftast i termer av risker.
- **3:** Splittrad och försiktigt nyfiken. Både entusiaster och skeptiker hörs.
- **4:** Övervägande positiv. AI ses som en möjlighet, men med vakna ögon.
- **6:** Stark teknikoptimism. AI omfamnas brett, kritiker marginaliseras.

## equity_in_schools

**Description:** Likvärdighet i svensk skola – i vilken grad alla elever får tillgång till god undervisning oberoende av skola, ort eller bakgrund. Påverkas särskilt av hur AI fördelas och används.

**ID:** equity_in_schools

**Min:** 0

**Max:** 6

**Unit:** (skala)

**Starting value:** 3

**Reference points:**

- **0:** Stark segregation. Resursrika skolor erbjuder kvalitativt annorlunda undervisning än svaga.
- **2:** Tydliga skillnader. AI har börjat förstärka glappet.
- **3:** Genomsnittlig svensk nivå 2026. Skillnader finns men anses hanterbara.
- **4:** Likvärdigheten har förbättrats. AI används medvetet för att utjämna.
- **6:** Hög likvärdighet. AI fungerar som ett aktivt utjämnande verktyg.

## student_outcomes

**Description:** Elevernas kunskapsutveckling nationellt. Reflekterar både rena resultat och kvaliteten i lärandet.

**ID:** student_outcomes

**Min:** 0

**Max:** 6

**Unit:** (skala)

**Starting value:** 3

**Reference points:**

- **0:** Allvarlig kunskapskris. Elever lämnar grundskolan med stora luckor.
- **3:** Genomsnittlig svensk nivå 2026.
- **6:** Stark kunskapsutveckling. Eleverna lär sig mer än tidigare generationer.

## staff_satisfaction

**Description:** Skolhuvudmännens lärares trivsel och vilja att stanna i yrket. Påverkar rekrytering och behållning.

**ID:** staff_satisfaction

**Min:** 0

**Max:** 6

**Unit:** (skala)

**Starting value:** 3

**Reference points:**

- **0:** Massflykt från läraryrket.
- **3:** Genomsnittlig nivå – många trivs men en del överväger att lämna.
- **6:** Yrket är attraktivt och lärare stannar.

## skolhuvudman_budget

**Description:** Skolhuvudmännens samlade ekonomiska utrymme. Påverkar vad de har råd att satsa på AI, kompetensutveckling och rekrytering.

**ID:** skolhuvudman_budget

**Min:** 0

**Max:** 6

**Unit:** (skala)

**Starting value:** 3

**Reference points:**

- **0:** Krisbudget. Huvudmännen tvingas till nedskärningar.
- **3:** Stram men hanterbar.
- **6:** Stark ekonomi, utrymme för satsningar.

## edtech_adoption

**Description:** Andelen svenska skolor som aktivt använder EdTech-sektorns AI-verktyg.

**ID:** edtech_adoption

**Min:** 0

**Max:** 6

**Unit:** (skala)

**Starting value:** 1

**Reference points:**

- **0:** Närmast ingen användning.
- **3:** Cirka hälften av skolorna använder något AI-verktyg från EdTech.
- **6:** Bred och djup användning av AI-verktyg i nästan alla skolor.

## regulatory_climate

**Description:** Hur gynnsamt det regulatoriska klimatet är för EdTech – ju högre, desto färre hinder för försäljning och produktintroduktion.

**ID:** regulatory_climate

**Min:** 0

**Max:** 6

**Unit:** (skala)

**Starting value:** 3

**Reference points:**

- **0:** Mycket strikt reglering. EdTech har svårt att verka.
- **3:** Standardvillkor – GDPR, skollag, viss AI-tillsyn.
- **6:** Mycket gynnsamt – snabbspår, generösa undantag, lågt motstånd.

## voter_trust

**Description:** Allmänhetens förtroende för regeringen och Skolverket i AI-skolfrågor.

**ID:** voter_trust

**Min:** 0

**Max:** 6

**Unit:** (skala)

**Starting value:** 3

**Reference points:**

- **0:** Förtroendekris, krav på regeringsskifte i skolfrågor.
- **3:** Genomsnittligt förtroende.
- **6:** Stark tilltro – staten ses som kompetent navigatör.

## international_standing

**Description:** Sveriges anseende internationellt vad gäller AI i skolan.

**ID:** international_standing

**Min:** 0

**Max:** 6

**Unit:** (skala)

**Starting value:** 3

**Reference points:**

- **0:** Sverige ses som en eftersläntrare.
- **3:** Mittenfält bland jämförbara länder.
- **6:** Sverige ses som föregångare och förebild.

## working_conditions

**Description:** Lärarnas upplevda arbetsförhållanden – arbetsbelastning, autonomi, professionell utveckling.

**ID:** working_conditions

**Min:** 0

**Max:** 6

**Unit:** (skala)

**Starting value:** 3

**Reference points:**

- **0:** Akuta arbetsmiljöproblem, bred utbrändhet.
- **3:** Genomsnittliga svenska förhållanden.
- **6:** Hållbara arbetsförhållanden, lärare har autonomi och utrymme.

## job_security

**Description:** Lärarnas upplevda anställningstrygghet – risken att AI ersätter lärartjänster.

**ID:** job_security

**Min:** 0

**Max:** 6

**Unit:** (skala)

**Starting value:** 4

**Reference points:**

- **0:** Akut existentiell oro – lärare ersätts av AI i stor skala.
- **3:** Begynnande oro, debatt om AI:s gränser.
- **4:** Trygg position – AI ses som komplement.
- **6:** Mycket trygg – professionell ställning starkare än tidigare.
