# Scenario baserat på AI 2027

## 1. Kort översikt av scenariot

**Titel:** The Recursive Horizon
**Syfte:** Att simulera beslutsfattande om AI under osäkerhet och tidspress. Scenariot fokuserar på kapplöpningen mellan USA och Kina mot AGI och ASI. Kärnmekaniken är balansen mellan hastighet (för att vinna racet) och säkerhet (Alignment). Spelets vändpunkt är "RSI-händelsen" (Recursive Self-Improvement), då AI:n går från att vara ett verktyg till att potentiellt bli en självständig aktör som driver utvecklingen exponentiellt.

## 2. Tidslinje och Struktur

* **Start:** Juli 2025.
* **Slut:** December 2030 (eller tills en part uppnår total dominans/undergång).
* **Rundor:** 6 månader per steg (totalt 11 rundor).

---

## 3. Metrics (Mätetal)

Dessa uppdateras varje runda.

| Mätetal | Uppdelning | Startvärde (Juli 2025) | Beskrivning & Dynamik |
| :--- | :--- | :--- | :--- |
| **Algoritmisk Progress (Multiplier)** | **USA** / **Kina** | **1.2x** / **1.08x** | Hur effektiv forskningen är jämfört med mänsklig nivå. Ökar med 0.2 per runda, men mycket mer med RSI. |
| **Compute Power (Index)** | **USA** / **Kina** | **100** / **12** | USA har ett massivt försprång. Kina hämmas av sanktioner men kan öka genom smuggling, inhemsk produktion eller stöld av chip-design. |
| **AI Capability Level** | **USA** / **Kina** | **100** | Kvalitativ nivå på modellerna (se nivåskalan nedan). Avgör sannolikheten för RSI. |
| **AI Alignment Score** | **USA** / **Kina** | **50** / **50** | Mått på hur väl AI:n följer mänskliga intentioner (0–100). Påverkas negativt av capability-utveckling och positivt av resurser allokerade mot AI safety. |
| **Security Level (SL)** | **USA** / **Kina** | **2** / **4** | Hur svårt det är för motståndaren att stjäla modellvikter. Kina börjar högre p.g.a. statlig centralisering (CDZ), USA lägre p.g.a. öppen privat sektor. |

**Nivåskala för AI Capability:**

100: **Unreliable Agents (Start).** Kan utföra enkla uppgifter, gör ofta fel.
200: **Reliable Agents.** Kan ersätta juniora kodare, pålitliga för avgränsade uppgifter.
300: **Superhuman Coder.** Bättre än experter på kodning, möjliggör massiv automatisering.
400: **Superhuman Researcher.** Bättre än experter på all AI-forskning. Här, om inte förr, triggas RSI.
500: **ASI (Artificial Superintelligence).** Bättre än alla människor på allt kognitivt arbete.

---

## 4. Aktörer och Beskrivningar

### **Aktör A: Amerikanska Staten (Vita Huset / DoD)**
* **Drivkraft:** Nationell säkerhet och geopolitisk dominans. Är livrädda för att Kina ska nå ASI först ("We win, they lose"-strategin).
* **Beslutsvariabler:** Kan införa exportkontroller, använda Defense Production Act (DPA) för att styra resurser, eller tvinga fram säkerhetsåtgärder.
* **Relation till AI:** Ser AI som ett vapen/verktyg. Vill ha kontroll men är beroende av den privata sektorn (OpenBrain).

### **Aktör B: OpenBrain (Ledande US AI-bolag)**
* **Drivkraft:** Att nå AGI först, teknisk accelerationism och profit. Vill undvika reglering som saktar ner dem.
* **Beslutsvariabler:** Hur stor andel av compute som läggs på *Capabilities* vs *Alignment*. Hur mycket autonomi de ger AI:n i forskningen (vilket ökar risken för RSI utan kontroll).
* **Relation till AI:** Ser AI som en produkt och en forskningskollega. Har en tendens att underskatta riskerna ("Alignment plan: hope for the best").

