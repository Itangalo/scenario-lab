Det är nu runda 2 som omfattar juli–december 2026.

Nuvarande metrics ser ut så här:

```json
{
  "ai_capability": 6,
  "ai_adoption_sweden": 48,
  "unemployment": 7,
  "public_sentiment_to_ai": 1
}
```

Världens tillstånd vid start av rundan beskrivs så här:

Under första halvåret 2026 präglas Sverige av en våg av koordinerade initiativ kring AI, där aktörerna samverkar i en blandning av optimism och försiktighet. Regeringen kickstartar året med att lansera AI-infrastrukturkommittén i januari, som snabbt kartlägger brister i beräkningskraft och talang – en signal om handlingskraft som väljs av väljare inför höstens val. Tripartitmötet i februari resulterar i en preliminär "AI-omställningsöverenskommelse", där fack och näringsliv enas om ramverk för utbildning och förhandlingar, vilket dämpar omedelbara konflikter. EU AI Act-handlingsplanen, inklusive det nya AI-regelverkskontoret, möts positivt av företag, som upplever Sverige som en förutsägbar marknad. Ett litet mediestöd till SVT och SR leder till mer nyanserad bevakning, medan pilotprogrammet för omskola i kundtjänst och administration startar med 500 deltagare, synliggörande regeringens engagemang.

Fackföreningarna stärker sin position genom en omfattande medlemsundersökning i februari, som avslöjar oro bland 60% av respondenterna för jobbförluster, och publiceras som faktabaserad ammunition i dialoger med stora arbetsgivare som Ericsson och Volvo. Den nya AI-expertisgruppen ger facken teknisk trovärdighet, och lobbying inför valet lyfter AI som valfråga i opinionsartiklar. Internationella kontakter med nordiska fack lägger grunden för framtida samordning.

Näringslivet accelererar genom det nya AI Adoption Network, som delar fallstudier om 20% produktivitetsvinster i fintech och tillverkning, lockande småföretag att delta. Talent-initiativet förenklar visum för 200 AI-experter, medan lobbying mot EU-regleringar mildrar risker för SME. En pragmatisk mediekampanj, med historier om AI som löser arbetskraftsbrist, når DN och SVT, höjande acceptansen. Internt planerar storföretag omstruktureringar diskret, med fokus på omskola snarare än uppsägningar.

Media bygger kapacitet via AI-ressortteam med KTH-experter, förbättrande granskningen. En långform-kampanj i maj följer drabbade arbetare i programmering och administration, avslöjande gap mellan politik och verklighet. Granskning av regeringens AI-politik i juni ifrågasätter kommissionens resultat, påverkan valdebatten. Branschforummet leder till en rapport om AI i journalistik, medan piloten för AI-faktakontroll ökar effektiviteten.

Sammanfattningsvis ökar AI-kapaciteten globalt, men i Sverige trycks adoptionen något av elitfokus på frontier-teknik. Arbetslösheten stiger marginellt till 7% genom tidiga automatiseringar, och opinionen tippar försiktigt positiv, driven av dialog men dämpad av osäkerhet.

---

Listan över potentiella externa händelser ser ut så här:

**AI-incident i Sverige**
- ID: ai_incident_sweden
- Villkor: Kräver ai_adoption_sweden > 30
- Sannolikhet: 10 procent per runda
- Kan upprepas: Ja
- Beskrivning: En tonåring tar sitt liv efter intensiv kontakt med en AI-kompanjon. Stor medieuppmärksamhet. Jämförelser med debatten om sociala mediers skadeverkningar. Krav på reglering ökar kraftigt. public_sentiment_to_ai minskar markant.

**Strejk mot AI-implementering**
- ID: strike
- Villkor: Kräver unemployment högre än 8
- Sannolikhet: Dubbla värdet på unemployment, delat med hundra
- Kan upprepas: Ja
- Beskrivning: Fackförbund inleder strejk mot AI-implementering på en eller flera större arbetsplatser. Produktivitet minskar tillfälligt, spänningar mellan fack och näringsliv ökar. Media uppmärksammar konflikten, vilket påverkar public_sentiment_to_ai negativt.

