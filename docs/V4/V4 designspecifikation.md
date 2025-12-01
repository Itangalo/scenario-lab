# Scenario Lab V4 – Designspecifikation

## Bakgrund och syfte

Scenario Lab är ett verktyg för att utforska möjliga framtider, särskilt kopplade till AI-utveckling och dess samhällseffekter. Syftet är att:

- Upptäcka effekter och mekanismer som inte är uppenbara i förväg
- Identifiera åtgärder som är avgörande för olika utfall
- Hitta tipping points och kritiska samband
- Förstå hur black swan-händelser påverkar beroende på när de inträffar
- Få kvantitativa mått på hur vanliga olika utfall är (genom många körningar)

## Designprincip: Lean into LLM

V4 bygger på principen att låta LLM:er hantera komplexitet i världen istället för att koda den i Python. Detta ger:

- **Skalbarhet** – scenarion blir bättre automatiskt när LLM:er förbättras
- **Transparens** – världsmodellen uttrycks i naturligt språk, inte kod
- **Emergenta samband** – LLM:en kan upptäcka kopplingar som inte specificerats i förväg
- **Enklare kod** – Python orkestrerar, LLM:er resonerar

## Arkitekturöversikt

### Körningsloop

```
Varje runda:

0. FÖRBEREDELSE (Orchestrator)
   - Ladda state från förra rundan

1. EXTERNA HÄNDELSER (Game Master)
   - Läser händelselistan
   - Bedömer vilka villkor som är uppfyllda
   - Returnerar namn och sannolikhet för de som kan triggas
   - Orchestrator exekverar check_event, vilket avgör vilka händelser som inträffar

2. AKTÖRER AGERAR (Aktörs-LLM:er)
   - Ser: metrics, narrativ, egna mål, triggade händelser
   - Justerar sina mål om det finns goda anledningar
   - Beskriver sina åtgärder i fritext

3. METRIC RULES ÖVERSYN (Game Master)
   - Granska och eventuellt uppdatera Metric Rules

4. UPPDATERA VÄRLDSBESKRIVNING (Game Master)
   - Läser aktörernas åtgärder + triggade händelser
   - Applicerar Metric Rules
   - Skriver narrativ sammanfattning

6. SPARA (Orchestrator)
   - Metrics, narrativ, Metric Rules, triggade händelser
```

### Komponenter

**Game Master (LLM)**
- Äger Metric Rules och kan modifiera dem under körning
- Bedömer villkor för externa händelser (i klartext), medan sannolikheter exekveras i python
- Äger Metrics och kan ändra dem
- Skriver narrativ sammanfattning

**Aktörer (LLM:er, körs parallellt)**
- Har mål som kan justeras över tid
- Ser: metrics, narrativ, egna mål, triggade händelser från innevarande runda
- Beslutar åtgärder i naturligt språk (ingen fördefinierad action-lista)
- Vet inte vad andra aktörer gör samma runda

**Orchestrator (Python)**
- Anropar LLM:er i rätt ordning
- Avgör utfall när externa händelser är beroende av slump
- Sparar och laddar state
- Loggar allt för efteranalys
- Håller reda på vilka externa händelser som inträffat, och undviker att engångshändelser upprepas

## Metrics

### Principer

- **Få metrics** (5-10 stycken) – tvingar fram meningsfullt resonemang
- **Tydliga skalor** – varje metric har definierad skala och riktlinjer för vad olika värden betyder i praktiken
- **Ingen hårdkodad dynamik** – samband hanteras via Metric Rules

### Exempel (sweden-ai-2030)

| Metric | Skala | Beskrivning | Exempel |
|--------|-------|-------------|---------|
| ai_capability | 0–1000 | Hur långa uppgifter AI klarar i hälften av fallen. Startvärde ~3h. | 8: AI-agenter kan utföra många datorbaserade uppgifter ungefär på nivå av en junior medarbetare. 24: AI-agenter kan utföra många datorbaserade uppgifter ungefär på nivå av en medelerfaren medarbetare. 100: AI-agenter kan utföra många datorbaserade uppgifter ungefär på nivå av en erfaren medarbetare. |
| ai_adoption_sweden | 0-100 | Andel av befolkning som regelbundet använder frontier AI-teknik. | 10: AI är endast för early adoptors, generell medvetenhet om tekniken är mycket låg. 50: AI anses som allmängods av de som använder tekniken, många av de som inte använder den har grundläggande medvetenhet om frontier AI. 80: Genomslaget i samhället är mycket stort. Vissa utsatta grupper saknar fortfarande AI-kompetens. |
| unemployment | 0–100 | Arbetslöshet enligt Arbetsförmedlingens definition. | 5: Låg arbetslöshet. 10: Arbetslöshet tas upp som ett problem i nyheter. 20: Hög arbetslöshet leder till oro och protester, särskilt bland grupper där arbetslösheten är särskilt hög. |
| public_sentiment_to_ai | -10 till +10 | Allmänhetens inställning till AI | -10: Demonstrationer och protester sker regelbundet. -5: AI beskrivs i media regelbundet som ett problem eller riskfyllt. 5: AI beskrivs i media regelbundet som en källa till möjligheter och en god framtid. |

