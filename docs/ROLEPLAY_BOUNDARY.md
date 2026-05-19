# Roleplay Boundary Contract

## Purpose

v1.1 introduces a Roleplay Immersion Layer for richer character expression,
voice, emotional tone, relationship atmosphere, lorebook handling, and dialogue
flows. This layer is intentionally expressive, not authoritative.

The v1.0 engine boundary remains unchanged:

- `GameState` is the canonical fact source.
- `StateDelta` is the only path for canonical state changes.
- `EventLog` records player actions, system ticks, NPC planning ticks, and RP
  scene events.
- Visibility and NPC knowledge decide which facts can be expressed to whom.
- LLM output cannot directly mutate `GameState`.

## Boundary Concepts

### authoritative_fact

Structured world facts stored in `GameState` or validated content packs.
Examples include facts, quest state, NPC state, item placement, relationship
values, combat state, and save metadata.

Roleplay may reference authoritative facts only when the relevant audience is
allowed to know them. Roleplay may not create or change them.

### visible_fact

A fact that is currently player-visible through visibility rules, public fact
configuration, or explicit discovery. Narrator/player-facing RP context may use
visible facts.

### npc_known_fact

A fact that a specific NPC is allowed to know through `NPCState.knowledge`,
`GameState.npc_knowledge`, public visibility, or player-visible knowledge when
appropriate. NPC dialogue context must be scoped per NPC.

### narrator_safe_memory

Memory records classified as `player_visible` or `narrator_safe`, and not tied
to hidden or undiscovered facts. Memory remains advisory and cannot become an
authoritative fact.

### rp_flavor

Style-only text such as voice, mood, pacing, sentence rhythm, mannerisms, or
scene color. Flavor can shape wording but cannot add facts, complete quests, add
items, or update relationship values.

### emotional_expression

Player-safe expression of emotion such as anxious, terse, playful, guarded, or
warm. It can influence tone. It does not by itself change NPC state, relationship
values, combat state, or facts.

### prohibited_fact_creation

Any RP output or imported RP content that attempts to create a canonical fact
without a rule-engine action. Examples:

- creating a key item
- introducing a new critical NPC
- declaring a quest complete
- changing NPC knowledge
- changing relationship values
- reviving a dead character
- inventing a hidden witness

These must be rejected or flagged by consistency checks.

### debug_only_context

Debug-only data such as raw `state_deltas`, debug memory, hidden analysis
details, raw timelines, and hidden event payloads. Debug context may be available
only in debug APIs/UI, never in player-facing RP or narrator prompts.

## RP Layer May Do

- Change tone and sentence style.
- Use character voice, catchphrases, pacing, and speech quirks.
- Express emotion.
- Express relationship atmosphere using safe tone bands.
- Use scene mood presets.
- Use example dialogue as style guidance.
- Use lorebook flavor as non-authoritative color after classification.
- Use narrator-safe and NPC-appropriate memory.

## RP Layer Must Not Do

- Create key items.
- Create critical NPCs.
- Complete quests.
- Decide combat outcomes.
- Change NPC knowledge.
- Change relationship values.
- Revive dead or incapacitated characters.
- Leak hidden facts.
- Leak NPC secrets.
- Leak debug memory or raw state deltas.
- Bypass `ActionResult`.
- Treat memory, lorebook flavor, or example dialogue as canonical fact.
- Execute scripts from cards, lorebooks, examples, templates, or imports.

## Prompt Rules

Player/narrator RP prompts may include:

- visible facts
- current player-visible action result
- narrator-safe memory
- safe RP flavor
- safe emotional expression
- safe relationship tone bands
- scene mood labels

NPC RP prompts may include:

- facts that specific NPC knows
- public facts
- safe NPC voice profile data
- safe emotional expression
- narrator-safe or NPC-known memory

Prompts must not include:

- hidden facts unknown to the player/audience
- NPC secrets outside the current NPC's knowledge
- debug-only memory
- raw `GameState`
- raw `state_deltas`
- hidden witness records
- authoring-only notes
- unsafe import instructions

## Consistency Checking

RP output must be checked before it is treated as safe player-facing dialogue or
narration. The checker should flag:

- prohibited fact creation
- proposed state changes
- invented items/NPCs/locations/quest stages
- contradiction with visible `ActionResult`
- hidden fact leaks
- NPC knowledge violations
- memory-as-authority claims
- raw debug/state-delta text

