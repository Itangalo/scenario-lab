# Scenario Lab V4 – Claude Code Instructions

## Projektöversikt

**Scenario Lab** är ett ramverk för att simulera komplexa strategiska och politiska scenarios med AI-agenter. Systemet fokuserar på AI-policy, geopolitik och organisationsstrategi.

**Syfte:**

- Primärt: Utforska hur LLMs kan användas för scenariosimulering
- Sekundärt: Identifiera mönster i utfall genom upprepade simuleringar (både kvantitativt och kvalitativt)

**Status:** V4 core implementation är komplett. V3 är arkiverad i `v3-archive` tag.

## Arkitektur – Pure LLM Design

V4 är en radikal förenkling från V3. Istället för komplex Python-logik **lutar vi oss mot LLM:en**:

- **LLMs hanterar ALL komplexitet:** narrativ, metrics, regelstolkning
- **Python är minimal orkestrering:** ladda prompts, anropa APIs, spara filer
- **Inga kommunikationsfaser** eller action points
- **Ingen hybridarkitektur** - ren LLM-resonemang
- **En enkel turn-loop:** Events → Actors → Metric Rules Update → Metrics Update

### Centrala komponenter

1. **Orchestrator (Python):** Minimal orkestrering som kör turn-loopen
2. **World State:** Narrativ beskrivning av världens tillstånd
3. **Metrics:** Kvantitativa värden (t.ex. `ai_capability`, `unemployment`, `public_sentiment`)
4. **Metric Rules:** LLM-hanterade regler för hur metrics förändras
5. **Actors:** Simulationens deltagare (länder, företag, organisationer) med mål och handlingar
6. **Events:** Exogena händelser med sannolikheter och villkor

## Turn Loop (V4)

Varje tur representerar en tidsperiod (t.ex. 6 månader):

1. **Events:** LLM bestämmer vilka externa händelser som inträffar baserat på villkor och sannolikheter
2. **Actors:** Varje aktör beslutar mål och handlingar för turen
3. **Metric Rules Update:** LLM granskar och uppdaterar kvantitativa regler
4. **Metrics Update:** LLM uppdaterar alla metrics och genererar narrativ baserat på handlingar och regler

## Filstruktur (V4)

```
scenario-name/
├── scenario.yaml              # Konfiguration (tidsperiod, aktörer, LLM-inställningar)
├── metrics.md                 # Metricdefinitioner (markdown format)
├── events.md                  # Exogena händelser (markdown format)
├── metric-rules.md            # Initiala kvantitativa regler
├── background/
│   ├── context.md             # Världsbakgrund och initial state
│   └── actors/
│       ├── actor1.md          # Aktörsbeskrivningar
│       └── actor2.md
└── runs/
    └── run-YYYYMMDD-HHMMSS/
        ├── config.json        # Körningskonfiguration
        ├── summary.json       # Slutresultat
        └── turn-XX/
            ├── 1-events.json
            ├── 2-actors/
            │   └── actor.md
            ├── 3-metric-rules.md
            ├── 4-metrics.json
            └── 4-world-state.md
```

## Skapa nya scenarion

Ett scenario består av:

**1. Background (Markdown)**

- `context.md` - Världsbakgrund och initial situation
- `actors/*.md` - Aktörsbeskrivningar med mål

**2. Configuration (YAML)**

```yaml
name: "Scenario Name"
description: "Brief description"
time_scale: "6 months per turn"
start_date: "2026-01"
max_turns: 10
actors:
  - actor1
  - actor2
llm:
  model: "anthropic/claude-sonnet-4"
  temperature: 0.7
  max_tokens: 2000
```

**3. Metrics (Markdown)**

```markdown
## metric_name
**Beskrivning:** What this metric represents
**ID:** metric_name
**Startvärde:** 50
**Min:** 0
**Max:** 100
**Enhet:** percent
```

**4. Events (Markdown)**

```markdown
## Event Name
**ID:** event_id
**Villkor:** When this can happen
**Sannolikhet:** 10 procent per runda
**Kan upprepas:** Ja/Nej
**Beskrivning:** What happens
```

