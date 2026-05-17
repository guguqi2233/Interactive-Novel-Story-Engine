# Combat System Design

## v0.4 Implementation Status

v0.4 implements the first lightweight combat core:

- player actions: `attack`, `defend`, `flee`
- rule-owned hit/miss/damage resolution
- actor life fields for player and NPCs, including HP, stamina, alive state, condition, status effects, and hostile targets
- `CombatState`, `CombatantState`, `AttackResult`, and `DamageResult` schemas
- damage and condition changes through `StateDelta`
- public assault/murder handoff to crime and witness rules
- save/load persistence for combat and life state

This document remains the design reference. Sections marked as future or recommended are not necessarily fully implemented. v0.4 still does not include tactical combat, equipment progression, armor, detailed weapon stats, or autonomous multi-round NPC combat planning.

## Goal

The combat system should support lightweight narrative RPG conflict for an interactive novel world. It is not a tactics game. Combat exists to produce structured consequences: injury, fear, hostility, crime, faction reputation changes, rumors, quest triggers, and visible narrative outcomes.

The rule engine decides combat outcomes. The LLM only renders already-resolved combat results into prose.

Core constraints:

- Combat hit/miss/damage/death are deterministic rule results, not LLM decisions.
- All HP, stamina, status, hostility, location, crime, reputation, and rumor changes use `StateDelta`.
- All combat actions and combat system consequences record `Event`.
- Combat-generated crimes, witnesses, rumors, and faction changes route through existing rule modules.
- Hidden NPCs, hidden observers, hidden witnesses, and hidden facts must not leak through `visible_state` or Narrator prompts.

## Non-Goals For v0.4

v0.4 combat should not implement:

- Tactical grid movement.
- Real-time combat.
- Detailed weapon reach, armor layers, hit locations, or damage types beyond minimal tags.
- Complex AI planning.
- Party combat.
- Full chase system.
- Guard pursuit or arrest AI.
- Trial/legal resolution.
- Loot tables.
- Skill progression.
- Equipment durability.
- LLM-authored combat outcomes.

## CombatantState

`CombatantState` is the per-actor combat-facing state. It may be embedded in `PlayerState` / `NPCState` later, or represented as a standalone map keyed by actor id.

Recommended schema:

```python
class CombatantState(BaseModel):
    actor_id: str
    hp: int = 10
    max_hp: int = 10
    stamina: int = 10
    max_stamina: int = 10
    attack: int = 1
    defense: int = 1
    initiative: int = 0
    condition: str = "healthy"  # healthy | injured | incapacitated | dead
    status_effects: list[str] = Field(default_factory=list)
    hostile_to: list[str] = Field(default_factory=list)
    fleeing: bool = False
```

For v0.4, this can be simplified by adding minimal fields directly to `PlayerState` and `NPCState`:

- `hp`
- `max_hp`
- `stamina`
- `max_stamina`
- `condition`
- `status_effects`
- `hostile_to`

The standalone `CombatantState` becomes useful when multiple combat encounters can exist independently.

## CombatState

`CombatState` tracks an active local conflict.

Recommended schema:

```python
class CombatStatus(StrEnum):
    ACTIVE = "active"
    ENDED = "ended"

class CombatState(BaseModel):
    id: str
    location_id: str
    status: CombatStatus = CombatStatus.ACTIVE
    combatant_ids: list[str] = Field(default_factory=list)
    current_actor_id: str | None = None
    round_index: int = 1
    turn_order: list[str] = Field(default_factory=list)
    started_turn: int
    ended_turn: int | None = None
    tags: list[str] = Field(default_factory=list)
```

For v0.4 minimal implementation, combat may be resolved as one action at a time without persistent `CombatState`. If persistent hostility is needed, use actor fields such as `npcs.{npc_id}.hostile_to`.

## HP, Stamina, And Status Effects

HP:

- Represents ability to remain conscious and functional.
- At `hp <= 0`, actor becomes `incapacitated` by default.
- Death should require explicit severe outcome or `hp <= -max_hp`.

Stamina:

- Spent on attack, defend, flee.
- Low stamina reduces attack/defense score.
- v0.4 may use a simple fixed cost:
  - attack: 2 stamina
  - defend: 1 stamina
  - flee: 2 stamina

Status effects:

- `guarded`
- `off_balance`
- `bleeding`
- `stunned`
- `fleeing`
- `incapacitated`
- `dead`

Status effects are strings in v0.4. v0.5 can promote them to structured objects.

## Combat Actions

### attack

Boundary:

- Requires visible/reachable target.
- Target must be in same location unless a future ranged rule exists.
- Cannot target hidden undiscovered NPCs.
- Cannot be performed by incapacitated/dead actor.

