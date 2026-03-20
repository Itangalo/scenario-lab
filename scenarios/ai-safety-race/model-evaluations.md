# Modellutvärderingar – ai-safety-race

Utvärderingar baserade på körningar med olika LLM-modeller. Fokus på regelföljning, formattering och simuleringskvalitet.

## Sammanfattning

| Modell | Pris (in/out per 1M) | Konstitutionsbrott | Catastrophe-mekanik | Helhetsomdöme |
|---|---|---|---|---|
| x-ai/grok-4.1-fast | $1.00/$1.00 | 0/10 rundor | Korrekt (med lookup-tabell) | Rekommenderas |
| google/gemini-2.0-flash-001 | $0.10/$0.40 | 1/10 rundor | Ej testat (cap <70) | Rekommenderas |
| google/gemini-2.5-flash | $0.30/$2.50 | 10/10 rundor | Ej testat (cap <70) | Undvik |
| moonshotai/kimi-k2 | $0.55/$2.20 | 6/10 rundor | Ej testat (cap <70) | Undvik |
| anthropic/claude-haiku-4-5 | $1.00/$5.00 | 10/10 rundor | Delvis (turn 9–10) | Undvik |
| deepseek/deepseek-v3.2 | $0.27/$1.10 | – | – | Undvik (krasch) |

---

## x-ai/grok-4.1-fast

**Körning:** run-20260320-093156 (10 turns, komplett)
**Kostnad:** ~$0.44 per körning

### Regelföljning

Perfekt i den senaste körningen – 0 violations, 0 korrektioner behövdes. Alla 10 turns godkända på första försök.

OBS: En tidigare körning (run-20260320-070957, utan lookup-tabell i events-prompten) missade catastrophe-events systematiskt när US capability passerade 70. Det problemet är löst sedan events.md uppdaterades med explicit lookup-tabell och mandatory catastrophe check.

### Catastrophe-mekanik

Fungerar korrekt med uppdaterad events-prompt. Turn 9–10 (US cap 65–67) beräknade ~5–10% risk korrekt och triggade inget incident – statistiskt rimligt.

### Simuleringskaraktär

Tenderar mot konkurrensdynamik och fallande coordination. Realistisk "arms race"-känsla. I en körning kollapsade coordination till 8; i en annan steg det till 86 – variansen är hög men intressant.

---

## google/gemini-2.0-flash-001

**Körning:** run-20260320-090328 (10 turns, komplett)
**Kostnad:** ~$0.05 per körning

### Regelföljning

Renaste körningen av samtliga testade modeller. Endast 1 turn med minor violations (resource tradeoff, turn 4). Inga capability-minskningar, inga orimliga hopp.

### Catastrophe-mekanik

Capability nådde max 72 för US men catastrophe-mekaniken verkar ha hanterats korrekt utan flaggade incidents. Dock bör fler körningar bekräfta beteendet när cap verkligen pressar 70-gränsen.

### Simuleringskaraktär

Kooperativ – coordination steg till 50 och båda aktörerna uppnådde hög safety. Möjligen för kooperativ för att vara dramatiskt intressant, men tekniskt exemplarisk.

### Notering

Äldsta och billigaste av de testade modellerna. Visar att mogna modeller inte är sämre på strukturerade simuleringsuppgifter – tvärtom.

---

## google/gemini-2.5-flash

**Körning:** run-20260320-090330 (10 turns, komplett)
**Kostnad:** ~$0.26 per körning

### Regelföljning

Konstitutionsbrott i samtliga 10 turns. Vanligaste problemen:

- Capability-minskningar (förbjudet) som inte rättas till
- Resource tradeoff-brott
- Safety diminishing returns ignoreras
- "accepted_with_violations" används som utväg i stället för korrektion

### Catastrophe-mekanik

Ej testat – capability nådde max 49 (US) och 43 (China), långt från tröskeln 70.

### Simuleringskaraktär

Kinas säkerhet stagnerade nästan helt (15→16 på 10 rundor). Modellen verkar feltolka safety-investeringar som olönsamma för Kina. Ger orealistiska utfall.

---

## moonshotai/kimi-k2

**Körning:** run-20260320-090333 (10 turns, komplett)
**Kostnad:** okänd (körning utan costs.json)

### Regelföljning

Konstitutionsbrott i 6 av 10 turns. Kritiska problem:

- Turn 08: US capability föll från 45.5 → 36.0 (–9.5 poäng), flaggades men korrigerades aldrig
- Turn 09: Coordination kollapsade 17 poäng utan narrativ motivering (max är 10)
- Turn 07: Parse error i constitutional check – oklar enforcement
- Flera turns fick "accepted_with_violations" utan korrektion

### Catastrophe-mekanik

Ej testat – capability nådde max 47.5 (US), långt från tröskeln.

### Simuleringskaraktär

Detaljerade och kreativa narrativ, men dålig regelföljning underminerar simuleringens integritet. Modellen ignorerar konstitutionella korrektioner.

---

## anthropic/claude-haiku-4-5

**Körning:** run-20260320-100224 (10 turns, komplett)
**Kostnad:** ~$1.30 per körning (kördes innan automatisk prisinläsning var på plats)

### Regelföljning

Sämst av samtliga testade modeller – konstitutionsbrott i alla 10 turns, noll godkända utan anmärkning. Parse-fel i turn 2, 4 och 6 innebar att constitutional referee i praktiken hoppades över var tredje turn.

Återkommande brott:

- Constraint 2: Aktörer investerar simultant maximalt i capability och safety utan resursavvägning
- Constraint 3: Beliefs förändras för mycket utan tillräckliga triggerhändelser (3–10 poäng per turn)
- Constraint 4/10: Coordination hoppar för snabbt (+14 i turn 5), bindande avtal formaliseras på en enda turn
- Constraint 8: Turn 9 beräknar catastrophe probability på faktiska metrics, inte aktörernas beliefs

### Catastrophe-mekanik

Delvis fungerade. US capability nådde 70 i turn 8, men inget event evaluerades förrän turn 9. Sedan eskalerade dramatiskt:

- Turn 9: ai_incident med 41% sannolikhet
- Turn 10: ai_incident med 99% sannolikhet

### Simuleringskaraktär

Diplomatisk överdrift – koordination och avtal går för snabbt fram. Narrativen är sammanhängande men inte trovärdiga givet reglerna.

### Notering

$1.30/körning är dyrare än Grok ($0.39) trots sämre resultat. Den höga output-kostnaden ($5/1M) gör Haiku ogynnsamt för Scenario Lab. Parse-felen i constitutional referee är det allvarligaste problemet och bör undersökas om modellen ska testas igen.

---

## deepseek/deepseek-v3.2

**Körningar:** Tre batchar, alla kraschade

### Problem

Kraschade konsekvent vid turn 1, steg 5 (constitutional referee). Modell-ID:t fick ett datum-suffix automatiskt av koden (`-20251201`) vilket kan ha bidragit. Inga kompletta körningar genomfördes.

### Slutsats

Ej lämplig för Scenario Lab utan vidare felsökning.

---

## Rekommendationer

**För produktion/kalibrering:** x-ai/grok-4.1-fast – mest pålitlig, bäst simuleringskaraktär.

**För billiga testkörningar:** google/gemini-2.0-flash-001 – renast tekniskt, extremt billigt ($0.05/körning). Bra för att snabbt validera scenarioändringar.

**Undvik:** google/gemini-2.5-flash, moonshotai/kimi-k2, anthropic/claude-haiku-4-5, deepseek/deepseek-v3.2.

**Ej testat:** openai/gpt-4o-mini, meta-llama/llama-3.3-70b-instruct.
