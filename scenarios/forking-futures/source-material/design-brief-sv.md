# Scenarioskiss: tröga åtgärder under osäkra trajektorier

Arbetsanteckningar för det scenario som kan bli huvudbeviset i Talos-texten. Kontext och tes: [[Assignment - analysis capacity]]. Skapad 2026-08-24 efter diskussion; inget scenario byggt än.

**Syfte (beslutat 2026-08-24):** inte simulera hur stater kämpar mot varandra, utan utforska vilka typer av regleringar och policyåtgärder som har god effekt i en värld där avancerad AI är på väg att bli verklighet. **En regulator, enda aktören.**

## Grundidén (Johans skiss 24 augusti)

– Utvecklingstakten varierar mellan körningar: i vissa grenar RSI och sedan AGI inom 5–10 år, i andra blir AI aldrig övermänsklig utanför domäner där RLVR fungerar. Mer mera. Att ha en bredd i hur AI-utvecklingen fortskrider är en nyckel för att få ut det som behövs från simuleringarna.

– Slumpvisa händelser: massiva cyberattacker, bioterrorism, Taiwan-blockad (ev. beslut snarare än slump), datacenter i rymden som fungerar (eller inte), ekonomisk kollaps kring AI, med mera.

– Regulatorn har en bred palett av åtgärder med olika tröghet. Det är oftast suboptimalt att vänta tills verkligheten kräver åtgärden – man måste gissa i förväg, satsa brett, eller hitta no-regret-åtgärder.

Mål med ca 50 körningar: mönster i vilka åtgärdstyper som lönar sig, och vilka händelseklasser som är viktigast att monitorera för tidiga tecken.

## Varför denna design vinner

– Tidslinjen blir experimentell dimension istället för påstående. Texten slipper ta ställning i tidslinjedebatten; scenariot frågar hur utfall *skiljer sig* mellan grenar. Crux 1 ur analysdokumentet (RLVR-gränsen) återkommer som gren, inte som tes.

– Frågan "vilka händelser bör monitoreras" producerar direkt innehållet i den indikatoruppsättning som texten föreslår att JRC ska hålla. Scenariot genererar ett utkast till sitt eget svar.

– Tröga åtgärder mot snabba fönster demonstrerar kadensproblemet konkret – samma mismatch som anförs mot EU:s nuvarande foresight-arbete.

– No-regret-ramen knyter till Winter–Bullock (Radical Optionality): deras kapacitet att handla, textens kapacitet att se.

## Aktörfrågan: beslutat – regulator som ende aktör

**Beslutat 2026-08-24: bara regulatorn/policysättaren är aktör.** Labbarna fångas av metrics + events.

**Regulatorns identitet (beslutat): medvetet global och vag.** Den ska inte vara en exakt institution utan representera hur EU – eller FN eller liknande organisationer – vill försöka styra arbetet med AI-policy: vilket håll man satsar åt, vilka samtal som ska föras och med vilka. Läs ingen exakt organisatorisk analogi in i utfallen.

Motivering:

– Studieobjektet är policymakarens beslutsproblem under osäkerhet. Det är den ende vars val analyseras.

– Om tidslinjearmar sätts exogent (via draws) finns det ingen mening i att även låta labben "bestämma" kapabiliteten – då styr två mekanismer samma storhet. Labbarnas beteende är just den variation som grenarna redan fångar. Det vi vill försöka fånga är inte hur frontier-lab bör agera, utan hur reglering och policy bör se ut för att frontier-lab ska knuffas i rätt riktning – liksom att andra saker i världen ska fungera bra.

– Renare attribution: utfall varierar med (a) tidslinjegren och (b) regulatorns val – exakt de två variabler texten diskuterar.

– Billigare per körning → fler körningar inom budget och mindre prompt-yta att felsöka.

**Variant övervägd och avfärdad (för denna omgång): två regulatorer, USA + Kina.** Det är en annan simulering – ett koordinations-/konkurrensspel mellan jurisdiktioner ("reglerar vi, flyttas utvecklingen ditåt") snarare än ett beslutsproblem under osäkerhet. Intressant, men den frågan svarar inte på vad op-ed:en behöver (vad ska monitoreras, när måste insats komma, finns no-regret), den duplicerar delvis ai-safety-races tvåmaktstema och tappar EU-kopplingen helt om ingen regulator är europeisk. Sparas som kandidat för uppföljningsessäen eller som senare utbyggnad – enligt samma logik gäller: bygg inte scenariot för den andra texten innan den första finns.