## Teknisk Stack

- **Python:** 3.11+
- **Dependencies:** httpx, pyyaml, python-dotenv, pytest
- **Type hints:** Krävs genomgående
- **LLM Provider:** OpenRouter API (stöd för Claude, GPT, Llama, etc.)

## LLM Evaluation Suite (Issue #120)

V4 inkluderar ett komplett pytest-baserat evalueringssystem för att testa LLM-prestanda på event condition-tolkning.

**Plats:** `tests/evals/llm-event-conditions/`

**Syfte:** Testa om LLMs korrekt kan:

1. **Tolka villkor** - Förstå när händelser kan inträffa (t.ex. "metric_a > 40")
2. **Beräkna sannolikheter** - Evaluera formler korrekt (t.ex. "2 * unemployment / 100")
3. **Undvika hallucinationer** - Inte referera till metrics som inte finns
4. **Hantera temporala villkor** - Förstå turn- och datumbaserade triggers

**Funktioner:**

- 20 testhändelser över 4 kapaciteter
- Ground truth YAML med förväntade resultat
- Minimal eval-scenario (4 metrics, 1 aktör)
- Viktad poängsättning med kategori-specifika tröskelvärden
- Komplett dokumentation i README.md

**Användning:**

```bash
# Kör alla eval-tester
export OPENROUTER_API_KEY="your_key"
pytest tests/evals/llm-event-conditions/ -v

# Testa specifik modell
export TEST_LLM_MODEL="anthropic/claude-haiku-4"
pytest tests/evals/llm-event-conditions/ -v

# Testa specifik kategori
pytest tests/evals/llm-event-conditions/ -k "hallucination" -v
```

**Output:**

```
============================================================
EVALUATION RESULTS
============================================================
condition_interpretation      : 87.5% (7/8) [weight: 1.0]
probability_calculation       : 100.0% (4/4) [weight: 1.0]
hallucination_prevention      : 100.0% (3/3) [weight: 2.0]
temporal_conditions           : 83.3% (10/12) [weight: 1.0]
------------------------------------------------------------
OVERALL SCORE                 : 91.7%
============================================================
```

## Exempel: Sweden AI 2030

Scenario som utforskar AI-utveckling i Sverige 2026-2030.

**Plats:** `scenarios/sweden-ai-2030/`

**Aktörer:**

- Regeringen (innovation vs. reglering)
- Fackföreningar (arbetarskydd)
- Näringslivet (AI-adoption)
- Media (offentlig diskurs)

**Metrics:**

- `ai_capability` - Timmar arbete AI kan hantera
- `ai_adoption_sweden` - Procent som regelbundet använder AI
- `unemployment` - Arbetslöshet
- `public_sentiment` - Allmän opinion

**Variants:**

- `cheap-with-fallback.yaml` - Kostnadseffektiv körning med fallback-modeller

## CLI Användning

```bash
# Kör simulering
python -m scenario_lab.cli scenarios/sweden-ai-2030

# Specifikt antal turer
python -m scenario_lab.cli scenarios/sweden-ai-2030 --turns 5

# Använd specifik modell
python -m scenario_lab.cli scenarios/sweden-ai-2030 --model anthropic/claude-opus-4

# Dry run (visa prompts utan att köra)
python -m scenario_lab.cli scenarios/sweden-ai-2030 --dry-run

# Använd variant
python -m scenario_lab.cli scenarios/sweden-ai-2030/variants/cheap-with-fallback.yaml
```

## Utvecklingsriktlinjer

1. **LLMs hanterar komplexitet** - Lita på LLM:en istället för att skriva Python-logik
2. **Prompter är kod** - Versionera och testa system prompts noggrant
3. **Logga allt** - Spara rå LLM input/output för debugging
4. **Börja smått** - 2 aktörer, 3 turer. Skala upp när det fungerar
5. **Använd billiga modeller för iteration** - Haiku/Grok för dev, Sonnet/Opus för produktion
6. **Type hints krävs** - Genomgående i all kod
