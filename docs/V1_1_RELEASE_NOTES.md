# v1.1 Release Notes: Roleplay Immersion Layer

## Version Name

v1.1: Roleplay Immersion Layer

## Version Goal

v1.1 adds a bounded roleplay immersion layer to the local interactive novel
world engine. It brings character-card-style import, voice profiles, emotional
tone, relationship tone, continuous Dialogue Mode, Group RP, lorebook
classification, example dialogue, RP memory context, RP prompt profiles, and
RP-specific tests into the local studio.

This remains a local personal engine. The LLM is still not the world judge. The
RP layer is for expression, character voice, mood, and immersion; it cannot
change authoritative facts, bypass visibility, grant NPCs unknown knowledge, or
write `GameState` from model text.

## New Features

### Roleplay Boundary Contract

- Added `docs/ROLEPLAY_BOUNDARY.md`.
- Defines the RP boundary between expressive context and authoritative facts.
- Introduces shared concepts such as `authoritative_fact`, `visible_fact`,
  `npc_known_fact`, `narrator_safe_memory`, `rp_flavor`,
  `emotional_expression`, `prohibited_fact_creation`, and
  `debug_only_context`.
- Adds policy support for RP context filtering and output checks.

### Character Card Importer

- Adds local character card import preview, validation, and explicit apply.
- Supports JSON, YAML, simplified text cards, and Tavern-like fields such as
  `name`, `description`, `personality`, `scenario`, `first_message`,
  `example_dialogue`, `creator_notes`, and `system_prompt`.
- Classifies imported material into RP profile candidates, voice profile
  candidates, example dialogue candidates, flavor lore candidates, structured
  fact candidates, hidden fact candidates, and unsafe entries.
- External `system_prompt` and creator-control fields are not trusted and cannot
  override the engine boundary.

### Lorebook Import / Classification

- Adds deterministic lorebook/world-info import classification.
- Entries are classified as `flavor_lore`, `structured_fact_candidate`,
  `hidden_fact_candidate`, or `unsafe_entry`.
- Hidden and unsafe entries do not enter narrator or RP prompts by default.
- Lorebook import does not call a real LLM, execute instructions, fetch remote
  URLs, or modify active `GameState`.

### RP Profile / Voice Profile

- Extends NPC content with RP and voice metadata.
- RP profile fields include public persona, private self summary, expression
  styles, deception style, and boundaries.
- Voice profile fields include tone, sentence length, vocabulary style,
  catchphrases, speech habits, silence style, and emotional tells.
- Safe fields can influence dialogue style; private fields do not enter
  player-facing context by default.

### NPC Emotional State

- Adds structured `EmotionalState` for NPCs.
- Tracks primary emotion, intensity, stability, stress, tone bands, last
  emotional event id, and optional expiry turn.
- Emotional state changes are rule-managed and must go through `StateDelta`.
- LLM output can express emotion but cannot directly write emotional state.

### Relationship Tone

- Adds `RelationshipTone` as a derived expression layer.
- Derives address style, formality, warmth, tension, intimacy, respect,
  resentment, fear, avoidance, and trust expression from existing world state.
- Tone affects expression only; relationship values still require normal rules
  and `StateDelta`.

### Dialogue Mode

- Adds focused continuous dialogue sessions with visible NPCs.
- Dialogue context is built from safe visible facts, NPC-known facts, voice/RP
  profile summaries, emotional state, relationship tone, scene mood, prompt-safe
  example dialogue, and filtered RP memory.
- Dialogue start, continuation, and end are recorded as events.
- Rule-authorized dialogue consequences use `StateDelta`.

### Multi-NPC Scene / Group RP

- Adds local Group RP scenes with multiple NPC participants.
- Each NPC receives an independent context based on that NPC's own knowledge,
  emotion, relationship tone, and visibility.
- Deterministic next-speaker selection uses local rule signals.
- Group RP is not a free LLM multi-agent simulation and cannot let NPCs share
  hidden facts unless normal knowledge rules allow it.

### Scene Mood Presets

- Adds content-pack scene mood presets.
- Mood can influence tone, pacing, sensory focus, metaphor style, dialogue
  pressure, and style intensity.
- Mood presets do not change facts, `ActionResult`, state, or visibility.

