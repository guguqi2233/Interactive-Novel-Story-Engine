# Sample Basic Action Mod

`sample_basic_action_mod` is a minimal local-only declarative Action Mod sample
for checklist, documentation, and local demo use.

It is intentionally conservative:

- no arbitrary code;
- no executable plugin files;
- no API keys or provider secrets;
- no `.env`, database, log, cache, or build output files;
- not enabled by default;
- no remote download or online marketplace behavior;
- no direct active `GameState` mutation.

The sample action proposes a `StateDelta`; the local engine remains responsible
for validation and application through the normal ActionRegistry / StateDelta /
EventLog path.
