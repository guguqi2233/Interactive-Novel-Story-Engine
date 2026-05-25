# v3.7 Real LLM Manual Smoke Test

This document describes the manual-only smoke test for using a real LLM
provider in v3.7 Local Playable Complete Product CN.

The smoke test is intentionally not part of CI or automated tests. It may send
prompts to the user-configured provider and may create provider-side costs.

## Scope

Use this guide only when a local user explicitly wants to verify a real
provider from the UI. Automated tests, release checks, and CI must continue to
use `mock`, `local_stub`, fake clients, or local deterministic fixtures.

Supported provider profile types for local configuration:

- `openai`
- `openai_compatible`
- `relay`
- `local_http`
- `custom`
- `mock`
- `local_stub`

`relay` means a generic OpenAI-compatible/custom base URL configuration. It is
not a specific relay vendor integration and not an API resale service.

## Safety Rules

- Do not put a real API key in project files.
- Do not put a real API key in frontend storage, logs, diagnostics, backups,
  exports, docs, tests, fixtures, package manifests, prompt profiles, or mods.
- Real provider calls occur only after an explicit user action such as **Test
  Connection**, **Fetch Models**, or a user-triggered generation action.
- CI and automated tests must not call real providers.
- The World Engine remains the source of truth. The LLM can parse, draft,
  summarize, roleplay, or narrate, but it is not the world judge.
- Hidden facts, NPC secrets, debug memory, mature/private content, raw prompts,
  raw outputs, and raw `state_deltas` remain filtered according to the project
  visibility and export policies.

## 1. Configure A Real Provider

Open the local app and go to:

1. **首页**
2. **配置模型** or **模型服务**
3. **Provider 设置向导**

Choose a provider type:

- **OpenAI** for the built-in OpenAI-compatible runtime path.
- **OpenAI-compatible** for compatible chat-completions APIs.
- **中转站 / Relay** for a generic compatible base URL. This is only local
  configuration metadata, not API resale.
- **本地模型服务 / local_http** for a locally running OpenAI-compatible server.
- **自定义 API** only when the backend provider adapter supports it.
- **Mock / 测试** for safe local testing without network calls.

Set a safe display name, base URL when needed, timeout, and model metadata. Do
not paste a real key into project files.

## 2. Choose A Secret Source

Use one of these secret modes:

### `api_key_env`

Store the key in the local backend process environment and save only the
environment variable name in the provider profile.

PowerShell example:

```powershell
$env:OPENAI_API_KEY = "<your-real-key>"
```

Provider profile field:

```text
api_key_env = OPENAI_API_KEY
```

The profile stores only `OPENAI_API_KEY`, not the key value.

### `secret_ref`

Use a backend secret resolver reference. The project stores only the reference
name. The resolved secret value must remain outside the project and must be
excluded from logs, diagnostics, backups, and exports.

Example reference value:

```text
secret_ref = providers/main
```

### `local_secret_ref`

Use a local secret reference outside the project directory if your local setup
supports it. The reference must not point inside the project, and the secret
store must be excluded from backups, exports, diagnostics, and git.

Example reference value:

```text
local_secret_ref = providers/main
```

### `transient_api_key`

Use only for a one-time manual test. It must not be persisted and must not enter
frontend storage, logs, diagnostics, backups, exports, or project files.

## 3. Test Connection

From the Provider UI, click **Test Connection** manually.

Expected safe outcomes:

- `connected`
- `missing_secret`
- `auth_failed`
- `invalid_base_url`
- `timeout`
- `model_list_failed`

Errors must be redacted. The UI must not show API keys, Authorization headers,
raw provider responses, raw env, or sensitive local paths.

## 4. Fetch Models

Click **Fetch Models** manually after the provider is configured.

Some providers do not support model-list APIs. That is not a failure of the
product. If model discovery is unsupported, manually add the required
`model_id`.

Model discovery may store safe metadata only:

- model id
- display name
- capability flags
- recommended use cases
- enabled/disabled status

It must not store credentials or raw provider responses.

## 5. Assign Models

Assign safe `ModelProfile` entries to use cases:

- 小说草稿
- 小说改写
- Tavern 回复
- 多 NPC 场景
- 世界输入解析
- 世界叙事渲染
- Cross-Mode 草稿
- 记忆摘要
- 质量检查
- 低成本摘要

World input parsing should use a JSON/structured-output capable model. If a
model does not advertise JSON capability, keep the warning visible or choose a
different model for structured use cases.

## 6. Use Real LLM In Product Workflows

After connection and assignment are ready:

- **Novel**: use the assigned model for draft, rewrite, and summary actions.
- **Tavern**: use the assigned model for single-character RP and multi-NPC
  scene replies.
- **World**: use assigned models for intent parsing and narration only.

World results are still decided by local rules, validated actions,
`StateDelta`, and `EventLog`. The provider can change wording, latency, or
formatting, but it cannot decide world facts.

## 7. Return To Mock / Local Stub

To close the real-provider smoke test:

1. Switch the provider profile back to `mock` or `local_stub`.
2. Reassign Novel / Tavern / World / Cross-Mode / Quality use cases to the
   mock/local-stub model.
3. Remove temporary real-provider environment variables from the shell if they
   are no longer needed.
4. Restart the local backend if the process environment changed.

PowerShell example:

```powershell
$env:LLM_PROVIDER = "mock"
$env:OPENAI_API_KEY = ""
```

Do not commit any shell profile, `.env`, local secret store, diagnostic bundle,
backup, or export that contains a real key.

## Manual Smoke Checklist

- Provider profile exists and stores no plaintext key.
- Secret source is `api_key_env`, `secret_ref`, `local_secret_ref`, or
  one-time `transient_api_key`.
- Manual **Test Connection** returns a redacted safe status.
- Manual **Fetch Models** succeeds or an explicit manual `model_id` is added.
- Model assignment covers Novel, Tavern, World, Cross-Mode, and Quality.
- Novel generation works through Provider Gateway.
- Tavern reply works through Provider Gateway.
- World input parsing and narration work through Provider Gateway.
- No API key appears in project files, frontend storage, logs, diagnostics,
  backups, exports, docs, tests, fixtures, or packages.
- CI and automated tests remain on fake/local_stub provider paths.

## What This Is Not

- Not CI coverage for real providers.
- Not a free-provider guarantee.
- Not an API resale service.
- Not a cloud sync or account feature.
- Not a promise that every provider supports model-list APIs.
- Not a change to World Engine authority or visibility boundaries.