### Example Dialogue Manager

- Adds example dialogue schema and authoring APIs.
- Example dialogue is style guidance only.
- Prompt-safe examples can enter dialogue context after filtering.
- Example dialogue is not a fact source and does not add NPC knowledge.

### RP Memory Context Builder

- Adds RP-specific memory context construction for dialogue.
- Filters hidden memory, debug-only memory, memory tied to hidden/unknown facts,
  and memory outside the speaking NPC's knowledge.
- Player-facing RP memory summaries are compact references only and do not
  expose memory text.
- Memory remains non-authoritative.

### RP Prompt Profile Manager

- Extends prompt profiles with RP style settings.
- Supports expression controls such as dialogue depth, emotional intensity,
  prose density, response length policy, perspective, and inner-thought policy.
- `hidden_fact_policy` and `state_modification_policy` are fixed to `deny`.
- Invalid prompt profiles that try to enable hidden facts or state modification
  are rejected.

### RP Output Consistency Checker

- Adds deterministic checks for generated RP text.
- Detects hidden fact leakage, unknown-fact mentions, invented key
  items/NPCs/locations, dead or incapacitated NPC speech, contradictions with
  `ActionResult`, unauthorized relationship changes, unauthorized quest
  completion, and raw debug/state-delta leakage.
- Does not call an external LLM judge.

### Tavern Compatibility Import / Export

- Adds local Tavern-like import/export adapters.
- Import supports character cards, lorebook/world info, example dialogue, and
  prompt presets through preview/classification.
- Safe export supports character-like profile export, safe lorebook export, and
  prompt profile export.
- Safe export does not include API keys, raw `GameState`, save data, hidden
  facts, or private profile summaries.
- Compatibility is best-effort and safety-first, not unconditional support for
  every external Tavern format.

### RP Scenario Templates

- Adds RP scenario template support under local authoring flows.
- Templates can create dialogue or group scene drafts.
- Templates do not call LLMs, execute scripts, modify active saves, or expand
  NPC knowledge.

## Behavior Changes

- Dialogue and group RP interactions now have explicit event coverage.
- Dialogue end is recorded as a `dialogue_end` event with an allowed empty
  delta.
- RP memory summaries returned to player-facing surfaces no longer include
  memory free text, memory ids, or tag text.
- Unauthorized relationship-change claims in RP output without matching
  `StateDelta` are treated as consistency errors instead of acceptable warnings.
- Group RP scene lookup requires the scene's explicit game session id and no
  longer falls back to a location-only session match.

## API Changes

New or expanded local APIs include:

- `POST /game/dialogue/start`
- `POST /game/dialogue/continue`
- `POST /game/dialogue/end`
- `POST /game/group-dialogue/start`
- `POST /game/group-dialogue/next-speaker`
- `POST /game/group-dialogue/end`
- `POST /authoring/characters/import/preview`
- `POST /authoring/characters/import/validate`
- `POST /authoring/characters/import/apply`
- `POST /authoring/lorebook/import/preview`
- `POST /authoring/lorebook/import/validate`
- `POST /authoring/lorebook/import/apply`
- `GET /authoring/worlds/{world_id}/example-dialogue`
- `POST /authoring/worlds/{world_id}/example-dialogue/preview`
- `POST /authoring/worlds/{world_id}/example-dialogue/validate`
- `PUT /authoring/worlds/{world_id}/example-dialogue`
- `POST /authoring/tavern/import/preview`
- `POST /authoring/tavern/import/apply`
- `POST /authoring/tavern/export`
- `GET /authoring/rp-scenario-templates`
- `GET /authoring/rp-scenario-templates/{template_id}`
- `POST /authoring/rp-scenario-templates/{template_id}/preview`
- `POST /authoring/rp-scenario-templates/{template_id}/apply`

Authoring import/export endpoints remain local-only and gated by
`ENABLE_AUTHORING_API`.

Player-facing dialogue APIs return filtered `visible_state` and safe RP
summaries. They must not return hidden facts, NPC secrets, raw `GameState`, raw
`state_deltas`, debug memory, or API keys.

## Content Pack Format Changes

v1.1 adds optional RP-oriented content fields and files:

