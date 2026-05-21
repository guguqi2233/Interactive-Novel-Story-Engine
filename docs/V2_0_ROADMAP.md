# v2.0 Roadmap: Modular Narrative RPG Platform

v2.0 turns the local AI Narrative Studio into a modular narrative RPG platform.
It builds on v1.8 stable contracts and v1.9 release hardening, while keeping the
same local-first safety model.

## Goals

- Stable Plugin API for manifest-only local extension bundles.
- Stable Module API for gameplay modules and declarative action mods.
- Content Pack Schema v2 with v1 compatibility shims.
- Save Migration Contract v2 with backup-before-apply recovery.
- Authoring Extension API for declarative editor panels and schemas.
- Provider Gateway v2 with safe summaries and stable error shape.
- Local Module Browser and Local Script Package Browser.
- Multi-campaign management, timeline branches, character transfer, and long
  campaign summaries.
- Workspace project manifests and v2 package import/export.
- v2 compatibility tests and release checklist automation.

## Explicit Non-Goals

- No LLM world judge.
- No online marketplace.
- No cloud sync, accounts, or multi-user collaboration.
- No arbitrary-code plugin execution by default.
- No large-scale war simulation, complete tactical combat, or MMO economy.
- No breakage of v1.x saves, content packs, modules, prompts, providers, or
  package contracts without compatibility checks or migration.

## Implementation Order

1. Platform boundary and v2 roadmap.
2. Plugin, Module, Package v2, Content Pack v2, Save Migration v2, Provider v2,
   and Authoring Extension contracts.
3. Local module/package browsers and workspace project services.
4. Multi-campaign, character transfer, timeline branching, and long campaign
   management.
5. v2 compatibility tests, release checklist, audits, docs, acceptance report,
   and release notes.

## Final Acceptance Standard

v2.0 is acceptable only when tests and frontend build pass, v2 compatibility and
release checklists pass, audits report no high-risk blockers, and docs clearly
state local-only boundaries.

## Recommended v2.1 Direction

Polish the platform UI, deepen long-campaign ergonomics, add broader legacy
fixtures, and expand package/plugin ecosystem tooling without changing the
local-first trust boundary.

