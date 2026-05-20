# Module Manifest Contract

Current gameplay module manifest contract version: `1.8`.

Gameplay modules must declare id, name, version, module type, contract version,
engine/schema compatibility, dependencies, conflicts, provided actions/rules,
state schema extensions, event types, permissions, save compatibility, and
quality tests.

Dangerous permissions such as execute code, network, filesystem, LLM calls, and
direct GameState modification remain rejected.
