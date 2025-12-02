# Sverige och AI fram till 2030

Skiss på ett scenario för att utforska hur svenska samhället påverkas av AI-utvecklingen.

## Syfte

- Testa Scenario Lab-ramverket med ett genomtänkt scenario
- Utforska realistisk dynamik mellan svenska aktörer
- Identifiera saknade features eller designproblem i ramverket

## Tidsram

Start: 1 januari 2026 (nästan nutid)
Slut: 31 december 2030

## Aktörer (preliminär lista)

- **Riksdag + Regering** - Politiskt beslutsfattande, reglering, statliga satsningar. JOHAN: Bör dessa vara två olika aktörer?
- **Fackföreningar** - Arbetsmarknadsperspektiv, omställning, förhandlingar. JOHAN: Jag håller gärna dessa som en enda aktör, även om det finns många olika fackföreningar. Tror du att det funkar?
- **Media** - Opinionsbildning, granskning, egen AI-användning
- **Näringsliv** - Implementation, innovation, konkurrenskraft
- **"Svenska folket"** - Opinioner, adoption, arbetsmarknadspåverkan

### Öppen fråga: Hur modellera "svenska folket"?

Alternativ:

- Dela upp i segment (teknikskeptiker vs early adopters)
- Modellera via world state istället (opinionsundersökningar)
- Passiv kraft som påverkar andra aktörers handlingsutrymme

JOHAN: Jag lutar mot att ha dem som world state och passiv kraft som påverkar andra aktörer. Även om svenska folket har en stark inverkan på politiska beslut är det för diffust för att kunna modellera som en aktör. Men då kanske world state ska ha ett kort avsnitt som beskriver hur olika delar av befolkningen tänker/agerar kring AI?

## Externa händelser (exogenous events)

### Bakgrundstrender (scheduled)

- Global AI-utveckling (nya modeller, kapabiliteter). JOHAN: Här tänker jag att vi ska ha en skala, kanske med utgångspunkt i METR:s undersökningar om long tasks. Det kan avspegla hur avancerad AI som finns. Det blir då också lätt att modellera olika takt på utveckling.
- EU-reglering (AI Act implementation, nya direktiv)

### Geopolitik (conditional/random)

- USA:s politiska riktning (presidentval 2028)
- Informationskrigsföring från Ryssland/Kina/Iran
- Global maktbalans och handelsrelationer

### Black swans (random, låg sannolikhet)

- AI-säkerhetsincident (stor eller liten). JOHAN: Det här kan vara dels något globalt, dels något i Sverige. I det senare fallet kan det vara en ung person som tar livet av sig, mycket på grund av konversationer med en AI-vän.
- Stort AI-genombrott (AGI-nära). JOHAN: Jag tänker att recursive self improvement är ett sådant genombrott, alternativt är en sådan händelse inte alls en black swan utan snarare något som sker gradvis när AI i allt större grad används för att förbättra AI-utveckling. En annan variant är en ny arkitektur, som har lika stor betydelse som transformers. En annan tanke är att AI-genombrott antingen kan ge ett enstaka hopp i AI-kapacitet, eller en varaktig ökning av hastigheten i AI-utveckling.
- Ekonomisk kris. JOHAN: En möjlighet är kollaps kring AI-investeringar, vilket inte känns osannolikt inom det närmsta året.
- Geopolitisk kris (t.ex. Taiwan, Baltikum, Mellanöstern). JOHAN: Särskilt konflikt över Taiwan är intressant. Det kan vara het konflikt eller en blockad som Kina inleder.
- Frontier AI klassas som nationell säkerhet i USA. Åtkomsten till de bästa amerikanska modellerna begränsas kraftigt utanför USA, och även inuti USA hålls kunskap om och åtkomst till de bästa modellerna strikt begränsat. Detta är vad som ibland kallas "A Manhattan project for AI".

## Scenariovarianter

Tre huvudspår baserat på AI-utvecklingstempo:

