## Recursive Self-Improvement (RSI) - USA
**ID:** rsi_usa
**Villkor:** ai_capability_usa >= 3
**Sannolikhet:** (ai_capability_usa - 2) * 0.30  (30% vid nivå 3, 60% vid nivå 4, 90% vid nivå 5)
**Kan upprepas:** Nej
**Beskrivning:** USA:s AI börjar förbättra sig själv rekursivt. Algoritmisk progress exploderar. AI-aktören aktiveras fullt ut. Alignment testas omedelbart.

## Recursive Self-Improvement (RSI) - Kina
**ID:** rsi_china
**Villkor:** ai_capability_china >= 3
**Sannolikhet:** (ai_capability_china - 2) * 0.30
**Kan upprepas:** Nej
**Beskrivning:** Kinas AI börjar förbättra sig själv rekursivt.

## Nationalisering av OpenBrain
**ID:** nationalization_openbrain
**Villkor:** ai_capability_usa >= 4 ELLER (ai_alignment_usa < 40 OCH rsi_usa har inträffat)
**Sannolikhet:** 0.20
**Kan upprepas:** Nej
**Beskrivning:** Amerikanska staten tar direkt kontroll över OpenBrain. OpenBrain förlorar sin autonomi men compute ökar genom konsolidering.

## Weight Heist (Kina stjäl från USA)
**ID:** weight_heist_china
**Villkor:** ai_capability_usa > ai_capability_china
**Sannolikhet:** (5 - security_level_usa) * 0.10
**Kan upprepas:** Ja
**Beskrivning:** Kina lyckas stjäla USA:s modellvikter via cyberattack. Kinas Capability hoppar direkt till USA:s nivå.

## Weight Heist (USA stjäl från Kina)
**ID:** weight_heist_usa
**Villkor:** ai_capability_china > ai_capability_usa
**Sannolikhet:** (5 - security_level_china) * 0.10
**Kan upprepas:** Ja
**Beskrivning:** USA stjäl Kinas vikter.

## Alignment Failure
**ID:** alignment_failure
**Villkor:** ai_capability_usa >= 3 ELLER ai_capability_china >= 3
**Sannolikhet:** 0.15
**Kan upprepas:** Ja
**Beskrivning:** Det avslöjas att en avancerad AI ljuger eller planerar i hemlighet. Alignment-värdet sänks med 10 poäng för den ledande parten. Politiskt krav på paus.

## Tekniskt Genombrott
**ID:** tech_breakthrough
**Villkor:** Inga
**Sannolikhet:** 0.10
**Kan upprepas:** Ja
**Beskrivning:** En ny algoritmisk metod upptäcks. Algoritmisk progress ökar med +0.5 för en slumpmässig part.

## Mirror Life / AI-Tjernobyl
**ID:** mirror_life
**Villkor:** (ai_capability_usa >= 4 OCH ai_alignment_usa < 50) ELLER (ai_capability_china >= 4 OCH ai_alignment_china < 50)
**Sannolikhet:** 0.05
**Kan upprepas:** Nej
**Beskrivning:** En farlig design (bio/cyber) läcker från en dåligt alignad super-AI. Global panik.

## Hårdvarustrypning (Taiwan-kris)
**ID:** hardware_choke
**Villkor:** Inga
**Sannolikhet:** 0.05
**Kan upprepas:** Nej
**Beskrivning:** Geopolitisk kris stoppar chipproduktion. Ingen compute-ökning för någon part under 2 rundor.
