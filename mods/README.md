# Local Mod Samples

This directory contains local-only sample packages for manual checklist,
documentation, and demo workflows.

Safety rules for samples:

- no arbitrary code;
- no Python, JavaScript, shell, binary, or executable plugin payloads;
- no API keys, provider secrets, `.env`, databases, logs, caches, or build
  outputs;
- not enabled by default;
- no remote download, online marketplace, account, or cloud-sync behavior;
- no direct active `GameState` mutation.

Samples are declarative package data. Runtime world changes, if a sample action
is installed by an explicit local workflow, must still go through
`ActionRegistry`, `StateDelta`, and `EventLog`.
