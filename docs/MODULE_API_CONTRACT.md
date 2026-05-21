# Module API Contract v2

The v2 Module API stabilizes gameplay module lifecycle and discovery while
preserving the v1.6/v1.8 gameplay module boundary.

## Lifecycle

`discovered`, `validated`, `compatible`, `enabled`, `disabled`, `blocked`,
`deprecated`.

## Capabilities

Modules may declare actions, state schema extensions, event types, save
compatibility, quality tests, dependencies, and conflicts. They may not execute
arbitrary code or directly modify GameState.

## Runtime Boundary

Module actions must go through ActionRegistry and return ActionResult,
StateDelta, and EventLog entries. Module debug data is debug-only and never
enters player APIs.

