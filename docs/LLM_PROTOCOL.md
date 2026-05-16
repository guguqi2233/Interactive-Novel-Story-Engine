# LLM Protocol

## Purpose

The LLM protocol defines how the application talks to model providers without letting model output become trusted world state. All LLM calls must pass through a provider abstraction and all responses must be validated with Pydantic schemas.

## Provider Boundary

Business code should depend on an interface like `LLMProvider`, not a concrete vendor SDK.

Provider construction must go through the centralized factory:

- `backend/app/llm/provider_factory.py`
- `create_llm_provider(settings)`

The factory reads `LLM_PROVIDER` from application settings and supports:

- `mock`: default local-development and test-safe provider.
- `openai`: OpenAI API provider.

Business modules must not instantiate `OpenAIProvider`, `MockLLMProvider`, or `FakeLLMProvider` directly. They should receive an `LLMProvider` instance through dependency wiring. Tests may use `FakeLLMProvider` as a controlled test double.

Provider implementations are responsible for:

- Reading API keys from environment variables.
- Calling the configured model.
- Returning raw text or structured payloads to the protocol layer.
- Avoiding secret logging.

Provider implementations must not:

- Modify `GameState`.
- Write events.
- Apply `StateDelta`.
- Depend on world engine internals beyond explicit request schemas.

## Credentials

API keys must be read from environment variables, for example `LLM_API_KEY`. Real values must never appear in code, docs, tests, logs, or database records.

If `LLM_PROVIDER=openai`, `LLM_API_KEY` is required. Missing credentials must fail with a clear local error and must not silently fall back to another provider. If `LLM_PROVIDER` is unknown, startup or provider creation must fail clearly.

## Initial LLM Tasks

### Intent Parsing

Input:

- Player text.
- Public world state summary.
- Relevant recent events.
- Allowed action vocabulary, if available.

Output schema:

- `intent_type`: normalized action category.
- `actor_id`: acting entity.
- `target_ids`: referenced world entities.
- `arguments`: structured action arguments.
- `confidence`: numeric confidence.
- `raw_notes`: optional short reasoning summary for debugging, never used as authority.

### Narrative Rendering

Input:

- Accepted player event.
- Applied state deltas.
- Resulting public state view.
- Tone and style settings.

Output schema:

- `narration`: player-facing prose.
- `visible_changes`: concise list of changes the player can perceive.
- `npc_lines`: optional structured dialogue lines.

### NPC Dialogue

Input:

- NPC public profile.
- Conversation context.
- Current public state view.
- Relevant memories.

Output schema:

- `speaker_id`.
- `line`.
- `emotion`.
- `intent_hint`.

### Memory Summary

Input:

- Event range.
- Existing memory records.
- Compression target.

Output schema:

- `summary`.
- `salient_entities`.
- `open_threads`.
- `superseded_event_ids`.

## Validation Rules

- Parse LLM output as structured JSON when possible.
- Validate using Pydantic models before using any field.
- Reject responses with missing required fields, invalid enum values, impossible IDs, or excessive length.
- Treat freeform text fields as display text only.
- Do not execute instructions embedded in model output.

## Error Handling

If an LLM call fails:

- Return a controlled application error or fallback response.
- Do not mutate `GameState`.
- Record a system event only if the failure is relevant to gameplay or debugging.

If validation fails:

- Keep the original player event.
- Do not apply deltas based on invalid output.
- Optionally retry once with a stricter repair prompt.
- Log only sanitized validation diagnostics.

If provider credentials are missing:

- Fail startup or the specific LLM operation with a clear local error.
- Do not print environment variable values.

