# Debug API Contract

Current Debug API contract version: `1.8`.

Debug APIs are controlled by `ENABLE_DEBUG_API`. Debug responses must not enter
player APIs, and ordinary debug output must redact API keys, raw env, hidden
text, raw prompts, and sensitive local paths.
