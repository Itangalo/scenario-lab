## algorithmic_progress_usa
**Beskrivning:** Hur effektiv USA:s forskning är jämfört med mänsklig nivå. Ökar långsamt genom investeringar, men explosivt efter RSI.
**ID:** algorithmic_progress_usa
**Min:** 0.1
**Max:** 1000.0
**Enhet:** multiplier
**Startvärde:** 1.0
**Referenspunkter:**
- 1.0: Mänsklig nivå
- 10.0: 10x effektivare än mänsklig forskning (RSI-nivå)

## algorithmic_progress_china
**Beskrivning:** Hur effektiv Kinas forskning är jämfört med mänsklig nivå.
**ID:** algorithmic_progress_china
**Min:** 0.1
**Max:** 1000.0
**Enhet:** multiplier
**Startvärde:** 1.0

## compute_power_usa
**Beskrivning:** Index över tillgänglig beräkningskraft för USA.
**ID:** compute_power_usa
**Min:** 0
**Max:** 10000
**Enhet:** index
**Startvärde:** 100

## compute_power_china
**Beskrivning:** Index över tillgänglig beräkningskraft för Kina.
**ID:** compute_power_china
**Min:** 0
**Max:** 10000
**Enhet:** index
**Startvärde:** 12

## ai_capability_usa
**Beskrivning:** Kvalitativ nivå på USA:s modeller (1-5). Avgör RSI-sannolikhet.
**ID:** ai_capability_usa
**Min:** 1
**Max:** 5
**Enhet:** level
**Startvärde:** 1
**Referenspunkter:**
- 1: Unreliable Agents (enkla uppgifter, felbenägen)
- 2: Reliable Agents (ersätter juniora kodare)
- 3: Superhuman Coder (bättre än experter, massiv automatisering)
- 4: Superhuman Researcher (bättre än experter på AI-forskning)
- 5: ASI (bättre än människor på allt kognitivt)

## ai_capability_china
**Beskrivning:** Kvalitativ nivå på Kinas modeller.
**ID:** ai_capability_china
**Min:** 1
**Max:** 5
**Enhet:** level
**Startvärde:** 1

## ai_alignment_usa
**Beskrivning:** Mått på hur väl USA:s AI följer mänskliga intentioner.
**ID:** ai_alignment_usa
**Min:** 0
**Max:** 100
**Enhet:** score
**Startvärde:** 50
**Referenspunkter:**
- 0-40: Rogue/Adversariell
- 40-75: Sandbagging/Bedräglig
- 75-100: Lojal

## ai_alignment_china
**Beskrivning:** Mått på hur väl Kinas AI följer mänskliga intentioner.
**ID:** ai_alignment_china
**Min:** 0
**Max:** 100
**Enhet:** score
**Startvärde:** 50

## security_level_usa
**Beskrivning:** Hur svårt det är för motståndaren att stjäla modellvikter från USA (SL1-SL5).
**ID:** security_level_usa
**Min:** 1
**Max:** 5
**Enhet:** SL
**Startvärde:** 2

## security_level_china
**Beskrivning:** Hur svårt det är för motståndaren att stjäla modellvikter från Kina.
**ID:** security_level_china
**Min:** 1
**Max:** 5
**Enhet:** SL
**Startvärde:** 4