Rule output:

- `success`: hit and damage applied.
- `partial_success`: glancing hit, stamina cost, or target becomes `off_balance`.
- `failure`: miss, stamina cost, possible attacker `off_balance`.
- `invalid`: missing/invisible/unreachable target.

The attack action can produce crime consequences through `crime.classify_crime`.

### defend

Boundary:

- Applies to actor only.
- Sets or refreshes `guarded`.
- Consumes stamina/time.

Rule output:

- Adds `guarded` status effect.
- May reduce incoming damage until next actor action or next turn.

### flee

Boundary:

- Requires an exit from current location.
- May fail if blocked by hostile NPCs.
- Hidden NPCs can affect difficulty but must not be identified in player-facing output.

Rule output:

- `success`: player location changes through `StateDelta`.
- `partial_success`: player moves but gains `injured`, loses stamina, or leaves evidence.
- `failure`: remains in combat, may become `off_balance`.

### use_item in combat

Boundary:

- Must use existing inventory rules.
- Item must be owned by player or reachable.
- Item effects are rule-defined, not prose-defined.

Allowed v0.4 examples:

- use healing item
- use smoke item to improve flee
- use improvised weapon

Not allowed:

- LLM inventing item effect.
- Item creating new hidden facts unless rule module creates them through `StateDelta`.

## Initiative And Turn Order

v0.4 can avoid full initiative if combat remains one action per player input.

Recommended minimum:

- Player action resolves first.
- Hostile NPC reactions are processed by world/social tick.
- If `CombatState` is active, `turn_order` can be deterministic:
  - player first
  - visible hostile NPCs by id
  - hidden hostile NPCs by id but never exposed to player unless discovered

v0.4 should not implement full round-robin combat unless needed for tests.

## NPC Hostility States

NPCs need a small reaction model:

- `neutral`
- `wary`
- `hostile`
- `fleeing`
- `incapacitated`
- `dead`

Initial implementation can use:

- `npcs.{npc_id}.mood`
- `npcs.{npc_id}.relationship_to_player`
- `npcs.{npc_id}.suspicion`
- `npcs.{npc_id}.goals`
- future `npcs.{npc_id}.hostile_to`
- future `npcs.{npc_id}.condition`

Hostility must be based on known facts, observed crimes, reputation, or direct attack state. NPCs cannot react to unknown crimes or hidden facts they do not know.

## Injury, Incapacitation, And Death

Recommended rules:

- `hp > 50% max_hp`: `healthy`
- `0 < hp <= 50% max_hp`: `injured`
- `hp <= 0`: `incapacitated`
- `hp <= -max_hp` or explicit lethal attack: `dead`

Death is canonical state and must never be narrative-only.

Injury deltas:

- `player.hp`
- `player.condition`
- `player.status_effects`
- `npcs.{npc_id}.hp`
- `npcs.{npc_id}.condition`
- `npcs.{npc_id}.status_effects`

Death side effects:

- Potential `murder` crime.
- Potential rumor.
- Potential faction reputation loss.
- Potential quest trigger.

## Relationship With Crime System

Combat can create crime records:

- attack visible NPC: `assault`
- incapacitate NPC in public: `assault` or elevated severity
- kill NPC: `murder`
- vandalize object during combat: `vandalism`

Combat actions should produce normal player `Event` entries such as `attack`. Existing `crime.classify_crime(event, state)` should classify them.

Witness handling:

- Use `detect_witnesses(event, state)`.
- Hidden witnesses may observe but must not be named in `visible_state` or Narrator.
- If player attacked while successfully sneaking, combat should set metadata similar to `sneak_result=success` only when appropriate.

## Relationship With Faction Reputation

Faction impact comes through social consequence rules, not direct combat prose.

Examples:

- Attacking a faction member lowers that faction's reputation.
- Killing a faction member lowers reputation more severely.
- Defending a faction member may increase reputation if observed or reported.

Reputation deltas:

- `factions.{faction_id}.reputation.value`
- `factions.{faction_id}.reputation.recent_reasons`

Do not let Narrator choose reputation changes.

## Relationship With Rumor Propagation

Combat can create rumors when:

- public combat occurs
- an NPC witnesses assault or murder
- combat happens in a public location
- a faction receives a report

Rumor text must be player-safe:

- If the rumor references a hidden fact, use `text_for_player`.
- If no safe text exists, use vague fallback text.
- Do not expose hidden witness identity or hidden NPC identity.

Rumor deltas:

- `rumors.{rumor_id}`
- `rumors.{rumor_id}.known_by_npcs`
- `rumors.{rumor_id}.known_by_factions`
- `rumors.{rumor_id}.known_by_player`
- `rumors.{rumor_id}.spread_level`

