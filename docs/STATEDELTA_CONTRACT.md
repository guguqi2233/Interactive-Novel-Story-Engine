# StateDelta Contract

Current StateDelta contract version: `1.8`.

Stable operations are `set`, `inc`, `add`, and `remove`. Deltas are data only:
they cannot execute Python, use arbitrary expressions, read files, call LLMs,
or mutate hidden data into player-visible data without rule authorization.

Stable contract validation rejects forbidden paths and unsupported operations.
The runtime `apply_delta` semantics remain compatible with existing saves and
tests.
