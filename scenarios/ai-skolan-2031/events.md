# Externa händelser – AI och skolan 2031

## Tekniskt genombrott

**ID:** tech_breakthrough

**Condition:** No conditions

**Probability:** 15 percent per round.

**Can repeat:** Yes

**Description:** Ett genombrott i AI-utveckling – ny arkitektur, träningsmetod eller skalning – ger ett oväntat språng. ai_tech_level stiger med 2 denna runda istället för det normala 1. Allmänheten uppmärksammar utvecklingen och public_attitude_ai påverkas något (kan både stiga och sjunka beroende på sammanhanget).

## Finansiell oro kring AI

**ID:** ai_financial_unrest

**Condition:** No conditions

**Probability:** 8 percent per round.

**Can repeat:** No

**Description:** Investerare börjar tvivla på AI-bolagens värderingar och pengar dras tillbaka. ai_tech_level stiger inte denna runda. edtech_adoption-tillväxt bromsas. Skolhuvudmännens budget kan tillfälligt få utrymme när stora upphandlingar skjuts på framtiden.

## Allvarlig AI-incident kopplad till skola

**ID:** ai_incident_school

**Condition:** Requires ai_tech_level >= 2 and edtech_adoption >= 2

**Probability:** 8 percent per round when edtech_adoption is 2-3, 14 percent when 4 or higher. Reduced by half if regulatory_climate is 2 or lower (strict reglering har minskat risken).

**Can repeat:** Yes

**Description:** En allvarlig incident i skolmiljö – diskriminerande bedömning, integritetsläcka, AI-driven mobbning, eller pedagogisk skandal. public_attitude_ai sjunker med 1. voter_trust sjunker med 1. EdTechs regulatory_climate sjunker med 1. Om regulatory_climate är 4 eller högre och ingen tillsynsmyndighet finns, sjunker dessutom equity_in_schools med 1 (incidenten drabbar resurssvaga skolor hårdast).

## EU-finansiering för AI i skolan

**ID:** eu_funding

**Condition:** No conditions

**Probability:** 12 percent per round, ökar till 20 percent om public_attitude_ai är 4 eller högre.

**Can repeat:** Yes

**Description:** EU lanserar en finansieringsomgång riktad mot AI i utbildning. skolhuvudman_budget stiger med 1. Om equity_in_schools är 2 eller lägre, stiger international_standing också med 1 (riktade insatser uppmärksammas).

## Hårda kontroller av AI-verktyg i skolan

**ID:** strict_ai_controls

**Condition:** Requires that the AI Incident in School event has occurred previously, or public_attitude_ai is 1 or lower.

**Probability:** 25 percent per round when conditions are met.

**Can repeat:** No

**Description:** Skolverket eller datainspektionen inför hårda kontroller av AI-verktyg i skolan. regulatory_climate sjunker med 1. edtech_adoption sjunker med 1 om EdTech inte aktivt mitigerar genom anpassningar eller avtal. equity_in_schools stiger med 1 (regleringen jämnar ut skillnader). voter_trust stiger med 1.

## Effektiva men dyra AI-verktyg lanseras

**ID:** premium_ai_tools

**Condition:** Requires ai_tech_level >= 3

**Probability:** 18 percent per round when conditions are met.

**Can repeat:** Yes

**Description:** En ny generation kraftfulla AI-verktyg lanseras till hög kostnad. Resursrika skolhuvudmän får student_outcomes +1 om de prioriterar inköp (kostar skolhuvudman_budget –1). equity_in_schools sjunker med 1 oavsett, eftersom inte alla har råd. EdTechs edtech_adoption stiger med 1.

## Riksdagsval

**ID:** election

**Condition:** Turn is 3.

**Probability:** 100 percent (fast timing).

**Can repeat:** No

**Description:** Riksdagsval äger rum. Om voter_trust är 2 eller lägre vid valet, sker en regeringsförändring – statens pågående initiativ försenas och voter_trust återställs till 3 (nytt mandat). Om voter_trust är 4 eller högre, stiger den med 1 ytterligare (mandatet stärks). AI-frågor i skolan har varit en valfråga och staten får utrymme att driva en ny policyriktning.

## Lärarstrejk

**ID:** teacher_strike

**Condition:** Requires working_conditions <= 1, or that Sveriges Lärare har eskalerat fackliga handlingar.

**Probability:** 35 percent per round when conditions are met.

**Can repeat:** Yes

**Description:** Lärare strejkar mot arbetsförhållandena, ofta i samband med AI-omställningen. staff_satisfaction sjunker med 1. student_outcomes sjunker med 1. working_conditions stiger med 1 (kraven hörsammas delvis). voter_trust sjunker med 1. Om en statlig flerårig reform pågår, försenas den.

## Sverige som föredöme

**ID:** sweden_as_model

**Condition:** Requires equity_in_schools >= 4 and turn is 3 or later.

**Probability:** 30 percent per round when conditions are met.

**Can repeat:** No

**Description:** Sverige uppmärksammas internationellt för en lyckad navigering av AI i skolan. international_standing stiger med 1. public_attitude_ai stiger med 1. voter_trust stiger med 1. Den positiva uppmärksamheten ger ny energi i samtliga aktörers arbete.