Förlorar: strategisk återkoppling. Världen reagerar inte på politiken (t.ex. att reglering sänker ena labbens tempo medan den andra tar ikapp, eller att labben flyttar verksamhet utanför EU:s jurisdiktion). Kompromiss utan full aktör: konditionella kopplingar i metric-rules, t.ex. "höga utvärderingskrav sänker kapabilitettillväxttempo men minskar incidentsannolikheten". Uppgradera till andra aktören bara om prototypruns visar att världen känns orimligt passiv. Notera dock att åtgärder dels kan vara riktade åt exempelvis Kina eller USA och inte måste vara globala, och de kan dessutom slå olika – inklusive att Kina eller USA i hemlighet bryter mot överenskommelser.

## Tidslinjearmar

Tre armar, implementerade som initial-state draws (inte fri slump):

1. **Snabb** – RSI inom några år, AGI-tendens mot senare halva av tidshorisonten.
2. **Platå** – stadig men avtagande utveckling, ingen övermänsklighet inom horisonten.
3. **RLVR-begränsad** – stark i verifierbara domäner (kod, cyber), platt där ute.

Ca 15–20 repetitioner per arm ger totalen ~50. Grenarna måste separera tydligt redan i prototypen, annars är designen fel.

**Tidsupplösning och horisont (beslutat):** halvår per varv, start andra halvåret 2026, senaste varvet slutar 2035 – totalt 18 varv. Kvartal avfärdat: dubbelt varvtal och nästan dubblerad kostnad per körning utan tydlig analysvinst, medan halvår ändå fångar lagstiftnings-tempots grovkornighet (tröga åtgärder tar då 1–3 varv, dvs. 0,5–1,5 år – realistiskt). 2040 avfärdat: 28 varv blir alltmer spekulativt, och 2035 räcker gott. Obs budgetkonsekvens: 18 varv gör varje körning nästan dubbelt så dyr som ai-safety-races tio – antal repetitioner per arm får ge efter och beslutas efter `estimate`.

## Metrics (skiss, håll minimalt)

– `us_capability`, `cn_capability` – referenspunkter i stil med ai-safety-race (0–100).

– `incident_pressure` – aktuellt hotläge, drivs av händelser och sjunker med beredskap.

– `regulatory_capacity` / politiskt kapital – begränsar hur mycket regulatorn kan driva samtidigt; ökar efter framgångsrika insatser, rasar efter misslyckanden.

– `economic_context` – investeringsklimat, slås omkring av bubblerelaterade events.

– Kandidat: `public_sentiment_to_ai` – hur AI uppfattas och accepteras i samhället. Ger kategori-8-åtgärder något mätbart att flytta och matar politiskt kapital. Avgörs om prototypen visar behov.

Eventuellt också en metric som berättar hur stort gapet är mellan open weight-modeller och de slutna frontier-modellerna. Det är en faktor som kan spela mycket stor roll, både vad gäller maktkoncentration och risken för misuse.

Trosfel-mekaniken från ai-safety-race (dold tröskel vs trodd tröskel) passar inte här – det finns ingen sann tröskel med fast värde när tidslinjen själv varierar. Tidig-varnings-värdet kommer från signalhändelserna i stället.

## Events (skiss)

**Grindmekanism istället för synliga föregångare (beslutat).** Prekursorn ska inte vara särskilt synlig alls. Mekanismen: ett prekursorevent – eller en metriktröskel – *öppnar en grind* för en handfull eskaleringshändelser under de nästföljande varven. Grinden ökar sannolikheten men garanterar ingenting: tärningen slås fortfarande. Det som avspeglas i narrativet är atmosfär och sammanträffanden, aldrig prognoser – spelledaren ska aldrig skriva "det kommer ett genombrott snart" eller "massiva cyberattacker mot bankväsendet inom tre varv". Däremot behöver spelledaren se vilka grindar som är öppna (det framgår av eventutvärderingarna), så att narrativet kan skrivas sammanhängande utan att telegrafera.

Det är denna osynlighet som gör early-signs-frågan ärlig: om föregångaren är lika tydlig som storhändelsen finns inget monitoreringsproblem, och om den är helt osynlig finns inget att monitorera. Öppen grind + tyst narrativ ligger mitt emellan.

Kandidathändelser (prekurs → eskalering där par finns):

– Cyber: intrång/rekognosering → massiv kampanj.

– Bio: rapporter om modellstödd patogensyntes → verklig incident.

– Taiwan: spänningsökning → blockad.

– Kapabilitetshopp (konditionerat på gren + regler).

– Datacenter i rymden lyckas (accelererar snabb gren).

– Investerarkollaps kring AI.

– Läcka/whistleblower om farlig kapabilitet inuti labben.

– Internationellt förhandlingsfönster (öppnas kort, lätt att missa).

## Åtgärdspalett: bred, med kategorier (beslut 24 augusti)

