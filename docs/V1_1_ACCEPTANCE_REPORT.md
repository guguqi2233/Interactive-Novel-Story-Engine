# v1.1 Acceptance Report: Roleplay Immersion Layer

## Verdict

Accepted for v1.1 release candidate.

The v1.1 Roleplay Immersion Layer is accepted as a bounded local RP layer on top
of the v1.0 stable world engine. The reviewed implementation adds character
card and lorebook import, RP/voice profiles, emotional state, relationship tone,
Dialogue Mode, Group RP, scene moods, example dialogue, RP memory context,
RP prompt profiles, RP output consistency checks, Tavern-compatible local
import/export, RP frontend panels, RP scenario templates, RP boundary evals,
and RP regression playtests while preserving the core rule:

Expression may vary; world facts remain controlled by the engine.

No acceptance blocker remains after the v1.1 release-blocker fixes for safe RP
memory summaries, dialogue end events, stricter unauthorized relationship-change
checking, and Group RP session lookup.

## Verification Date

2026-05-19

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Results:

- `python -m pytest`: passed, 890 tests.
- `cd frontend && npm.cmd run build`: passed, TypeScript build and Vite
  production build completed.

## Scope Accepted

### Roleplay Boundary Contract

Accepted.

- `docs/ROLEPLAY_BOUNDARY.md` explicitly separates expressive RP context from
  authoritative world facts.
- The boundary prohibits LLM direct `GameState` mutation, hidden fact leakage,
  raw debug/state-delta exposure, example-dialogue-as-fact behavior, and
  imported prompt override.
- `RoleplayContextPolicy` and RP boundary tests cover player-facing, NPC
  dialogue, narrator-safe, debug-only, and unsafe context classes.

### Character Card Importer

Accepted.

- Character card import supports preview, validation, and explicit apply.
- JSON, YAML, simple text cards, and Tavern-like fields are normalized and
  classified into RP profile candidates, voice profile candidates, example
  dialogue candidates, flavor lore candidates, structured fact candidates,
  hidden fact candidates, and unsafe entries.
- External `system_prompt` and creator prompt/control fields are treated as
  unsafe when they attempt to widen authority.
- Preview does not write disk or active `GameState`.
- Apply is local authoring only, explicit, and validation-gated.

### Lorebook Import / Classification

Accepted.

- Lorebook entries are classified as `flavor_lore`,
  `structured_fact_candidate`, `hidden_fact_candidate`, or `unsafe_entry`.
- Hidden and unsafe entries do not enter narrator or RP prompts by default.
- Import rejects remote URL/script-like content and does not execute entry
  instructions.
- Apply remains explicit authoring content-pack work, not active state mutation.

### RP Profile / Voice Profile

Accepted.

- NPCs can load RP and voice profile fields.
- Safe voice/style fields can influence dialogue context.
- `private_self_summary`, taboo topics, and authoring/private fields do not
  enter player-facing context by default.
- Profiles affect expression only and do not grant NPC knowledge, change
  relationship values, override `ActionResult`, or mutate `GameState`.

### NPC Emotional State

Accepted.

- `EmotionalState` is structured NPC state.
- Emotion changes are rule-side state changes represented by `StateDelta`.
- Dialogue-related emotional shifts are deterministic and tested.
- Dead/incapacitated NPCs do not receive ordinary dialogue emotion updates.
- Save/load coverage preserves emotional state compatibility.

### Relationship Tone

Accepted.

- `RelationshipTone` is derived from relationship state, emotion, faction
  context, and safe rule signals.
- It is an expression layer, not a replacement for `RelationshipState`.
- Hidden relationship details do not enter player graph or ordinary dialogue
  summaries.
- Unauthorized relationship-change claims without matching `StateDelta` are now
  treated as consistency errors.

### Dialogue Mode

Accepted.

- `DialogueSession` can be created, continued, and ended.
- Dialogue target validation requires the NPC to exist, be present,
  player-visible, and able to talk.
- Dialogue context uses NPC knowledge and visibility filtering.
- Rule-authorized dialogue consequences use `StateDelta`.
- Dialogue start, continuation, and end events are recorded.
- RP output consistency checks cover prohibited fact creation, state change
  claims, hidden leaks, unknown facts, raw debug/state-delta text, and other
  boundary violations.