## Relationship With Visible State

Potential additive `visible_state` fields:

- `player_condition`
- `player_hp`
- `player_stamina`
- `visible_npcs[].condition_band`
- `visible_npcs[].hostility`
- `active_combat`

Visibility rules:

- Exact player HP can be visible to the player.
- NPC exact HP should not be shown unless intentionally exposed.
- Use bands for NPCs:
  - `healthy`
  - `hurt`
  - `down`
  - `dead`
- Hidden NPCs must not appear in `visible_npcs`.
- Hidden combat causes must not appear in visible summaries.

## Narrator Boundary

Narrator receives:

- player input
- `ActionResult.success_level`
- player-safe `ActionResult.reason`
- `ActionResult.visible_facts`
- filtered `visible_state`

Narrator must not receive:

- raw combat internals
- hidden observer ids
- hidden NPC identity
- exact hidden NPC HP
- raw debug timeline
- `ActionResult.hidden_facts`
- crime witness records unless player-visible

Combat prose can dramatize only already-resolved outcomes.

## StateDelta Paths

Recommended v0.4 paths:

- `player.hp`
- `player.stamina`
- `player.condition`
- `player.status_effects`
- `npcs.{npc_id}.hp`
- `npcs.{npc_id}.stamina`
- `npcs.{npc_id}.condition`
- `npcs.{npc_id}.status_effects`
- `npcs.{npc_id}.hostile_to`
- `npcs.{npc_id}.mood`
- `npcs.{npc_id}.suspicion`
- `combats.{combat_id}`
- `combats.{combat_id}.status`
- `combats.{combat_id}.combatant_ids`
- `combats.{combat_id}.current_actor_id`
- `crimes.{crime_id}`
- `witnesses.{witness_id}`
- `rumors.{rumor_id}`
- `factions.{faction_id}.reputation.value`
- `social_flags.{consequence_id}`

All new paths must be covered by unit tests.

## Event Types

Recommended `Event.action_type` values:

- `attack`
- `defend`
- `flee`
- `combat_use_item`
- `combat_started`
- `combat_damage`
- `combat_missed`
- `combat_status_changed`
- `actor_incapacitated`
- `actor_died`
- `combat_ended`
- `crime_consequence`
- `rumor_spread`
- `faction_reputation_changed`

Player action events should be visible to player. System consequence events may be hidden unless they produce player-visible changes.

## Save, Load, And Replay

Requirements:

- Combat state must be JSON-serializable.
- Event replay must reproduce HP/status/condition/combat state by applying `state_deltas`.
- Save/load must preserve:
  - active combat
  - actor HP/stamina
  - conditions/status effects
  - hostility
  - crimes/witnesses from combat
  - rumors from combat
  - faction reputation changes
- Loading mid-combat must allow the next player input to continue without turn drift.

No combat state may live only in memory outside `GameState`.

## Test Plan

Unit tests:

- attack visible NPC applies damage through `StateDelta`
- attack missing target returns invalid
- attack hidden undiscovered NPC returns invalid
- defend adds guarded status
- flee success moves player through `StateDelta`
- flee failure does not move player
- hp below threshold changes condition
- hp <= 0 incapacitates actor
- lethal damage marks actor dead
- incapacitated/dead actor cannot attack

Integration tests:

- attack generates player Event
- attack can generate assault crime
- witnessed attack creates witness record
- reported assault lowers faction reputation
- public combat creates rumor
- hidden witness does not enter `visible_state`
- Narrator does not receive hidden witness id
- save/load preserves combat state
- replay reaches same final state

Regression tests:

- `python -m pytest`
- frontend build if `visible_state` shape changes

## v0.4 Minimum Implementation Scope

The smallest useful v0.4 combat release:

1. Add actor HP/stamina/condition/status fields.
2. Add `attack` action handler.
3. Add `defend` action handler if needed by tests.
4. Add simple `flee` action or reuse `move/sneak` with combat constraints.
5. Add combat rule module:
   - `can_attack`
   - `resolve_attack`
   - `calculate_damage`
   - `apply_damage`
   - `evaluate_condition`
6. Integrate attack events with crime classification.
7. Expose player HP/condition and NPC condition band in `visible_state`.
8. Add save/load and replay tests.

This scope is enough for conflict consequences without building a full combat game.

## v0.5 Extension Direction

Potential v0.5 combat expansions:

- structured weapons and armor
- damage types
- stamina recovery
- multiple combat rounds
- NPC combat reactions in world tick
- flee/chase integration
- non-lethal takedowns
- intimidation and surrender
- combat-specific quest triggers
- equipment durability
- healing and recovery over time
- richer combat debug timeline
- optional tactical layer if the project ever needs it
