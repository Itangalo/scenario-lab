# System Prompts for Sweden and AI 2030

These scenario-specific system prompts override the default templates in `templates/system-prompts/`. They are customized for the Sweden and AI 2030 scenario with actual metrics, actors, and context.

## Files

- **events.md** - Customizes how external events are evaluated
- **actor_government.md** - Customizes behavior for the Government actor
- **actor_labor-unions.md** - Customizes behavior for the Labor Unions actor
- **actor_media.md** - Customizes behavior for the Media actor
- **actor_business-sector.md** - Customizes behavior for the Business Sector actor
- **metric-rules.md** - Customizes how metric rules are updated
- **metrics-update.md** - Customizes metrics updates and narrative generation

## How They Work

1. **Loading**: When the scenario is loaded, these files are read and stored in the scenario object
2. **Fallback**: If an actor-specific prompt file is missing, the system falls back to the default template
3. **Placeholder replacement**: Placeholders like `{{actor_name}}` and `{{actor_description}}` are replaced with actual data when prompts are built
4. **Actor-specific**: Each actor has their own system prompt file with customized behavioral constraints

## Actor-Specific Behavioral Constraints

Each actor prompt includes specific behavioral traits from their descriptions:

- **Government**: Slow decision-making, reactive policy, EU-focused, consensus-seeking
- **Labor Unions**: Negotiation-oriented, member-representative, pragmatic but skeptical
- **Media**: Fast news cycle, engagement-driven, limited technical depth, influential on public sentiment
- **Business Sector**: Quarterly-driven, active lobbying, pragmatic rule-follower, skills challenged

## Editing

These prompts were generated from the templates but can be edited to customize the simulation behavior. Changes will take effect the next time the scenario is run.

To revert to default templates, simply delete these files.