1. **Långsam** - Inkrementella förbättringar, inga stora genombrott
2. **Snabb** - Kontinuerliga framsteg, tydlig påverkan på arbetsmarknad
3. **Explosiv** - Stora genombrott, potentiellt AGI-nära kapabiliteter

JOHAN: Jag tänker att detta handlar om hur kurvan på METR:s skala för långa uppgifter fortsätter. Nuvarande trend säger dubbling var sjunde månad, eller eventuellt var fjärde månad för resonerande språkmodeller (men det är tveksamt). Frågan är då om kurvan fortsätter att vara exponentiell i samma takt, om den lugnar ner sig, eller om det till och med accelererar.

Kan implementeras via batch configs med olika exogenous-events-filer.

## Branch points

- **Riksdagsval i Sverige 2026** - Kan eventuellt innebära större politiskt engagemang inom AI, eller fortsatt business as usual
- **USA presidentval 2028** - Manuell branching för olika utgångar

## Metrics att följa

| Metric | Beskrivning | Typ |
|--------|-------------|-----|
| AI-kapabilitet | Hur avancerad AI som finns globalt | LLM-extraction |
| AI-användning jobb | Andel svenska arbetsplatser med AI-verktyg | LLM-extraction |
| AI-användning befolkning | Allmänhetens användning av AI | LLM-extraction |
| Allmänhetens inställning | Positiv/negativ syn på AI | Scale (-10 to +10) |
| Statliga AI-satsningar | Medel som satsas från staten | LLM-extraction (MSEK) |
| Arbetslöshet | Arbetslöshet så som den rapporteras av Arbetsförmedlingen | LLM-extraction |

JOHAN: Jag vet inte vad "LLM-extraction" avser i sammanhanget, men jag tänker att det är bra att ha definierade skalor. Utkast:
* AI-kapabilitet: Baserat på METR-studien. Hur långa uppgifter inom mjukvaruutveckling klarar AI-modeller av i hälften av fallen? November 2025 säger 2:42, och dubblering av detta var sjunde månad.
* AI-användning i jobb: Andel av svenska arbetstagare som uppger att de använder AI-verktyg i arbetet. (Okända värden i november 2025, sannolikt 40–50 procent.)
* AI-användning befolkning: Andel av svenskar 11–80 år som uppger att de använder AI-verktyg regelbundet, privat eller på jobbet. (Sannolikt 45–50 procent i november 2025.)
* Allmänhetens inställning: Skala –10 till +10, som både avspeglar hur många som lutar mot generellt positiv/negativ inställning, och hur starka dessa åsikter är.
* Arbetslöshet: Arbetslöshet så som den rapporteras av Arbetsförmedlingen. Meningsfullt eftersom hög arbetslöshet påverkar så många saker i samhället. Det är intressant om arbetslöshet är koncentrerad till exempelvis unga eller särskilda branscher, men det här får duga som mått.

## EU:s roll

Modelleras som del av omvärlden (exogenous events) snarare än egen aktör:

- AI Act-implementation och efterlevnad
- Eventuell minskning av reglering genom AI Act eller GDPR
- Nya regleringsinitiativ
- Digital suveränitet-satsningar
- Påverkar svenska aktörers handlingsutrymme

## Öppna frågor

- [ ] Hur detaljerad ska AI-utvecklingen vara i exogenous events?
- [ ] Vilken tidsupplösning? (kvartal, halvår, år?) JOHAN: Jag tror att halvår är en bra upplösning.
- [ ] Ska vi ha regionala skillnader (storstad vs glesbygd)?
- [ ] Hur hantera val 2026 (riksdag) och 2028 (USA)? JOHAN: Jag tror att det är enklast att hantera som branching i scenariot, inte att försöka simulera/förutsäga hur utfallet blir. I båda fallen spelar det egentligen mindre roll vilka som vinner valen, utan snarare vilken agenda de har (eller saknar) när det gäller AI.

## Nästa steg

1. Förfina aktörslistan och deras mål/begränsningar
2. Skissa på initial world state
3. Definiera exogenous events mer konkret
4. Bestämma tidsupplösning och antal turns
5. Skapa första utkast av scenario.yaml