**AI-genombrott**
- ID: ai_breakthrough
- Villkor: Inga villkor
- Sannolikhet: 5 procent per runda
- Kan upprepas: Ja
- Beskrivning: En ny arkitektur eller träningsmetod ger dramatiskt förbättrade AI-kapabiliteter. ai_capability tar ett stort steg uppåt (motsvarande 1-2 års normal utveckling) och utvecklas sedan enligt samma exponentiella mönster som innan. Stor medieuppmärksamhet globalt.

**AI-utvecklingen planar ut**
- ID: ai_stall
- Villkor: Inga villkor
- Sannolikhet: 3 procent per runda
- Kan upprepas: Nej
- Beskrivning: Utvecklingen av AI stöter på motstånd som visar sig svårt att övervinna – möjligen relaterat till datatillgång, arkitektoniska begränsningar, eller energikostnader. AI-utvecklingen minskar till en långsam linjär takt och förblir så tills ett nytt AI-genombrott sker. AI-utvecklingens inbromsning skapar oro på finansmarknaden men i övrigt är den stora effekten att förväntade effekter av kraftfullare AI uteblir.

**Taiwan-blockad**
- ID: taiwan_blockade
- Villkor: Kan inträffa från runda 3 och framåt
- Sannolikhet: 5 procent per runda
- Kan upprepas: Nej
- Beskrivning: Kina inleder blockad av Taiwan. Global chipproduktion störs kraftigt. Så länge blockaden pågår går AI-utvecklingen mycket långsamt framåt (ai_capability ökar minimalt). Priser på elektronik stiger kraftigt. Geopolitisk osäkerhet ökar dramatiskt. Varje efterföljande runda efter att blockaden inletts är det 50 procent chans att blockaden får ett fredligt slut och 10 procent risk att den övergår i en militär konflikt (vilket skulle innebära ännu värre konsekvenser).

**AI-bubblans kollaps**
- ID: ai_bubble_collapse
- Villkor: Inga villkor
- Sannolikhet: 15 procent runda 1-2, 10 procent runda 3-4, 5 procent runda 5+
- Kan upprepas: Nej
- Beskrivning: AI-investeringsbubbllan spricker. Massiva nedskrivningar av AI-startup-värderingar. Många företag går i konkurs. Utvecklingstakten i AI-sektorn bromsar in tillfälligt (1-2 rundor). Etablerade aktörer konsoliderar sin makt. Arbetslöshet inom tech-sektorn ökar.

**Riksdagsval 2026**
- ID: general_election_2026
- Villkor: November 2026 ingår i rundan
- Sannolikhet: 100 procent
- Kan upprepas: Nej
- Beskrivning: Nytt riksdagsval leder till regeringsförhandlingar och eventuellt regeringsskifte. Vid regeringsskifte kan regeringens mål radikalt ändras.

**Presidentval i USA 2028**
- ID: usa_election_2028
- Villkor: November 2028 ingår i turen som avhandlas
- Sannolikhet: 100 procent
- Kan upprepas: Nej
- Beskrivning: När en ny president väljs i USA kan landets policy kring AI ändras drastiskt.

---

Använd bakgrundsinformationen för att avgöra vilka externa event som kan inträffa i den här rundan. Om sannolikheten anges som en formel eller beskrivning, ska du beräkna det faktiska värdet.

Ditt svar ska vara en JSON-array med objekt för varje händelse vars villkor är uppfyllt, på det här formatet:

```json
[
  {"id": "event1_id", "probability": 0.10},
  {"id": "event2_id", "probability": 0.24}
]
```

Sannolikheten ska anges som ett värde mellan 0 och 1. Om ingen händelse uppfyller villkoren ska du svara med en tom array: `[]`

Svara *endast* med denna JSON-array, inget annat.