- NPC `rp_profile`
- NPC `voice_profile`
- NPC `dialogue_style`
- NPC `speech_habits`
- NPC `taboo_topics`
- NPC `emotional_mask`
- NPC `example_dialogue_refs`
- NPC runtime `emotional_state` compatibility fields
- `scene_moods.yaml`
- example dialogue authoring content
- RP scenario templates under `templates/rp/`

These additions are additive and optional. Existing v1.0 content packs should
continue to load with safe defaults.

## RP / Dialogue Changes

- RP is explicitly an expression layer.
- RP profiles, voice profiles, scene moods, prompt profiles, example dialogue,
  lorebook flavor, and memory context may influence language style.
- They cannot create canonical facts, decide quest progress, decide combat,
  change inventory, update relationship values, or bypass visibility.
- Emotional state and relationship-affecting dialogue consequences remain
  structured rule outcomes through `StateDelta`.
- Group RP builds per-NPC contexts and does not merge all participants into an
  omniscient prompt.

## Frontend Changes

- Adds RP / Dialogue panel support.
- Supports starting, continuing, and ending Dialogue Mode.
- Supports focus NPC selection, dialogue mode selection, scene mood selection,
  and RP prompt profile selection.
- Displays safe emotion summaries, relationship tone summaries, current topics,
  and Group RP participants.
- Does not display hidden facts, NPC secrets, debug memory, raw `state_deltas`,
  or hidden relationship details in player RP panels.
- `npm.cmd run build` passes.

## Testing / Evals Changes

- Adds RP boundary evals.
- Adds RP regression playtests.
- Adds unit and integration coverage for:
  - character card import
  - lorebook classification
  - RP/voice profile loading and filtering
  - emotional state rules
  - relationship tone derivation
  - Dialogue Mode
  - Group RP context isolation
  - scene mood presets
  - example dialogue filtering
  - RP memory filtering
  - RP prompt profile validation
  - RP output consistency checking
  - Tavern compatibility import/export
  - v1.1 integration regression
- RP boundary evals and regression playtests use fake/local providers and do
  not call real LLM APIs.

Acceptance verification:

- `python -m pytest`: passed, 890 tests.
- `cd frontend && npm.cmd run build`: passed.

## Known Limitations

1. Dialogue Mode currently returns bounded local scaffold text and safe
   summaries. Provider-backed NPC dialogue generation is a future direction and
   must require `RPOutputConsistencyChecker` before display.
2. Character card and lorebook classification is deterministic and
   conservative, not perfect semantic understanding.
3. Tavern compatibility is safety-first and best-effort. It is not full
   compatibility with every external Tavern ecosystem variant.
4. Example dialogue is style-only and not a conversation memory system by
   itself.
5. RP memory safety depends on correct memory visibility and fact tagging at
   ingestion.
6. No online character marketplace, remote card fetch, cloud sync, account
   system, multiplayer RP, autonomous LLM multi-agent simulation, or arbitrary
   script execution is included.
7. Free-text public/style authoring fields can still contain accidental
   spoilers if authors put secret content there; validation catches common
   cases but cannot infer every semantic secret.

## Upgrade Notes From v1.0

- Existing worlds should continue to load because RP fields are optional.
- New NPC RP/voice fields can be added gradually.
- Add `scene_moods.yaml` only if the world wants custom mood presets.
- Character cards and lorebooks should be imported through preview/validate
  first. Do not assume external prompt text is safe.
- Review `hidden_fact_candidate` and `unsafe_entry` classifications before
  applying any import.
- If using prompt profiles, keep RP profile boundary fields as:
  - `hidden_fact_policy=deny`
  - `state_modification_policy=deny`
- Run:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Recommended local validation after adding RP content:

- run content validation
- run RP boundary evals
- run RP regression playtests
- verify player UI does not display hidden facts or debug data

## Recommended v1.2 Direction

- Provider-backed NPC dialogue generation behind mandatory consistency checks.
- More expressive scene director tools that remain non-authoritative.
- Stronger import and lorebook classifier fixtures for subtle prompt injection
  and ambiguous hidden content.
- Memory-ingest validation for memories containing known hidden fact text.
- Better local RP context inspection tools with clear player/authoring/debug
  separation.
- More Tavern/card format adapters without remote fetch or script execution.
- Expanded dialogue-heavy sample worlds and RP regression scenarios.