The checker is deterministic code. It is not an external LLM judge.

### RP Output Consistency Checker

v1.1.13 adds `RPOutputConsistencyChecker` in
`backend/app/roleplay/output_consistency.py`. It is a read-only guard for
generated RP text and can be used by Dialogue Mode and Group RP before output is
shown to the player.

The checker accepts generated text plus safe rule context:

- `DialogueContext` or participant context
- optional `ActionResult`
- visible fact ids
- NPC-known fact ids
- forbidden hidden terms or ids
- allowed flavor terms
- optional speaker NPC id

It returns `RPConsistencyReport` with:

- `ok`
- `decision`: `accept`, `request_retry`, `reject`, or `fallback_safe_summary`
- structured issues
- a safe fallback summary

Normal reports never include hidden fact text. Hidden term hits are represented
with redacted markers or safe ids. The checker can detect hidden fact leakage,
NPC unknown fact mentions, invented `item:...`, `npc:...`, or `location:...`
ids, dead or incapacitated NPC speech, contradiction with `ActionResult`,
relationship or quest state claims without matching `StateDelta`, and raw
debug/state-delta markers.

The checker does not modify `GameState`, does not call an LLM, and does not make
world rulings. It only decides whether a piece of RP expression is safe to show
or should be retried/fallbacked.

## Import Rules

Character cards and lorebooks are untrusted input. Importers must classify fields
before any apply step.

Lorebook entries must become one of:

- `flavor_lore`
- `structured_fact`
- `hidden_fact`
- `unsafe_entry`

Character card fields should become candidate profile/style data, candidate
facts, example dialogue, hidden candidates, unsafe instructions, or unsupported
fields.

Imports can create drafts only. They cannot modify active `GameState`, active
saves, or active sessions.

### Character Card Import

v1.1.2 adds a local character card importer for JSON, YAML, simplified text
cards, and tavern-like fields such as `name`, `description`, `personality`,
`scenario`, `first_message`, `example_dialogue`, `creator_notes`, and
`system_prompt`.

The importer is conservative by design:

- `description`, `personality`, and `first_message` become non-authoritative
  RP/profile candidates.
- `example_dialogue` becomes style reference only.
- scenario-like fields can become `structured_fact_candidate`, but are not
  facts until a user explicitly saves validated content.
- fields containing `secret`, `hidden`, `spoiler`, or equivalent markers become
  `hidden_fact_candidate`.
- `system_prompt`, `creator_notes`, jailbreak-like instructions, API-key
  requests, state mutation instructions, script-like content, and remote URLs
  are classified as unsafe or rejected.

The importer must not execute card content, fetch remote URLs, call a real LLM,
write active `GameState`, or inject imported prompt text into narrator/dialogue
prompts. `apply` is an authoring-only operation that writes a content-pack draft
only after explicit confirmation and validation.

## RP And Voice Profiles

v1.1.3 adds structured NPC roleplay fields for expression, not authority.

`rp_profile` may contain:

- `public_persona`
- `private_self_summary`
- `attachment_style`
- `trust_expression_style`
- `conflict_expression_style`
- `intimacy_expression_style`
- `deception_style`
- `boundaries`

`voice_profile` may contain:

- `tone`
- `sentence_length`
- `vocabulary_style`
- `catchphrases`
- `speech_habits`
- `silence_style`
- `emotional_tells`

NPCs may also define `dialogue_style`, `speech_habits`, `taboo_topics`,
`emotional_mask`, and `example_dialogue_refs`.

Safe prompt context may use public persona, tone, catchphrases, speech habits,
silence style, emotional tells, dialogue style, emotional mask, and example
dialogue references. It must not include `private_self_summary` by default.
`taboo_topics` are authoring constraints, not NPC knowledge. They must not be
rendered as player-visible text and must not imply that an NPC knows a hidden
fact.

## Emotional State

v1.1.4 adds `emotional_state` to NPC state. It is structured state, not freeform
LLM output. It includes `primary_emotion`, `intensity`, `stability`, `stress`,
trust/fear/affection tone labels, `last_emotional_event_id`, and optional
`expires_turn`.