## Metric Rules

En lista i naturligt språk som styr hur metrics förändras. Game Master kan lägga till, ta bort, eller modifiera regler under körningens gång.

Exempel:

1. ai_capability dubbleras varje halvår
2. När ai_capability ökar snabbt trycker det ner ai_adoption_sweden
3. Hög unemployment minskar public_sentiment_to_ai

### Uppdatering

Varje runda granskar Game Master listan och kan:
- Modifiera befintliga regler
- Lägga till nya regler baserat på vad som hänt ("Starka sociala skyddsnät har införts → unemployment påverkar government_mandate mindre")
- Ta bort regler som inte längre gäller

Ändringar motiveras explicit och sparas i loggen.

## Externa händelser

### Format

```
Händelse: [Namn]
ID: [ID]
Villkor: [När kan den inträffa? Krav på metrics? I klartext.]
Sannolikhet: [Sannolikhet att händelsen inträffar under en runda, givet att villkor är uppfyllda]
Kan upprepas: [Ja/Nej - kan händelsen ske flera gånger? Frivillig – default är att händelser inte upprepas]
Beskrivning: [Vad händer och vilka effekter får det? Beskrivning i klartext.]
```

### Exempel

```
Händelse: Taiwan-blockad
ID: tawian_blockade
Villkor: Kan inträffa från runda 3.
Sannolikhet: 10 procent
Kan upprepas: Nej
Beskrivning: Kina inleder blockad av Taiwan. Global chipproduktion störs kraftigt. Så länge blockaden pågår går AI-utvecklingen mycket långsamt framåt. Priser på elektronik går upp, men datorchip utöver de av toppkvalitet går fortfarande att få tag på. Geopolitisk osäkerhet ökar dramatiskt. Varje efterföljande runda är det 50 procent chans att blockaden får ett fredligt slut och 10 procent risk att den övergår i en militär konflikt.

Händelse: Personlig AI-incident i Sverige
ID: ai_incident_1
Villkor: Kräver ai_adoption_sweden > 20.
Sannolikhet: 10 procent
Kan upprepas: Ja
Beskrivning: En tonåring tar sitt liv efter intensiv kontakt med en AI-kompanjon. Stor medieuppmärksamhet. Krav på reglering ökar.

Händelse: Attack med stöd av AI
ID: ai_incident_2
Villkor: Kräver ai_capability > 20.
Sannolikhet: 5 procent
Kan upprepas: Ja
Beskrivning: En terroristattack eller ett massivt cyberangrepp genomförs i något västland, med många döda eller stora ekonomiska kostnader. Det visar sig att attacken gjorts möjlig på grund av AI. Stor medieuppmärksamhet. Krav på reglering ökar.

Händelse: Strejk
ID: strike
Villkor: Kräver unemployment > 12.
Sannolikhet: Dubbla värdet på unemployment, i procent
Kan upprepas: Ja
Beskrivning: Fackförbund inleder strejk mot AI-implementering. Produktivitet minskar tillfälligt, spänningar ökar.

Händelse: Stort AI-genombrott
ID: ai_breakthrough
Villkor: Inga villkor.
Sannolikhet: 3 procent
Kan upprepas: Ja
Beskrivning: En ny arkitektur eller träningsmetod ger dramatiskt förbättrade AI-kapabiliteter. ai_capability tar ett stort steg uppåt och utvecklas sedan enligt samma mönster som innan.

Händelse: AI-utvecklingen planar ut
ID: ai_stall
Villkor: Inga villkor.
Sannolikhet: 3 procent
Kan upprepas: Ja
Beskrivning: Utvecklingen av AI stöter på motstånd som visar sig svår att övervinna. AI-utvecklingen minskar till en långsam linjär takt och förblir så tills ett nytt AI-genombrott sker. AI-utvecklingens inbromsning skapar oro på finansmarknaden men i övrigt är den stora effekten att effekterna av allt kraftfullare AI uteblir.
```

### Hantering

