# GameState Contract

Current GameState contract version: `1.8`.

Stable fields include player, locations, objects/items, NPCs, facts, quests,
factions, rumors, crimes/witnesses, relationships, memory references, and
module state extensions. Runtime code must continue to change state through
StateDelta only.

Serialization must remain deterministic for set-like fields such as
`player_visible_facts` and `npc_knowledge`. Legacy payload loading may fill
missing defaults, but must not change hidden facts into player-visible facts.