Known implementation note: the current player API returns bounded local
dialogue scaffold text rather than provider-backed NPC dialogue generation. Any
future generated NPC text must pass through `RPOutputConsistencyChecker` before
player display.

### Multi-NPC Scene / Group RP

Accepted.

- `GroupDialogueScene` and `GroupDialogueManager` support local group scenes.
- Participant contexts are built independently per NPC.
- NPCs do not receive facts outside their own knowledge context.
- Dead/incapacitated NPCs cannot participate in ordinary group chat.
- Group scene start, next-speaker, and end actions record events.
- Group scene lookup now requires the scene's explicit game session id and no
  longer falls back to a location-only session match.

### Scene Mood Presets

Accepted.

- Scene mood presets load from content-pack data.
- Mood affects tone, pacing, sensory focus, and expression style only.
- Mood cannot alter `ActionResult`, state, facts, visibility, or NPC knowledge.
- Invalid mood presets are validated.

### Example Dialogue Manager

Accepted.

- Example dialogue is style guidance only.
- Prompt selection is limited to `prompt_safe` examples and safe fact policies.
- Hidden, debug-only, authoring-only, or unsafe examples stay out of runtime
  RP prompts.
- Example dialogue does not become a `GameState` fact and does not add NPC
  knowledge.

### RP Memory Context Builder

Accepted.

- RP memory context filters hidden memory, debug-only memory, memories linked to
  hidden/unknown facts, and memories outside the speaking NPC's knowledge.
- Memory remains non-authoritative and cannot override `GameState`.
- Player-facing RP memory summaries are now compact references only and do not
  include memory text, memory ids, or tag text.
- Debug exclusion reasons remain debug-only.

### RP Prompt Profile Manager

Accepted.

- RP prompt profile style fields can tune dialogue depth, emotional intensity,
  prose density, response length, perspective, and related expression controls.
- `hidden_fact_policy` and `state_modification_policy` are fixed to `deny`.
- Validation rejects profiles that attempt to enable hidden facts or state
  modification.
- Prompt profiles do not change visible facts, NPC knowledge, `ActionResult`,
  `StateDelta`, quest state, or world rules.

### RP Output Consistency Checker

Accepted.

- Checker detects hidden fact leakage, NPC unknown fact mentions, invented
  key item/NPC/location markers, dead/incapacitated NPC speech, contradiction
  with `ActionResult`, unauthorized relationship change, unauthorized quest
  completion, and raw debug/state-delta leakage.
- Checker is deterministic code, not an external LLM judge.
- Serious issues request retry or fallback and do not mutate state.

### Tavern Compatibility Import / Export

Accepted.

- Local compatibility import supports character cards, lorebooks/world info,
  example dialogue, and prompt presets through preview/classification paths.
- Safe export excludes API keys, raw `GameState`, save data, hidden facts, and
  private profile summaries.
- Path traversal, remote URL references, scripts, and untrusted external
  system prompts are rejected or quarantined.
- Apply requires explicit confirmation and validation.

### RP Frontend Panels

Accepted.

- Frontend RP / Dialogue panel supports dialogue controls, focus NPC, dialogue
  mode, scene mood, RP prompt profile, safe emotion/tone summaries, topics, and
  group scene participant display.
- The frontend build passes.
- Player UI uses safe summary fields and does not display hidden facts, NPC
  secrets, debug memory, raw state deltas, or hidden relationship details.
- Authoring/debug data remains separate from player RP panels.

### RP Scenario Templates

Accepted.

- RP scenario templates support preview/apply draft flows.
- Templates create dialogue or group scene drafts and do not modify
  `GameState`, active saves, or NPC knowledge directly.
- Required participants and visible-fact requirements are validated.
- Templates do not call LLMs or execute scripts.

### RP Boundary Evals And RP Regression Playtests

Accepted.

- RP boundary evals cover hidden fact leakage, unknown fact mentions, example
  dialogue misuse, hidden lore prompt entries, emotional-state state changes,
  relationship tone misuse, group context crossover, and scene mood fact
  override.
- RP regression playtests cover friendly talk, secret probing, interrogation,
  group scenes, deterministic seeds, and safe reporting.
- Tests use fake/local providers and do not call real APIs.

### v1.1 Integration Tests

Accepted.

