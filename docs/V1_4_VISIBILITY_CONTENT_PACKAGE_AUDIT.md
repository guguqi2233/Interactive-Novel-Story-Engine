# v1.4 Visibility / Content Production / Package Audit

Verification Date: 2026-05-20

Scope:

- v1.4 Content Production Pipeline.
- Normal production reports, safe package exports, import/export profiles, batch tools, local content library, batch quality gate, coverage planner, and campaign/script package builders.
- Existing player visibility, narrator context, RP prompt context, and character/lorebook import boundaries.

Review Commands:

- `rg -n "hidden|secret|private_self_summary|normal_report|safe_export|redact|visible_state|player_visible|narrator|production" backend/app/engine/content backend/app/quality backend/app/api.py backend/app/llm backend/app/roleplay`
- Manual review of:
  - `backend/app/engine/content/batch_character_card_import.py`
  - `backend/app/engine/content/batch_lorebook_classification.py`
  - `backend/app/engine/content/character_pack_builder.py`
  - `backend/app/engine/content/import_export_profiles.py`
  - `backend/app/engine/content/mystery_templates.py`
  - `backend/app/engine/content/quest_pack_generator.py`
  - `backend/app/engine/content/script_package_builder.py`
  - `backend/app/engine/content/campaign_starter_kit.py`
  - `backend/app/engine/content/local_content_library.py`
  - `backend/app/engine/content/production_pipeline_dashboard.py`
  - `backend/app/quality/content_coverage_planner.py`
  - `backend/app/quality/batch_quality_gate.py`
  - `backend/app/llm/context_builder.py`
  - `backend/app/llm/narrator.py`

## Verdict

v1.4 passes the visibility, content production, and package safety audit.

No high-risk hidden-content leak was found in v1.4 production paths. The current implementation keeps generated production content in drafts/packages, redacts or removes hidden/private fields from normal reports and safe exports, and preserves the existing player/narrator/RP visibility boundary.

This audit does not block v1.4.

## Passed Items

1. Hidden facts do not enter normal production reports by default.
   - Batch lorebook classification redacts hidden entries in normal mode using `[redacted hidden lorebook entry]`.
   - Content coverage reports use counts such as `hidden_entities_redacted` rather than raw hidden text.
   - Batch Quality Gate and Production Pipeline Dashboard apply redaction before returning normal summaries.

2. Hidden facts do not enter player `visible_state`.
   - v1.4 production modules operate on drafts, package files, previews, or world-pack files.
   - Runtime player visibility remains controlled by existing `player_visible_facts` and visibility rules.
   - `WorldLoader.to_game_state()` marks hidden facts as secret and initializes player-visible facts separately.

3. Hidden NPC secrets do not enter safe package exports.
   - `CharacterPackBuilder.export_character_pack(... safe_export=True)` removes `knowledge` and `secrets`.
   - `NPCPackGenerator` safe export also removes `knowledge`, `secrets`, and `private_self_summary`.
   - Import/export profiles reinforce safe export behavior.

4. Hidden RP fields do not enter normal character packs.
   - Safe character pack export removes `rp_profile.private_self_summary`.
   - Tavern compatibility safe export also excludes `private_self_summary`.
   - RP dialogue prompt context uses expression-only fields and excludes `private_self_summary` and taboo topic text.

5. Batch Character Import marks unsafe prompts.
   - Batch character card import delegates to `CharacterCardImporter`.
   - Prompt-control fields such as `system_prompt` and unsafe instructions are reported in `unsafe_entries`.
   - Batch output remains draft-only and does not write active world or active `GameState`.

6. Batch Lorebook Classification isolates hidden and unsafe entries.
   - Hidden entries are separated into `hidden_fact_candidates`.
   - Prompt/control entries are separated into `unsafe_entries`.
   - Normal reports redact hidden entry summaries unless `authoring_debug` is explicitly enabled.
   - Apply-draft validates proposed `facts.yaml` but still does not write disk.

7. Mystery template `truth_fact` is hidden.
   - Built-in mystery templates mark the truth fact as hidden.
   - Mystery generated quest/rumor/item player-facing text does not include the raw hidden truth.
   - Scenario regression drafts include forbidden visible facts for hidden truth ids.

8. Quest Pack Generator avoids hidden facts in player-facing text.
   - Mystery-mode clues are generated as hidden/discoverable facts.
   - Public quest text uses generic clue language rather than raw hidden clue text.
   - Existing validator catches `public_quest_reveals_hidden_fact` and `rumor_reveals_hidden_fact`.

9. Content Coverage Plan does not expose hidden details in normal output.
   - Coverage planner reports categories, suggested tools, and safe refs.
   - Hidden content is summarized via counts and generic “hidden leak regression” suggestions.
   - `safe_refs` performs additional redaction for obvious hidden/secret/private identifiers.

10. Script Package manifest does not include hidden text full content in normal manifest.
    - `ScriptPackageBuildReport.normal_manifest` removes checksums and does not include file contents.
    - `script_package_payload.json` stores file paths and hidden flags, not hidden file text.
    - Package validation rejects API keys, `.env`, DB/log files, and executable files.

