# v1.6 Visibility / Gameplay / Mod Audit

Verification Date: 2026-05-20

Scope:

- v1.6 gameplay module runtime and package surfaces.
- Declarative Action Mod, Action DSL, Action Mod Validation, ActionRegistry,
  module loader, module debugger, quality gate, regression playtests, import /
  export.
- Domain modules: Magic, Hacking, Crafting, Investigation / Deduction,
  Survival, Stealth, Combat, Social Manipulation, Faction Mission, Domain /
  Base Management.
- Player visible-state filtering and debug API separation.

Commands / Evidence:

- `rg "hidden|visible_state|player_visible|visible_facts|hidden_facts|narrator_hints|debug|dry-run|dry_run|module" backend\app\engine backend\app\session_store.py backend\app\main.py ...`
- Reviewed `backend/app/session_store.py`
- Reviewed `backend/app/engine/actions/declarative.py`
- Reviewed `backend/app/engine/actions/dsl.py`
- Reviewed v1.6 module tests, especially hidden leak tests for magic, hacking,
  investigation, stealth, combat, social manipulation, and v1.6 integration.

## Passed Items

1. Hidden facts are filtered from normal player visible state when they are not
   present in `player_visible_facts`.
   - `build_visible_state` only serializes facts from
     `state.player_visible_facts`.
   - Hidden NPCs and hidden objects are filtered unless discovered by player.

2. Hidden action targets are filtered by the visibility layer in major runtime
   paths.
   - Declarative actions validate object/NPC targets against
     `get_visible_facts`.
   - ActionRegistry suggested actions filter visible affordances for NPC/object
     target types.

3. Hidden magic effects are not player-visible by default.
   - Magic tests assert hidden effect IDs go to `hidden_facts`, not
     `visible_facts`, and do not appear in visible state.
   - Public illegal spell witnesses exclude hidden NPC witnesses.

4. Hidden hacking logs do not leak through player-visible facts.
   - Hacking `access_logs` reveals discoverable/public linked facts and keeps
     hidden linked facts in `hidden_facts`.

5. Hidden investigation truth does not leak on evidence examination.
   - Investigation tests assert `truth_fact` does not enter
     `player_visible_facts` and truth text is absent from visible state.

6. Hidden witnesses do not leak through combat or magic witness handling.
   - Combat visible summary filters hidden combatants.
   - Magic crime witness records exclude hidden NPCs.

7. Hidden NPCs are guarded in module action paths.
   - Social manipulation target lookup rejects hidden, undiscovered NPCs.
   - Stealth hidden observer returns a redacted summary and omits observer id.

8. Module debug data is gated by debug API.
   - `/debug/modules`, `/debug/modules/{module_id}`, and module dry-run routes
     call `require_debug_api()`.
   - Disabled debug API returns 403 in tests.

9. Module dry-run is debug-only and does not modify state.
   - `ModuleActionDryRunResponse` reports `dry_run=True` and
     `state_unchanged=True`.
   - v1.6 integration tests assert debugger dry-run does not mutate state.

10. Module quality reports are normal-safe by design.
    - Gameplay module quality report tracks `normal_report_redacted=True`.
    - `main.py` strips debug-only quality payload keys from normal quality API
      responses.

11. Narrator does not receive module debugger dry-run output through player
    APIs.
    - Module debugger APIs are separate debug routes.
    - `build_visible_state` has no module debug/dry-run fields.

## Possible Leak Paths

1. Action DSL `ADD_FACT_DISCOVERY` can compile a delta that adds any `fact_id`
   to `player_visible_facts`.
   - `compile_effect(ActionEffectType.ADD_FACT_DISCOVERY)` currently returns:
     `StateDelta(operation=ADD, path="player_visible_facts", value=effect.fact_id, ...)`
     without checking `FactVisibility`.
   - This means a declarative module using the lower-level DSL directly could
     add a hidden fact to player-visible facts unless a higher-level validator
     or rule wrapper blocks it.

2. Declarative Action `visible_facts` can name facts/ids without an explicit
   hidden-fact lookup at runtime.
   - If an Action Mod author places a hidden fact id in `visible_facts`, the
     action result can expose the id in `visible_facts`.
   - Current tests verify hidden text does not leak in normal scenarios, but
     the runtime itself does not cross-check every `visible_facts` id against
     `state.facts`.

3. `DeclarativeNarratorHints` includes `hidden_summary`.
   - The field exists in schema. The reviewed runtime does not feed it to
     narrator/player APIs, but package authors could place hidden text there.
   - The current audit did not find a player API path that returns it, but
     validators should continue treating it as debug/authoring-only.

