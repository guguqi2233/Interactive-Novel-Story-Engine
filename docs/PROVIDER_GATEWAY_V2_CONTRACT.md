# Provider Gateway v2 Contract

Provider Gateway v2 keeps all model access behind LLMProvider / ProviderRouter.
It stabilizes provider capabilities, safe summaries, and errors.

## Rules

- Business modules cannot instantiate concrete providers directly.
- Safe summaries never include API keys, raw env, database passwords, or raw
  prompts.
- Structured JSON use cases must verify provider capability or use fallback.
- Real provider tests are disabled by default.
- Provider output never directly modifies GameState.

