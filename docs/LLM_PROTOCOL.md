# LLM Protocol

## Purpose

The LLM protocol defines how this project talks to model providers without letting model output become trusted world state. All LLM calls pass through `LLMProvider`, and structured outputs are validated with Pydantic schemas.

The LLM is a parser, narrator, and summarizer. It is not the world judge.

## Provider Boundary

Runtime provider construction must go through:

- `backend/app/llm/provider_factory.py`
- `create_llm_provider(settings)`

The factory reads `LLM_PROVIDER` from settings/environment.

Supported values:

- `mock`: default for local development and tests.
- `openai`: OpenAI API provider.

Business modules depend on `LLMProvider`, not `OpenAIProvider` or a vendor SDK. Tests may use `FakeLLMProvider` as a controlled test double.

## Credentials

API keys are read only from environment variables.

- `LLM_API_KEY` is required when `LLM_PROVIDER=openai`.
- Real API keys must not be committed, logged, written into fixtures, returned from APIs, or stored in saves.
- Missing OpenAI credentials fail with a clear `LLMProviderError`.
- Unknown providers fail with a clear `LLMProviderError`.

## Current LLM Uses

### IntentParser

`IntentParser` receives player text and asks the provider for a schema-validated `PlayerIntent`.

The parsed intent is input to the world engine. It does not modify `GameState`.

If provider/schema failure occurs, the parser returns a controlled clarification/unknown intent rather than applying world changes.

### Narrator

`Narrator` renders player-facing prose after the world engine has already resolved the action.

Inputs include:

- player input
- safe action result payload
- `visible_facts`
- current location id
- tone

`Narrator` does not receive:

- `ActionResult.hidden_facts`
- raw `GameState`
- raw system tick deltas
- raw debug event timeline
- witness records
- NPC secrets
- hidden/debug memories

Current caution: `Narrator` receives `ActionResult.reason`. Rule authors must keep this reason player-safe. A future hardening pass should split `player_reason` and `debug_reason`.

### MemorySummarizer

`MemorySummarizer` summarizes recent events into `MemorySummary`.

It does not:

- mutate `GameState`
- apply `StateDelta`
- write `EventLog`
- promote summary text into canonical facts
- replace structured state

Because event payloads can contain raw `state_deltas`, summaries derived from hidden/debug events should be stored as `debug_only` or `hidden` unless explicitly sanitized.

### Advanced Memory Retrieval

Memory retrieval is local deterministic code and does not call the LLM.

`MemoryRecord.visibility` values:

- `player_visible`
- `narrator_safe`
- `debug_only`
- `hidden`

Narrator-safe memory filtering must use:

- `filter_narrator_safe_memories`

Allowed for narrator:

- `player_visible`
- `narrator_safe`

Forbidden for narrator:

- `debug_only`
- `hidden`

Player-facing memory filtering must use:

- `filter_player_visible_memories`

Allowed for player response:

- `player_visible`

## v0.4 Rule Modules Do Not Call LLM

The following v0.4 modules are deterministic rule/code paths and do not call `LLMProvider`:

- content validation tools
- faction reputation
- rumor propagation
- crime/witness rules
- social consequence tick
- combat core
- injury/death/incapacitation rules
- NPC reaction rules
- advanced memory retrieval

Existing deterministic v0.3/v0.4 rule paths also do not call the LLM:

- search
- inventory rules
- lockpick
- sneak
- quest state machine
- NPC schedule resolver
- world tick
- debug timeline API

They may receive a schema-validated `PlayerIntent`, but action results and state changes are decided by Python rules and emitted as `StateDelta`.

## Output Validation

All LLM JSON outputs must validate against Pydantic schemas:

- `PlayerIntent`
- `NarrativeResult`
- `MemorySummary`

Schema validation failure must not silently modify state.

Observed behavior:

- `IntentParser` falls back to a clarification/unknown intent.
- `Narrator` errors propagate; `GameLoop` tests ensure state/event commit does not happen after narrator failure.
- `MemorySummarizer` invalid schema raises provider error.

## Error Handling

If an LLM call fails:

- do not mutate `GameState`
- do not apply deltas based on failed output
- return a clear application/provider error or controlled fallback
- do not print secrets or environment values

If narrator generation fails after rule resolution, `GameLoop` must not commit state or append events for the failed step.

## Visibility Rules For Prompts

Prompt inputs must obey world visibility:

- player-visible facts only
- narrator-safe memories only, if memory is introduced to narrator context
- no hidden facts unless discovered and promoted to `player_visible_facts`
- no NPC secrets unless deterministic rules explicitly make them player-visible
- no debug timeline data in narrative prompts
- no raw `state_deltas` in narrative prompts
- no raw `hidden_facts` field in narrator payloads
- no hidden witness identities unless discovered

The LLM can render prose, but it cannot create canonical items, NPCs, locations, quest progress, crimes, rumors, combat outcomes, faction changes, memories, or facts.

## Known v0.4 Hardening Items

- Split `ActionResult.reason` into `player_reason` and `debug_reason`.
- Classify memory summaries from raw non-player-visible events as `debug_only` or `hidden` by default.
- Rewrite any mojibake prompt text into clean UTF-8 wording.
- Keep raw debug data out of narrator-facing memory retrieval.