4. Debug dry-run includes state delta previews.
   - This is debug-gated and redacted for hidden facts, but any future normal UI
     reuse of dry-run payload would be risky.

## High-Risk Leaks

### HR-1: Action DSL fact discovery can reveal hidden facts if used directly

Status: Potential high-risk leak path.

Evidence:

- `backend/app/engine/actions/dsl.py`
  `compile_effect(... ADD_FACT_DISCOVERY ...)` creates a
  `player_visible_facts` delta for `effect.fact_id` without checking whether
  the target fact is hidden, discoverable, public, or rule-authorized.
- Existing `test_action_dsl.py` demonstrates the primitive can add a hidden
  fact id to `player_visible_facts`.

Impact:

- A module action or future rule wrapper that uses `ADD_FACT_DISCOVERY` with a
  hidden fact id could make that hidden fact player-visible.
- Once in `player_visible_facts`, `build_visible_state` will serialize the
  full fact text.

Blocking Assessment:

- This should be treated as blocking for v1.6 acceptance unless the current
  release scope explicitly restricts `ADD_FACT_DISCOVERY` to trusted rule code
  only and documents that hidden-fact discovery must be checked by callers.
  Safer fix: make `compile_effect` refuse hidden facts unless an explicit
  rule-authorized flag/scope is present, and add validator coverage.

## Medium-Risk Leaks

### MR-1: Declarative `visible_facts` has no runtime hidden-fact validation

Status: Medium risk.

Impact:

- Action results may include hidden fact ids in `visible_facts` if a module
  definition is malformed or validator coverage is bypassed.
- This is less severe than HR-1 because `visible_facts` in `ActionResult` is
  not automatically the same as `player_visible_facts`, but narrator/player UI
  integrations must not treat it as authoritative without filtering.

Recommendation:

- Validate `visible_facts` against `state.facts` at runtime or require Action
  Mod Validation to reject hidden facts in `visible_facts`.

### MR-2: `narrator_hints.hidden_summary` requires strict segregation

Status: Medium watch item.

Impact:

- The field is not currently found in player API output, but it is a schema
  place where hidden text can be stored.

Recommendation:

- Add validator checks that `narrator_hints.safe_summary` cannot contain hidden
  fact text and that `hidden_summary` is never included in normal reports,
  exports, or narrator prompts.

## Minor Issues

- Grep-based reviews are noisy because v1.6 tests intentionally assert hidden
  text is absent. A scripted visibility audit would reduce false positives.
- Debug and authoring route names are clear, but future frontend work should
  avoid reusing debug dry-run response components in normal/player surfaces.
- Some domain modules use generic `visible_facts` tokens such as
  `stealth:hidden`, `noise:created`, or action ids. These are safe labels, but
  the distinction between safe labels and fact ids should stay documented.

## Fix Recommendations

1. Block or guard `ActionEffectType.ADD_FACT_DISCOVERY` for hidden facts.
   - Recommended behavior: only allow adding public/discoverable facts by
     default.
   - Require an explicit trusted rule context for hidden fact reveal.
   - Add tests proving hidden fact IDs cannot be added to
     `player_visible_facts` through generic DSL effects.

2. Extend Action Mod Validation:
   - Reject hidden fact ids in `visible_facts`.
   - Reject hidden fact text in `narrator_hints.safe_summary`.
   - Ensure `narrator_hints.hidden_summary` is export/debug-only and not
     surfaced in normal reports.

3. Keep module debugger output debug-only.
   - Do not pass `state_delta_preview`, `checks_result`, or `event_preview` to
     narrator/player UI.

4. Keep player APIs based on `build_visible_state`.
   - Do not serialize raw `ActionResult.hidden_facts`, raw `Event`, or module
     debug summaries into player-visible responses.

5. Add a release-blocker regression:
   - A declarative/DSL action attempts to reveal a hidden fact.
   - Expected result: validation or runtime blocks it; hidden text remains
     absent from visible state and narrator context.

## Blocking Status

Potentially blocking v1.6.

Most v1.6 visibility boundaries pass, and existing domain-module tests show
good coverage for hidden magic, hacking logs, investigation truth, hidden
witnesses, hidden NPCs, module debug data, and safe player visible-state
filtering. However, the Action DSL `ADD_FACT_DISCOVERY` primitive currently has
a direct path to `player_visible_facts` without hidden fact visibility checks.
Because v1.6 explicitly allows declarative modules and DSL effects, this should
be fixed or formally scoped to trusted-only rule code before acceptance.