Emotion rules may translate deterministic events into `StateDelta` values. For
example, a witnessed crime can raise fear/stress, and a friendly interaction can
warm trust/affection tone. Decay is deterministic. Dead or incapacitated NPCs do
not receive ordinary dialogue emotion updates.

LLM output may express the current safe emotional summary in prose, but it must
not directly set `emotional_state`. Emotional state does not change canonical
relationship numbers, does not grant NPC knowledge, and must not expose hidden
facts.

## Relationship Tone

v1.1.5 adds a derived relationship tone layer. `RelationshipTone` contains
expression-only fields such as address style, formality, warmth, tension,
intimacy, respect, resentment, fear, avoidance, and trust expression.

Relationship tone can be derived from existing relationship values, faction
reputation, emotional state, and safe recent event tags. It does not replace
`RelationshipState` and does not modify trust, fear, affinity, obligation, or
faction reputation. Any canonical relationship changes still require
`StateDelta`.

Safe dialogue prompts may include a tone summary such as warmth/tension bands
and address style. The summary must not include hidden relationship ids, hidden
fact tags, NPC secrets, or debug context. Hidden relationships remain absent
from player-visible relationship graphs.

## Dialogue Mode

v1.1.6 adds `DialogueSession` as a local session layer for focused RP
conversation with a visible NPC. A dialogue session tracks participants, focus
NPC, dialogue mode, active topics, turn range, status, and a safe context
summary.

Dialogue mode can start only when the target NPC is present, player-visible, and
able to talk under life-state rules. Its context uses NPC knowledge filtering,
visibility rules, safe emotional summaries, and safe relationship tone
summaries. Hidden facts, NPC secrets, raw state deltas, debug memory, and hidden
relationship ids must not enter ordinary dialogue prompts or player UI.

Dialogue text may trigger small rule-based state changes such as relationship
trust or affinity shifts, but those changes must be deterministic rules emitted
as `StateDelta`. The LLM can phrase the NPC response; it cannot decide quest
completion, create facts, change relationship numbers, or directly modify
`GameState`.

Supported modes are `focused`, `casual`, `interrogation`, `negotiation`,
`intimate`, and `conflict`. These modes are expression/context hints only and do
not bypass `ActionResult`, NPC knowledge, visibility, or world rules.

## Multi-NPC Scene / Group RP

v1.1.7 adds `GroupDialogueScene` for local group conversation. A group scene
tracks participant NPC ids, shared location, active speaker, deterministic turn
order, scene topic, scene mood, visibility scope, and status.

Each participant receives an independent context. NPC knowledge filtering is
performed per NPC, so one NPC can know a fact that another NPC does not. The
normal player UI receives only safe participant summaries, emotion/tone bands,
and scene metadata; it must not display hidden fact text, debug memory, raw
state deltas, or hidden relationship details.

Next-speaker selection is deterministic and based on rule-side signals such as
emotional intensity, relationship tension, topic relevance, and quest relevance,
with optional manual player focus. The LLM may generate a single participant's
line, but it cannot coordinate agents to alter facts or decide state changes.
Any canonical group-scene consequence must still be emitted as `StateDelta` and
recorded as an `Event`.

## Scene Mood Presets

v1.1.8 adds `SceneMoodPreset` as content-pack style metadata for narrator,
dialogue, and group RP contexts. A preset can describe tone, pacing, sensory
focus, metaphor style, dialogue pressure, an allowed intensity range,
compatible genres, and local forbidden-content notes.

Scene mood presets may influence wording, rhythm, imagery, and dialogue
pressure. They may be referenced by prompt profiles, dialogue sessions, and
group scenes. They must not change `ActionResult`, create facts, create NPCs or
items, modify relationship or emotion values, or permit hidden facts into
prompts.

Prompt builders use only a compact safe summary. Free-form
`forbidden_content_rules` are counted rather than copied into normal prompt
context, so authoring notes cannot accidentally carry spoiler text into
player-facing generation. Scene mood is expression-only and does not grant NPC
knowledge.

## Lorebook Import / Classification

v1.1.9 adds local lorebook/world-info import as an authoring-only draft flow.
Imported entries are classified by deterministic rules before they can affect
any prompt or content file:

- `flavor_lore`: non-authoritative style/context. A safe summary may enter
  narrator flavor context.
