# Content Pack Schema Contract

Current content pack schema contract version: `1.8`.

World content files remain local YAML: `manifest.yaml`, `locations.yaml`,
`npcs.yaml`, `items.yaml`, `quests.yaml`, `facts.yaml`, `factions.yaml`,
`rumors.yaml`, and `relationships.yaml`.

Legacy content packs without schema metadata are loaded through compatibility
paths and validation warnings where possible. Deprecated fields require
metadata and migration notes. Content migrations must not expose hidden/debug
data to players and must not modify active GameState directly.
