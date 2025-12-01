# V4 Early Testing – Sverige och AI 2030

Testmiljö för att validera V4-prompter och körningsloop.

## Scenario

**Tidsram:** Januari 2026 – December 2030 (10 rundor á 6 månader)

**Fokus:** Hur svenska samhället hanterar AI-utvecklingen och dess konsekvenser för arbetsmarknad, politik och samhälle.

## Aktörer

1. **Regeringen** (government) – Politiskt beslutsfattande, reglering, resursallokering
2. **Fackföreningarna** (labor-unions) – Arbetstagarperspektiv, förhandling, omställning
3. **Näringslivet** (business-sector) – Implementation, innovation, konkurrenskraft
4. **Media** (media) – Opinionsbildning, granskning, rapportering

## Metrics

Metrics representeras som rena tal. Min/Max/Enhet definieras i metrics.md för läsbarhet och diagramgenerering.

- **ai_capability** (Min: 0, Max: 1000, Enhet: timmar, Start: 3)
- **ai_adoption_sweden** (Min: 0, Max: 100, Enhet: procent, Start: 10)
- **unemployment** (Min: 0, Max: 100, Enhet: procent, Start: 8)
- **public_sentiment_to_ai** (Min: -10, Max: 10, Enhet: dimensionslös, Start: 3)

Vid normal utveckling dubbleras ai_capability varje halvår: 3 → 6 → 12 → 24 → ... → 1536 över 10 rundor.

## Externa händelser

- AI-incident i Sverige
- Strejk mot AI-implementering
- AI-genombrott
- AI-utvecklingen planar ut
- Taiwan-blockad
- AI-bubblans kollaps
- Riksdagsval 2026
- Presidentval i USA 2028

## Testkörning

För denna testkörning kommer en LLM att agera både:
- **Orchestrator** (körningsloop, slumphändelser)
- **Game Master** (hantera events, uppdatera regler och metrics, skriva narrativ)
- **Actors** (regeringen, facket, näringslivet, media)

Detta för att validera att prompterna fungerar och ger meningsfulla resultat.