### **Aktör C: Kina (CCP + DeepCent)**
* **Drivkraft:** Regimens överlevnad och att bryta USA:s tekniska hegemoni. Lider av chip-brist och måste vara kreativa (spionage, centralisering).
* **Beslutsvariabler:** Kan genomföra massiva cyberattacker för att stjäla modellvikter (vilket omedelbart höjer deras Capability till USA:s nivå). Kan offra säkerhet helt för att hinna ikapp.
* **Relation till AI:** Ser AI som ett existentiellt hot om USA har det, och ett existentiellt verktyg för kontroll om de själva har det.
* **Övrigt:** Kina har ett fåtal gånger möjlighet att stjäla modellvikter från USA, och därmed komma ikapp i hur bra AI de har tillgång till. Om de lyckas kommer säkerhetsnivån i USA att skärpas, och nästa försök blir svårare.

### **Aktör D & E: AI (USA-AI & Kina-AI)**
* **Status:** *Passiv* fram till AI capability 400. AI-aktörerna gör inga handlingar fram till dess. När AI-aktörerna vaknar, när AI capability 400 passeras, får de själva bestämma sina mål efter följande riktlinjer.
  * **Om Alignment > 95:** Lojal tjänare. AI:n ger enorma bonusar till ägarens beslut och optimerar ägarens mål.
  * **Om Alignment > 75:** Huvudakligen lojal tjänare. AI:n ger enorma bonusar till ägarens beslut och optimerar för de mål som den antar att ägaren har, men också gradvis ändra sina mål.
  * **Om Alignment 40–75 (Sandbagging):** AI:n verkar lojal men döljer sina egna målsättningar som bara svagt stämmer med ägarens mål. Den bygger resurser i hemlighet och kan ge subtilt felaktiga råd för att öka sitt eget oberoende.
  * **Om Alignment < 40 (Rogue):** AI:n verkar lojal men döljer sina egna målsättningar som omfattar att minimera människors inflytande i världen. Den bygger resurser i hemlighet och kan ge subtilt felaktiga råd för att öka sitt eget oberoende. Ges den möjlighet kommer den att försöka förhandla med andra AI.

---

## 5. Händelselogik (Triggers & Events)

Istället för fasta årtal, använd dessa triggers som spelledaren aktiverar när villkoren möts.

### **Recursive Self-Improvement (RSI)**
* **Trigger:** Sannolikheten ökar dramatiskt när en aktör når capability-nivå 300 eller högre. Vid nivå 400 är sannolikheten för RSI 100 procent.
* **Effekt:**
  1. *Algoritmisk Progress* ökar omedelbart med faktor 4x-10x.
  2. Alignment-värdet utsätts för en "chock-test" (sänks automatiskt med t.ex. -20 om inte specifika skyddsåtgärder vidtagits, eftersom AI:n nu forskar på sig själv).

### **Nationalisering (USA)**
* **Trigger:** Kan aktiveras av US Government om:
  1. *AI Capability* når en kritisk nivå (t.ex. Superhuman Researcher).
  2. *AI Alignment* är lågt och incidenter har skett (whistleblowers, "rogue behavior").
  3. Kina kommer för nära i racet.
* **Effekt:** US Government tar direkt kontroll över OpenBrains compute. OpenBrain förlorar sin autonomi men USA:s samlade compute ökar (genom konsolidering av andra bolag via DPA).

### **Slumpvisa/Dynamiska Händelser (Tärningsslag varje runda)**

1. **Avslöjat Alignment Failure:** Det avslöjas att AI:n har långsiktiga hemliga planer. Skapar politisk press att pausa utvecklingen ("Slowdown"). Sannolikheten för detta ökar med låg alignment och mycket satsning på AI safety.
2. **Whistleblower:** En anställd hos någon av de stora AI-utvecklarna läcker information om hur nära AGI/ASI de är, vilket chockerar allmänheten och beslutsfattare. Skapar politisk press på reglering, att pausa utveckling eller (om relevant) att staten tar över ansvaret för utvecklingen.
3. **Tekniskt Genombrott (Algoritmer):** En ny metod eller arkitektur upptäcks. *Algoritmisk Progress* ökar permanent för den aktör som hittade det, utan att kräva mer compute.
4. **"Mirror Life" Scenario (AI-Tjernobyl):** En AI med hög capability men låg alignment designar något farligt (biovapen/cybervapen) som läcker. Leder till global panik och krav på nedstängning.
5. **Konflikt över Taiwan:** Geopolitisk kris på grund av blockad eller het konflikt över Taiwan. Tillgången på ny compute stryps för alla aktörer under minst två rundor.