Beslutat: paletten ska vara bred, och spelledaren ska aktivt bjuda in regulatorn att hitta på egna åtgärder. Det ställer krav på att spelledaren dynamiskt tolkar både effekter och genomförbarhet – det är den flexibilitet Scenario Lab är byggt för. Konstruktionerna nedan räddar analysbarheten trots friheten.

**Kategorier (utgångspunkt: "Effective Mitigations for Systemic Risks from General-Purpose AI" från vecka 1, breddad med samhällskategori som den paper-listan saknar).** Varje åtgärd – känd eller uppfunnen – taggas med en kategori, inklusive "Annat". En representant per kategori finns alltid i prompten som ankare:

1. **Utvärdering och tillsyn.** Representant: *Tredjepartsgranskning före release* – oberoende granskning av en modells farliga kapabiliteter innan den släpps. (Ur listan: audits, riskbedömningar, extern granskning av testprocedurer, förregistrering av träningskörningar.)

2. **Transparens och rapportering.** Representant: *Incidentrapportering* – allvarliga incidenter och nära-ögonblick rapporteras till ett gemensamt organ. (Ur listan: incidentrapportering, whistleblower-skydd, delning av safety cases.)

3. **Gränser och restriktioner.** Representant: *Intolerabla risktrösklar* – röda linjer satta av tredje part som stoppar utveckling eller drift när de passeras. (Ur listan: red lines, KYC, förbud mot högrisktillämpningar, fine-tuning/capability restrictions.)

4. **Kapacitet och forskning.** Representant: *Institutsbyggande* – egen utvärderingskapacitet och finansierad säkerhetsforskning. (Ur listan: vetted researcher access, advanced model access; jfr textens egen ask.)

5. **Beredskap och respons.** Representant: *Beredskapsplaner med övningar* – rutiner och spelade scenarier för snabba incidentklasser. (Ur listan: safety drills.)

6. **Samhällsmotståndskraft.** Representant: *Skyddsnätssatsning* – social trygghet och ompolering mot AI-driven arbetslöshet. (Den kategorin finns inte i mitigation-paperet men i systemic risks: labour market, R&D divide.)

7. **Internationell samordning.** Representant: *Avtal och dialogkanaler* – bindande överenskommelser och stående förhandlingsforum.

8. **Spridning, adoption och samhällspåverkan.** Representanter: *Digitala signaturer för säkra källor* – offentlig verksamhet och stora mediebolag signerar innehåll, stora plattformar uppmanas stödja verifiering. *Energisatsning* – bred utbyggnad av elproduktion mot AI:s behov. (Hit hör även t.ex. reglering av AI-companions riktade till unga, offentlig AI-adoption och utbildningssatsningar.)

9. **Annat.** Allt som inte passar – inklusive kombinationer och nypåhitt.

Kategori 8 är medveten och viktig: alla övriga pekar rakt mot globala risker, men verklig policymaking hanterar också åtgärder som bara indirekt gör det – och som ändå formar hur AI sprids och uppfattas i samhället. De är inte dekoration utan kopplas mekaniskt till världen: spridningens bredd ger ekonomisk vinning men också angreppsytta och misuse-exponering, förtroendet avgör hur mycket kapital som finns när incidenter kommer, och infrastrukturtempo påverkar kapabilitetsdriften. Två varningar samtidigt: scenariot ska inte bli en generell samhällssimulering (research questions står sig; samhällsåtgärderna är med eftersom de formger risklandskapet, inte för att utvärdera allt), och den enorma åtgärdsrymden hanteras av samma konstruktioner som tidigare – namngivna ankare, kategoritaggning, spelledarens rubrik. Skulle kategori 8 dominera utfall i vissa armar är det förresten ett legitimt huvudfynd: "den bästa hävarmen siktade inte mot frontieren".

**Åtgärders form: rubrik + kort mening.** Aldrig bara rubrik – meningen tvingar fram vad åtgärden faktiskt innebär, vilket också ger spelledaren något att tolka effekter ifrån.

**Bedömningsrubrik istället för effektlista.** Spelledaren bedömer varje åtgärd mot samma dimensioner, så tolkningen blir konsistent även för nyheter:

– kapitalkostnad: politiskt pris att införa

– ledtid: antal varv innan full effekt

– riktad effekt: vilka metrics, åt vilket håll, ungefärlig storlek

Politisk asymmetri gäller alltid: billigare att införa efter en incident än före. Det är mekanismen som gör no-regret-frågan intressant.

**Genomförande i faser – lean på LLM, inget sifferbygge.** Varje åtgärd har status: föreslagen → beslutad → under införande → fullt verkställd. Så länge den inte är fullt verkställd drar den kapital varje varv (kvalitativt: lägre/medel/hög belastning, inte punktsiffror). Effekten skalar med hur långt införandet kommit, bedömt av spelledaren. Balansen uppstår därav naturligt: satsa hårt på några få (långa kapitalbelastningar, snabb full effekt) eller många långsamma (spridd belastning, sen effekt). Ingen mer matematik än så.

