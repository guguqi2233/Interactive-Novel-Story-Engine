# v2.2 Visibility and Novel Context Audit

## Passed

- World Bible hidden entries are excluded from `NovelWorldBibleContext`.
- Lore/fact hidden entries are excluded from Novel safe context.
- Character private notes are omitted from safe summaries.
- Timeline hidden/authoring-only events are excluded from Novel timeline
  summaries.
- Novel export omits authoring notes, hidden refs, raw state deltas, debug
  memory, API keys, and provider profile data.
- EventLog-to-Novel import includes only player-visible/narrator-safe summaries
  and counts hidden exclusions without printing hidden details.

## Possible Leak Paths

- Authoring/debug mode can include authoring notes by explicit request. These
  must remain outside normal editor/export views.

## High Risk Leaks

None found.

## Blocking Status

Not blocking v2.2.
