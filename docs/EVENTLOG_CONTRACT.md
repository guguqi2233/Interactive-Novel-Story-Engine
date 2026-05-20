# EventLog Contract

Current EventLog contract version: `1.8`.

Events must include `event_id`, `turn`, `event_type`, `actor_id`,
`action_type`, result, visibility flag, state deltas, creation time, and
contract version. Empty-delta events must be explicitly marked.

Committed events are append-only history for replay, debugging, save recovery,
and timelines. Player-visible event fields must not contain API keys, raw env,
or debug-only hidden details.