**Taggningen är analysnyckeln.** Kategoritaggarna gör att `synthesize` kan gruppera mönster över körningar trots friheten – t.ex. om beredskapsåtgärder konsekvent slår begränsningar i vissa armar.

**En ny åtgärd per varv – beslutat, med prioritetsförklaring istället för ansträngningsreglage.** Regulatorn får komma med högst ett nytt förslag per varv. Ingen formell gräns finns på hur många åtgärder som kan vara igång samtidigt, men varje varv ska regulatorn också namnge en prioritet: vilken åtgärd som trycks hårdast just nu. Helhjärtad kontra halvhjärtad satsning uppstår då ur kapitalet istället för en reglage: när kapitalet räcker till flyttas allt framåt, när det kniper går bara den namngivna prioriteten vidare och övriga stannar. Vinsterna: rena, jämförbara körningar ("varv 5: drev tredjepartsgranskning"), ingen sifferbokföring att tolka, och koncentrera-eller-sprida är ändå ett verkligt val varje varv. En explicit två-åtgärdsregel eller hel/halv-reglade övervägdes och avförs – mer mekanik, sämre jämförbarhet, mot samma effekt som kapitalscarcity redan ger. Konstitutionen kräver rimlighetsmotivering för uppfinningar; referee-steget fångar orimliga effekter.

Två olika flexibilitetsknopar – skilj dem åt när du konfigurerar:

– Aktörens frihet att uppfinna åtgärder är endogen politik och styrs i aktörsprompten – ingen särskild inställning behövs.

– `emergent_events.enabled` handlar om exogena världshändelser utanför events.md. **Beslutat: på.**

## Research questions (under arbete)

– Slår tidiga, breda insatser reaktiva insatser i utfall – i vilka armar, under vilka villkor?

– Vilka föregångarhändelser föregår de största divergenserna mellan körningar? (→ indikatorkandidater.)

– Finns no-regret-paket: åtgärdskombinationer som aldrig är sämre och ofta bättre över alla tre armar?

Dessa ska in i scenario.yaml som `research_questions` så att `synthesize` svarar på dem explicit.

## Registerdisciplin (gäller från första prototypen)

– Strukturella mönster, inte policy-ranking. Formuleringar i stil med "reaktiva insatser kom sent i X av Y grenar", aldrig "modellen visar att åtgärd Z är bäst".

– Siffrorna är ramverksgenererade. Detta är scenarioexploration, varken syntes av evidens eller kalibrerad prognos – samma trespråt som analysdokumentet fastslagit.

– Op-ed:en använder distributionsfyndet + signalfyndet + kadensillustrationen. Interventionsanalys i fullt djup blir uppföljningsessäen – kortversionen är trailern.

## Praktisk plan

1. Beslut kvar: antal körningar per arm efter kostnadsestimat; scenario-namn. (Regulatorns identitet, prekursormodellering, emergent_events och notepad är beslutade – se respektive sektion.)

2. Bygg i repot enligt pipelinen (frame-scenario → create-scenario, se AGENTS.md). Framtida hem: `kodprojekt/Scenario Lab 3/scenarios/forking-futures/`.

3. Prototyp först: 2 varv × 3 armar. Kolla att armar separerar och att regulatorns beslut ser meningsfulla ut. Kostnadsuppskattning innan batch.

4. Batch via `batch-run --repeat` + initial-states, sedan `ensemble` (API-fritt) och `synthesize`.

5. Fallback reglerad: ger prototypen gröt, används ai-safety-race (12 kompletta körningar finns) som bevis i stället. Beslutspunkt senast i början av september, inför Auriane-samtalet i vecka 3.

## Konfigurationsbeslut

– `emergent_events.enabled: true` (exogena händelser utanför listan – mot förutfattade meningar).

– Notepad: ja, regulatorn använder notepad för planering över varv. Inget mer sofistikerat minne än så.

– Grindmekanismen implementeras som konditionella sannolikheter i events.md, med öppna grindar synliga i eventutvärderingarna men tysta i narrativinstruktionerna.

## Öppna frågor

– Antal körningar per arm – efter kostnadsestimat (`estimate`-kommandot).

– Hur många varv "under införande" rimligen tar per åtgärdstyp – kalibreras i prototypen.

– Namn (beslutat): `forking-futures`, visningsnamn "Forking Futures". Sparade kandidater för essän eller uppföljaren: *Atlas of Futures* (stående översiktsverk – resonerar direkt med asken till JRC), *Slow Levers, Fast World*, *Garden of Forking Paths*.

– Ska draws inom en arm variera mer än trajektorn (t.ex. startvärld)? Troligen nej i första omgången – håll armen ren.
