# Provider Gateway Contract

Current Provider Gateway contract version: `1.8`.

All model calls must go through LLMProvider and ProviderRouter/factory paths.
Provider capability summaries are declared local metadata and must not include
API keys, raw env, or secret URLs.

Provider routing cannot change GameState authority or bypass schema validation.
