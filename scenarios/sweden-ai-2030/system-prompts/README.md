# System Prompts for Sweden and AI 2030

Scenario-specific prompt overrides for the steps this scenario tunes. Actor
prompts use the default templates in `templates/system-prompts/` and
`templates/user-prompts/`: actor character lives in `background/actors/*.md`
(long description, statements, behavioral traits), and the statement-ledger
machinery is framework-level, so a per-actor override here would only
duplicate – or worse, replace and silently drop – the default contract.

## Files

- **events.md** - Customizes how external events are evaluated
- **metric-rules.md** - Customizes how metric rules are updated
- **metrics-update.md** - Customizes metrics updates and narrative generation

## How overrides work

An override fully *replaces* the corresponding default template for this
scenario (or, named `actor_<id>.md`, for one actor). There is no merging: an
actor-prompt override must therefore contain the entire system prompt,
including the statement-tier norms, or those never reach the model.