1. Orchestrator ger Game Master händelselistan, där engångshändelser som redan inträffat rensats bort.
2. Game Master läser händelselistan och bedömer vilka villkor som är uppfyllda (i klartext).
3. För varje händelse med uppfyllt villkor returnerar Game Master namn och sannolikhet.
4. Orchestrator:
   - Slår tärning mot sannolikheter
   - Markerar engångshändelser som inträffade
   - Använder triggade händelser i vidare flöde för turen

## Aktörer

### Beskrivning

Varje aktör har:
- **Roll**: Vem/vad aktören representerar.
- **Mål**: Vad aktören vill uppnå (kan justeras under körning). Beskrivs i punktform.
- **Kort beskrivning**: Används i översikter för Game Master och andra aktörer.
- **Lång beskrivning**: Används av aktören själv, för att förstå exempelvis begränsningar, styrkor, förhållande till andra aktörer, och beslutsstil.

### Input till aktörer

Varje runda ser aktörerna:
(Uppdatera från hur skiss på prompt ser ut.)

Aktörerna vet *inte* vad andra aktörer beslutar samma runda (parallell exekvering).

### Åtgärder

Aktörer beskriver sina åtgärder i naturligt språk – ingen fördefinierad lista. Exempel:
- "Regeringen tillsätter en AI-kommission och avsätter 500 MSEK till omställningsstöd"
- "Facket inleder förhandlingar med Svenskt Näringsliv om AI-avtal"
- "Näringslivet accelererar AI-implementation trots fackligt motstånd"

I senare steg bedömer Game Master hur framgångsrika aktörerna är, uppdaterar Metric Rules och sedan Metrics.

### Mål-justering

Aktörer kan justera sina mål baserat på hur scenariot utvecklas. Varje sådan ändring ska motiveras av aktören.
Eventuella justeringar av målen sker *innan* åtgärderna.

## Kommunikation mellan aktörer

**Ingår ej i V4 MVP.**

Kan läggas till i V4.1 om det visar sig att utfallen blir för förutsägbara utan explicit förhandling. I MVP sammanfattas aktörers interaktioner implicit genom deras åtgärder.

## Filstruktur (skiss)

```
scenario-name/
├── scenario.md          # Övergripande beskrivning, tidsram, kontext
├── actors/
│   ├── government.md
│   ├── labor-unions.md
│   └── ...
├── metrics.md           # Metrics med skalor och beskrivningar
├── metric-rules.md      # Startregler (uppdateras under körning)
├── events.md            # Externa händelser med villkor
└── runs/
    └── run-001/
        ├── log.md       # Komplett logg över speltekniska händelser: metrics, externa händelser som triggas, Metric Rules för varje runda
        ├── turn-01.md   # Narrativ + metrics + ändringar
        ├── turn-02.md
        ├── metrics.json # Komplett historik över metrics
        └── summary.md   # Slutsammanfattning + outcome flags
```

## Python-kodens ansvar (Orchestrator)

Minimal kod som hanterar:

1. **Orkestrera rundor** – anropa LLM:er i rätt ordning med rätt kontext
2. **Hantera slump** – slå tärning för externa händelser
3. **Spåra engångshändelser** – hålla reda på vilka som redan inträffat
4. **Spara state** – metrics, Metric Rules, narrativ efter varje runda
5. **Logga** – spara all LLM-input/output för efteranalys
6. **Köra batcher** – samma scenario många gånger för statistik

## Efteranalys

För att uppnå målen (identifiera avgörande åtgärder, tipping points, etc.) behövs:

- **Outcome flags** – strukturerade markörer för viktiga utfall (kris, genombrott, etc.)
- **Många körningar** – samma scenario körs 10-100 gånger
- **Jämförelseverktyg** – analysera vad som skiljer körningar med olika utfall

Detta kan byggas som separat analysmodul efter att MVP fungerar.

## Avgränsningar i V4 MVP

Följande ingår **inte** i första versionen:

- Kommunikation/förhandling mellan aktörer
- Avancerad analysmodul
- Webb-UI
- Stöd för mänskliga spelare
- Outcome flags
- Eventuellt inte heller batch-verktyg

## Nästa steg

1. Skapa Game Master-prompt och testa mot ett enkelt scenario (klart!)
2. Implementera minimal Python-orkestrerare
3. Testa med sweden-ai-2030 (förenklad version)
4. Iterera på prompts baserat på resultat
5. Lägg till batchkörning och grundläggande analys (eventuellt)

---

*Dokument skapat: November 2025*
*Senast uppdatering: 2025-12-01*
*Version: 0.3*