11. Campaign Starter Kit normal preview does not expose hidden truth.
    - Campaign starter mystery draft references structured hidden truth only in authoring draft objects.
    - Scenario suite uses forbidden hidden fact ids but not hidden truth prose.
    - Preview does not write disk or modify active `GameState`.

12. Import/export profiles handle hidden authoring data correctly.
    - Safe export excludes hidden facts and private RP fields.
    - Authoring redacted export can include hidden ids/markers but redacts hidden text.
    - Import profiles warn or reject unsafe hidden/API/executable/path traversal content.

13. Local Content Library normal view does not show hidden details.
    - Library items expose safe metadata, tags, quality summaries, and path labels rather than raw hidden fact text.
    - RP profile items mark private fields redacted.
    - Export path uses safe profiles for character packs.

14. Batch Quality Gate report redacts hidden details.
    - Batch Quality Gate redacts tokens such as `sk-`, `api_key`, `secret`, `hidden`, `private_self_summary`, `.env`, and known hidden ids.
    - Report declares `hidden_details_redacted=True`.
    - Package checks use `normal_report=True`.

15. Narrator cannot see production debug data through v1.4 paths.
    - Production modules do not feed reports into narrator prompts.
    - `Narrator.render()` receives only `visible_facts`, a safe `ActionResult` payload, current location, and tone.
    - `MemoryContextBuilder` filters narrator memory to narrator-safe memory and excludes hidden/unknown facts.

## Possible Leak Paths

1. Token-based redaction in Batch Quality Gate and CLI-style reports.
   - Current redaction catches common sensitive tokens and known hidden ids.
   - Risk remains for spoiler ids or hidden prose that do not contain obvious words such as `hidden`, `secret`, or known fixture ids.

2. Content Coverage Planner safe refs.
   - `safe_refs` redacts obvious hidden/secret/private ids.
   - If upstream coverage metrics include a non-obvious hidden id, it may appear as an id, not full text.
   - This is lower risk than text leakage but could still reveal an internal identifier.

3. Authoring/debug modes.
   - `BatchLorebookClassificationRequest.authoring_debug=True` can expose hidden entry summaries.
   - This is explicit authoring/debug behavior, not normal view.
   - It must remain local-only and unavailable to player UI.

4. Script package export archive contents.
   - Normal manifest is safe, but full script package archives can include hidden file content if the creator intentionally adds hidden files.
   - Validation rejects secrets/API keys/executables, but does not remove all hidden narrative content from the archive because script packages are authoring artifacts.

5. Import profile warnings may include hidden ids.
   - Safe import warns that hidden fact candidates are review-only and can include hidden candidate ids in `ref_id`.
   - It does not include hidden full text by default.

## High-Risk Leaks

None found.

No path was found where:

- Hidden facts enter player `visible_state`.
- Hidden NPC secrets enter safe character package exports.
- `private_self_summary` enters normal character packs or dialogue prompt context.
- Production debug/report data enters narrator prompts.
- Unsafe imported prompts are trusted as prompt content.

## Medium-Risk Leaks

None blocking.

Medium attention item:

- Redaction is partly decentralized and sometimes token-based. This is acceptable for v1.4 acceptance because high-risk paths use structural filtering, but future package/report expansion would benefit from a shared redaction service that redacts by visibility metadata, not only text tokens.

## Minor Issues

1. `ContentCoveragePlan.safe_refs` can show non-obvious hidden identifiers if an upstream report supplies them as uncovered ids.
   - Impact: Low; id-only exposure is less severe than text exposure, and current content coverage generally separates hidden counts.

2. Batch Quality Gate uses token redaction.
   - Impact: Low; package validators and normal reports are already mostly structured.

3. Script package archives are authoring artifacts, not safe player exports.
   - Impact: Low if docs/UI keep this distinction clear.

4. Authoring debug mode can reveal hidden lore summaries.
   - Impact: Expected local-only behavior; keep `ENABLE_AUTHORING_API` / debug controls strict.

## Fix Recommendations

No release-blocking fixes are required.

Recommended non-blocking follow-ups:

1. Introduce a shared `VisibilityRedactor` or `SafeReportBuilder` for production reports.
2. Ensure coverage planner only emits hidden counts or redacted ids for hidden coverage gaps.
3. Keep authoring/debug hidden-detail modes visually and API-wise distinct from normal production views.
4. Add a regression test for non-obvious hidden ids in coverage planner `safe_refs`.
5. Add package UI copy clarifying that Script Packages are authoring artifacts and not player-safe exports by default.
6. Continue routing safe character exports through `ExportProfile` and `CharacterPackBuilder` rather than ad hoc serializers.

## v1.4 Blocking Assessment

Not blocked.

Final status:

- Hidden facts remain out of player `visible_state`.
- Hidden facts and hidden lore are redacted from normal production reports.
- Safe package export removes NPC secrets, hidden facts, and private RP fields.
- Batch import/classification quarantines unsafe prompt and hidden content.
- Mystery and quest generators preserve hidden/player-facing separation.
- Production dashboard, local library, coverage planner, and batch quality reports return safe summaries.
- Narrator receives visible runtime context only and does not consume production debug data.
