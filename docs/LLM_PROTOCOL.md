# LLM Protocol

## Purpose

The LLM protocol defines how this project talks to model providers without letting model output become trusted world state. All LLM calls pass through `LLMProvider`, and structured outputs are validated with Pydantic schemas.

## Provider Boundary

Runtime provider construction must go through:

- `backend/app/llm/provider_factory.py`
- `create_llm_provider(settings)`

The factory reads `LLM_PROVIDER` from settings/environment.

Supported values:

- `mock`: default for local development and tests.
- `openai`: OpenAI API provider.

Business modules should depend on `LLMProvider`, not `OpenAIProvider` or any vendor SDK. Tests may use `FakeLLMProvider` as a controlled test double.

## Credentials

API keys are read only from environment variables.

- `LLM_API_KEY` is required when `LLM_PROVIDER=openai`.
- Real API keys must not be committed, logged, written into fixtures, or returned from APIs.
- Missing OpenAI credentials fail with a clear `LLMProviderError`.
- Unknown providers fail with a clear `LLMProviderError`.

## Current LLM Uses

### IntentParser

`IntentParser` receives player text and asks the provider for a schema-validated `PlayerIntent`.

The parsed intent is input to the world engine. It does not modify `GameState`.

### Narrator

`Narrator` renders player-facing prose after the world engine has already resolved the action.

Inputs include:

- player input
- safe action result payload
- `visible_facts`
- current location
- tone

`Narrator` does not receive:

- `ActionResult.hidden_facts`
- raw `GameState`
- raw system tick deltas
- NPC secrets
- debug timeline events

The narrator returns a schema-validated `NarrativeResult`.

### MemorySummarizer

`MemorySummarizer` summarizes recent events into `MemorySummary`.

It does not:

- mutate `GameState`
- apply `StateDelta`
- write `EventLog`
- promote summary text into canonical facts

Memory summaries are internal and must not replace structured state.

## v0.3 Rule Modules Do Not Call LLM

The following v0.3 modules are deterministic rule/code paths and do not call `LLMProvider`:

- search
- inventory rules
- lockpick
- sneak
- quest state machine
- NPC schedule resolver
- world tick
- debug timeline API

They may receive `PlayerIntent` as input, but action results and state changes are decided by Python rules and emitted as `StateDelta`.

## Output Validation

All LLM JSON outputs must validate against Pydantic schemas:

- `PlayerIntent`
- `NarrativeResult`
- `MemorySummary`

Schema validation failure must not silently modify state. Provider or parser errors should surface as controlled errors or explicit fallback behavior.

## Error Handling

If an LLM call fails:

- do not mutate `GameState`
- do not apply deltas based on failed output
- return a clear application/provider error
- do not print secrets or environment values

If narrator generation fails after rule resolution, `GameLoop` must not commit state or append events for the failed step.

## Visibility Rules for Prompts

Prompt inputs must obey world visibility:

- player-visible facts only
- no hidden facts unless discovered and promoted to `player_visible_facts`
- no NPC secrets unless rules explicitly made them visible
- no debug timeline data in narrative prompts
- no raw `hidden_facts` field in narrator payloads

The LLM can render prose, but it cannot create canonical items, NPCs, locations, quest progress, or facts.

