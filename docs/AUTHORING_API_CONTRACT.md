# Authoring API Contract

Current Authoring API contract version: `1.8`.

Authoring APIs are controlled by `ENABLE_AUTHORING_API`. Preview and validate
must not write disk. Save/apply operations must pass validation gates and must
not modify active runtime GameState.