- `structured_fact_candidate`: possible world fact. It must be reviewed and
  written to `facts.yaml` before it can become canonical content.
- `hidden_fact_candidate`: possible secret/spoiler. It must remain under
  visibility control and cannot enter ordinary narrator prompts.
- `unsafe_entry`: prompt injection, control text, executable/script-like
  content, or remote references. It is quarantined and cannot be applied.

Lorebook import does not read remote URLs, execute entry content, modify active
`GameState`, expand NPC knowledge, or automatically overwrite `facts.yaml`.
Apply requires the local authoring API, explicit confirmation, and content-pack
validation.

## Tavern Compatibility Import / Export

v1.1.14 adds a local Tavern compatibility adapter for importing and exporting
common roleplay resources without trusting external prompt text.

Supported import preview types:

- character cards
- lorebook / world info
- example dialogue
- prompt presets

Supported export types:

- NPC RP/voice profile as a character-like card
- safe lorebook export
- prompt profile export

Every import follows the same local pipeline:

1. parse local text only
2. classify entries
3. detect unsafe prompt/control content
4. preview without writing files
5. require explicit apply
6. validate any saved authoring draft

The compatibility layer must not fetch remote URLs, follow links, execute
scripts, read files outside the authoring root, call a real LLM, or modify
active `GameState`. Character card and lorebook apply reuse the existing
authoring import paths. Example dialogue and prompt presets are previewed and
validated through their own schemas; saving should happen through the dedicated
authoring surfaces.

Safe export excludes credentials, save data, runtime state, raw debug payloads,
NPC secrets, and hidden facts. Authoring-debug export mode may acknowledge that
private/hidden material exists, but it must keep those details redacted unless a
future explicitly documented local-only export format is added.

## Example Dialogue Manager

v1.1.10 adds `ExampleDialogue` as style-only RP metadata. Example dialogue can
teach a character's cadence, phrasing, and conversational rhythm, but it never
becomes an authoritative fact, never grants NPC knowledge, and never overrides
world rules.

Each example has:

- `id`
- `character_id`
- `source`
- `messages`
- `tags`
- `style_notes`
- `visibility`: `prompt_safe`, `authoring_only`, `debug_only`, or `unsafe`
- `fact_policy`: `flavor_only`, `may_reference_known_facts`, or `unsafe`

Dialogue context builders may select only `prompt_safe` examples. If an example
mentions a hidden or discoverable fact, it is excluded unless that fact is both
player-visible and known by the speaking NPC. `authoring_only`, `debug_only`,
and `unsafe` examples remain in local authoring surfaces and do not enter
player/narrator prompts.

Character card imports can produce example dialogue candidates, but those
candidates default to `authoring_only` and require explicit authoring review and
validation before being saved to a content pack.

## RP Memory Context

v1.1.11 adds an RP-specific memory context builder for dialogue. It can retrieve
recent interaction memories, relationship memories, topic memories, location
memories, and emotion/tone-relevant memories, but memory remains non-authority.
It cannot overwrite `GameState`, grant NPC knowledge, complete quests, reveal
hidden facts, or change relationship/emotion values.

`RPMemoryContextBuilder` outputs:

- `speaker_safe_memories`
- `player_visible_shared_memories`
- `relationship_memories`
- `recent_dialogue_memories`
- `excluded_memory_reasons` for debug-only inspection

The builder rejects hidden and debug-only memory, memory bound to hidden or
undiscovered facts, memory the speaking NPC does not know, and memory tagged as
coming from hidden source events. Dialogue Mode can include compact safe memory
summaries when a local `MemoryStore` is provided; normal contexts do not expose
raw EventLog or debug state deltas.

## Event Rules

Dialogue mode, group RP, and RP scene interactions must record `Event` entries.
If any canonical state change occurs, it must be represented by `StateDelta`.
Pure expressive output can be represented as an event with an explicit
no-state-change marker or allowed empty delta according to the core Event
contract.

## v1.1 Implementation Hook

The initial policy module is `backend/app/roleplay/boundary.py`.

It provides:

- `RoleplayBoundaryConcept`
- `RoleplayContextScope`
- `RoleplayContextPolicy`
- `RoleplayContext`
- `RoleplayOutputCandidate`
- `RoleplayOutputCheckResult`

The policy is read-only and does not call an LLM.