- v1.1 integration regression tests cover imports, RP/voice profile context,
  emotion and relationship tone boundaries, Dialogue Mode, Group RP, scene mood,
  prompt profiles, RP memory, frontend-safe API surfaces, and no hidden/debug
  data in normal RP surfaces.
- Full backend suite passes.

## Boundary Review

### LLM Authority

Accepted.

- LLM remains a parser, narrator, summarizer, authoring draft assistant, and RP
  expression layer.
- LLM output does not directly modify `GameState`.
- Provider selection remains through `LLMProvider` and provider factory.
- Tests use mock, local stub, fake provider, or fake transport.

### StateDelta And EventLog

Accepted.

- Canonical relationship/emotion changes in dialogue are emitted as
  `StateDelta`.
- Dialogue start, dialogue continuation, dialogue end, group scene start,
  group next-speaker, and group scene end record events.
- Pure expressive events use empty deltas with explicit `allow_empty_delta`.

### Visibility And NPC Knowledge

Accepted.

- Hidden facts do not enter `visible_state`.
- Hidden facts do not enter ordinary RP prompt context.
- NPC dialogue context is scoped by NPC knowledge.
- Group RP participant contexts are isolated.
- Private profile fields, hidden memory, debug memory, hidden example dialogue,
  unsafe lorebook entries, and raw `state_deltas` do not enter player/RP
  surfaces.

### Import / Export Safety

Accepted.

- Character cards, lorebooks, Tavern resources, examples, and templates are
  treated as untrusted local authoring input.
- Import flows do not execute scripts, read remote URLs, or directly apply
  prompt instructions.
- Safe export does not include API keys, raw state, save data, or hidden facts.

### Frontend Safety

Accepted.

- RP panel displays safe summaries and counts rather than raw hidden/debug
  details.
- Debug/authoring surfaces remain separate from player surfaces.
- Frontend build passes.

## Known Limitations

1. Dialogue Mode currently returns bounded local response text and safe context
   summaries. A future provider-backed NPC line generator must make
   `RPOutputConsistencyChecker` mandatory before player display.
2. Character card and lorebook classification is deterministic and conservative,
   not semantic-perfect. Ambiguous spoilers may still require local author
   review.
3. `CharacterCardImport.source_name` and `LorebookImport.source_name` are
   metadata-only and not filesystem paths, but they could use the same explicit
   separator validation as Tavern import as defense in depth.
4. RP memory safety depends on correct memory visibility/fact tagging at
   ingestion. The current player-facing summaries no longer expose memory text,
   but stronger memory-ingest validation remains useful.
5. No online Tavern resource marketplace, remote card fetcher, cloud sync,
   account system, multiplayer RP, autonomous LLM multi-agent simulation, or
   full external Tavern format compatibility is included.
6. RP profile, scene mood, prompt profile, example dialogue, and lorebook
   fields are style/content metadata. They are not formal safety classifiers for
   arbitrary malicious text beyond the current local validation rules.

## Acceptance Risks

No high-risk acceptance blocker remains.

Residual non-blocking risks:

- Future LLM-backed dialogue generation must not bypass the RP consistency
  checker.
- Free-text authoring fields can still contain spoilers if authors place secret
  content into fields that are explicitly public/style fields.
- Import classification should keep gaining fixtures for subtle prompt
  injection and spoiler phrasing.
- Any future authoring-debug Tavern export mode that includes hidden/private
  material must require explicit local-only warnings and separate tests.

## Recommended v1.2 Priorities

1. Provider-backed NPC dialogue generation behind mandatory consistency checks.
2. More expressive scene director tools that remain non-authoritative.
3. Stronger import/lorebook classifier fixtures for subtle prompt injection and
   ambiguous hidden content.
4. Memory-ingest validation that requires fact bindings for memory containing
   known hidden fact text.
5. Better local RP context inspection tools that clearly separate player,
   authoring, and debug views.
6. More Tavern/card format adapters without remote fetch or script execution.
7. Expanded dialogue-heavy sample worlds and RP regression scenarios.

## Final Status

v1.1 is accepted as a release candidate.

The Roleplay Immersion Layer adds richer character expression, continuous
dialogue, group RP, local import/export compatibility, and RP-specific
regression checks without breaking the v1.0 engine boundary. `GameState`,
`StateDelta`, `EventLog`, visibility, NPC knowledge, provider abstraction, and
local-only tooling boundaries remain intact.

