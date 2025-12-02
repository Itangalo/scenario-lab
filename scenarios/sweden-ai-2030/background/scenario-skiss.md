# Sweden and AI towards 2030

Sketch of a scenario to explore how Swedish society is affected by AI development.

## Purpose

- Test the Scenario Lab framework with a well-thought-out scenario
- Explore realistic dynamics between Swedish actors
- Identify missing features or design problems in the framework

## Time Frame

Start: January 1, 2026 (almost present time)
End: December 31, 2030

## Actors (preliminary list)

- **Parliament + Government** - Political decision-making, regulation, state investments. JOHAN: Should these be two different actors?
- **Trade Unions** - Labor market perspective, transition, negotiations. JOHAN: I'm happy to keep these as a single actor, even though there are many different trade unions. Do you think that works?
- **Media** - Opinion formation, scrutiny, own AI use
- **Business** - Implementation, innovation, competitiveness
- **"Swedish people"** - Opinions, adoption, labor market impact

### Open question: How to model "Swedish people"?

Alternatives:

- Split into segments (tech skeptics vs early adopters)
- Model via world state instead (opinion polls)
- Passive force that affects other actors' room for action

JOHAN: I'm leaning towards having them as world state and passive force that affects other actors. Even though Swedish people have a strong impact on political decisions, it's too diffuse to model as an actor. But then maybe world state should have a short section describing how different parts of the population think/act about AI?

## External Events (exogenous events)

### Background Trends (scheduled)

- Global AI development (new models, capabilities). JOHAN: Here I'm thinking we should have a scale, perhaps based on METR's surveys about long tasks. This can reflect how advanced AI exists. It also makes it easy to model different paces of development.
- EU regulation (AI Act implementation, new directives)

### Geopolitics (conditional/random)

- US political direction (presidential election 2028)
- Information warfare from Russia/China/Iran
- Global power balance and trade relations

### Black Swans (random, low probability)

- AI safety incident (large or small). JOHAN: This can be both something global and something in Sweden. In the latter case, it could be a young person who takes their life, largely due to conversations with an AI friend.
- Major AI breakthrough (near-AGI). JOHAN: I'm thinking that recursive self improvement is such a breakthrough, alternatively such an event is not a black swan at all but rather something that happens gradually as AI is increasingly used to improve AI development. Another variant is a new architecture, which has as much significance as transformers. Another thought is that AI breakthroughs can either give a single jump in AI capability, or a lasting increase in the speed of AI development.
- Economic crisis. JOHAN: One possibility is collapse around AI investments, which doesn't feel unlikely within the next year.
- Geopolitical crisis (e.g., Taiwan, Baltics, Middle East). JOHAN: Especially conflict over Taiwan is interesting. It can be hot conflict or a blockade that China initiates.
- Frontier AI classified as national security in the USA. Access to the best American models is severely limited outside the USA, and even inside the USA, knowledge of and access to the best models is strictly limited. This is what is sometimes called "A Manhattan project for AI".

## Scenario Variants

Three main tracks based on AI development pace:

1. **Slow** - Incremental improvements, no major breakthroughs
2. **Fast** - Continuous progress, clear impact on labor market
3. **Explosive** - Major breakthroughs, potentially near-AGI capabilities

JOHAN: I'm thinking this is about how the curve on METR's scale for long tasks continues. Current trend says doubling every seventh month, or possibly every fourth month for reasoning language models (but that's questionable). The question then is whether the curve continues to be exponential at the same pace, whether it calms down, or whether it even accelerates.

Can be implemented via batch configs with different exogenous-events files.

## Branch Points

- **Parliamentary election in Sweden 2026** - May possibly mean greater political engagement in AI, or continued business as usual
- **US presidential election 2028** - Manual branching for different outcomes

## Metrics to Follow

| Metric | Description | Type |
|--------|-------------|------|
| AI capability | How advanced AI exists globally | LLM-extraction |
| AI use at work | Share of Swedish workplaces with AI tools | LLM-extraction |
| AI use population | Public use of AI | LLM-extraction |
| Public attitude | Positive/negative view on AI | Scale (-10 to +10) |
| State AI investments | Funds invested by the state | LLM-extraction (MSEK) |
| Unemployment | Unemployment as reported by the Employment Service | LLM-extraction |

JOHAN: I don't know what "LLM-extraction" refers to in this context, but I think it's good to have defined scales. Draft:
* AI capability: Based on the METR study. How long tasks in software development can AI models handle successfully in half the cases? November 2025 says 2:42, and doubling of this every seventh month.
* AI use at work: Share of Swedish workers who report using AI tools at work. (Unknown values in November 2025, probably 40–50 percent.)
* AI use population: Share of Swedes aged 11–80 who report using AI tools regularly, privately or at work. (Probably 45–50 percent in November 2025.)
* Public attitude: Scale –10 to +10, which reflects both how many lean towards generally positive/negative attitude, and how strong these opinions are.
* Unemployment: Unemployment as reported by the Employment Service. Meaningful because high unemployment affects so many things in society. It's interesting if unemployment is concentrated to, for example, young people or particular industries, but this will have to do as a measure.

## EU's Role

Modeled as part of the environment (exogenous events) rather than as its own actor:

- AI Act implementation and compliance
- Possible reduction of regulation through AI Act or GDPR
- New regulatory initiatives
- Digital sovereignty investments
- Affects Swedish actors' room for action

## Open Questions

- [ ] How detailed should AI development be in exogenous events?
- [ ] What time resolution? (quarter, half-year, year?) JOHAN: I think half-year is a good resolution.
- [ ] Should we have regional differences (city vs rural)?
- [ ] How to handle elections 2026 (parliament) and 2028 (USA)? JOHAN: I think it's easiest to handle as branching in the scenario, not to try to simulate/predict the outcome. In both cases, it really matters less who wins the elections, but rather what agenda they have (or lack) when it comes to AI.

## Next Steps

1. Refine the actor list and their goals/constraints
2. Sketch initial world state
3. Define exogenous events more concretely
4. Determine time resolution and number of turns
5. Create first draft of scenario.yaml
