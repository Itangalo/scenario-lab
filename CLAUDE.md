# Scenario Lab V3 – Claude Code Instructions

## Projektöversikt

**Scenario Lab** är ett ramverk för att simulera komplexa strategiska och politiska scenarios med AI-agenter. Systemet fokuserar på AI-policy, geopolitik och organisationsstrategi.

**Syfte:**
- Primärt: Utforska hur LLMs kan användas för scenariosimulering
- Sekundärt: Identifiera mönster i utfall genom upprepade simuleringar (både kvantitativt och kvalitativt)

**Ignorera:** Filen `Implementation phases.md` ska helt ignoreras vid utveckling.

## Arkitektur – Hybridmodell

V3 löser grundläggande problem från tidigare versioner genom en hybridarkitektur:

- **Narrativ flexibilitet:** LLMs hanterar diplomati, intentioner och kvalitativa beskrivningar
- **Deterministisk logik:** Python-kod hanterar kvantitativa konsekvenser, resursflöden och verifierbara fakta
- **Informationsasymmetri:** Aktörer har privat och publik information, vilket skapar realistisk osäkerhet

### Centrala komponenter

1. **Engine (Python):** Orkestrerar spelet, anropar LLM APIs och underhåller World State
2. **World State:** Sanningen om världen vid en given tidpunkt, består av fyra lager:
   - **Narrative State:** Löpande textbeskrivning (historia + nuläge)
   - **Metrics:** Kvantitativ data (global, private, public)
   - **Fact Ledger:** Verifierade hårda fakta som aldrig sammanfattas bort
   - **Relationship State:** Strukturerad data per aktörspar (trust, active_agreements)
3. **The Director:** Specialiserad systemaktor som väver samman handlingar och händelser till sammanhängande narrativ
4. **Actors:** Simulationens deltagare (länder, företag, organisationer), kontrollerade av LLM personas med specifika mål
5. **Action Points (AP):** Valuta som begränsar kommunikation och uppmärksamhet

## Skapa nya scenarion

**Läs `docs/creating-scenarios.md` innan du skapar nya scenarion.**

Dokumentet innehåller:
- Krav på background-filer (sketch-format)
- Tekniska filformat (scenario.yaml, metrics.yaml, events.yaml, methods.py)
- Steg-för-steg-process för att generera filer från sketches
- Valideringschecklista

Använd `examples/us-china-ai/` som referensexempel.

## Filstruktur

```
scenario-name/
├── background/
│   ├── context.md
│   └── actors/
│       ├── USA.md
│       └── China.md
├── scenario.yaml          # Tidsskala, AP-regler, world_altering_triggers
├── metrics.yaml           # World + actors (private/public)
├── events.yaml            # Exogena händelser
├── methods.py             # Logik, validering, tolkningar
└── runs/
    └── run-001/
        ├── turn-01/
        │   ├── views/
        │   │   ├── USA.json      # Aktörsspecifik World State
        │   │   └── China.json
        │   ├── comms_phase_1.json
        │   ├── comms_phase_2.json
        │   ├── actions.json
        │   ├── world_state.md
        │   ├── metrics.json
        │   ├── relationships.json
        │   └── fact_ledger.json
        └── summary.json          # Outcome flags för analys
```

## Simuleringsloop

Varje tur representerar en tidsperiod (t.ex. 6 månader).

### Pre-Turn
1. Event Check
2. Trigger Check (World Altering Events)
3. AP Reset
4. View Generation (aktörsspecifik filtrerad World State)

### Fas 1: Initiative & Communication
- Aktörer får sin filtrerade World State
- Kan skicka meddelanden (1 AP per mottagare)

### Fas 2: Response & Final Negotiation
- Aktörer får inkommande meddelanden
- Svar till avsändare: 0 AP
- Nytt meddelande/vidarebefordra: 1 AP

### Fas 3: Execution & Goal Adjustment
- Diplomati avslutad, alla agerar
- Max 2 stora initiativ per tur (valideras av methods.py)
- Output: Narrativ text + strukturerade funktionsanrop + uppdaterade mål

### Post-Turn Synthesis
1. Validering via methods.py
2. Metrics Update
3. Relationship Update
4. Fact Ledger Update
5. Narrative Synthesis (Director genererar world_state.md)

## Informationsasymmetri

Metrics delas in i tre kategorier:

```yaml
world:           # Synlig för alla
  global_temperature: 1.2
  ai_catastrophe_risk: 0.05

actors:
  USA:
    private:     # Synlig endast för ägaren
      military_capacity: 85
    public:      # Synlig för alla
      budget: 500
```

## methods.py – Scenariospecifik logik

Varje scenario definierar sina egna action functions. Engine anropar dem dynamiskt baserat på function_call-namn i LLM output.

**Standard signatur:**
```python
def action_name(actor: str, args: dict, state: WorldState) -> list[str]:
    """
    Modifiera state.metrics och state.outcome_flags vid behov.
    Returnera lista med tolkningssträngar för Director.
    """
    pass
```

**Outcome Flags** sätts av methods.py för kvantitativ analys:
```python
state["outcome_flags"]["war_declared"] = True
state["outcome_flags"]["war_parties"] = [attacker, defender]
```

## Teknisk Stack

- **Python:** 3.11+
- **Dependencies:** pydantic, pyyaml, httpx
- **Execution model:** Synkron för MVP (async kan läggas till senare)
- **Type hints:** Krävs genomgående

### LLM Provider Abstraction

Stöd för flera LLM backends via provider abstraction:
- **OpenRouterProvider:** Primär provider (Claude, GPT, Llama, etc.)
- **LocalProvider:** För lokala modeller (Ollama, llama.cpp)

Konfigureras i scenario.yaml:
```yaml
llm:
  provider: "openrouter"
  model: "anthropic/claude-sonnet-4"
  api_key_env: "OPENROUTER_API_KEY"
```

## Utvecklingsriktlinjer

1. **Versionera prompter separat:** Lagra i `prompts/` directory för iteration utan kodändringar
2. **Logga allt:** Spara rå LLM input/output för debugging
3. **Börja smått:** 2 aktörer, 3 turer. Skala upp när det fungerar
4. **Använd billiga modeller för iteration:** Byt till starkare modeller för produktionskörningar
5. **Type hints krävs:** Genomgående i all kod
6. **Validering först:** methods.py validerar och begränsar handlingar

## MVP Implementation Roadmap

1. Core Engine (loop som läser YAML, genererar views, kör turer)
2. Metrics Filter (implementera `get_visible_metrics()`)
3. Action Validation (methods.py validerar och begränsar handlingar)
4. Mock LLM (dummy agent för att testa flödet)
5. LLM Integration (OpenRouter provider med retry logic)
6. Prompt Engineering (system prompts för alla faser)
7. Director (narrativ syntes)
8. Outcome Flags (strukturerad data för analys)
9. CLI (realtidsvisning av simulering)

## Minnehantering

För långa simuleringar:

1. **Narrative:** Rolling window – senaste 2 turerna i detalj, sammanfattning av tidigare epoker
2. **Fact Ledger:** Kritiska punkter som aldrig sammanfattas bort
3. **Relationship State:** Strukturerad data som ersätter narrativt relationsminne
4. **Metrics:** Senaste snapshot + datatolkningar

## Viktiga designprinciper

- **Hybrid architecture:** LLM för narrativ, Python för logik
- **Information asymmetry:** Aktörer har begränsad information
- **Deterministic validation:** methods.py säkerställer regelefterlevnad
- **Structured outcomes:** Outcome flags möjliggör kvantitativ analys
- **Memory efficiency:** Strukturerad data + selektiv narrativ
