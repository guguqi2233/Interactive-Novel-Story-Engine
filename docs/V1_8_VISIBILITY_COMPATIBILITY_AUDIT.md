# v1.8 Visibility and Compatibility Audit

Verification date: 2026-05-21

## Passed Items

- Legacy save migration preserves hidden visibility classification. v1.8 migration checks include hidden-fact preservation and EventLog preservation.
- Compatibility shims do not change hidden/visible classification. They emit warnings for legacy shape changes and refuse unsupported breaking versions.
- Deprecated fields are metadata-driven. Deprecated-field handling warns, but it does not promote hidden data into player-visible state.
- Package import compatibility checks validate manifest contract version, checksum, zip-slip safety, executable rejection, and sensitive-file exclusion before apply.
- Content pack legacy loading uses compatibility paths and validation warnings. It does not make hidden fields player-visible.
- Module, action, and prompt profile compatibility checks preserve existing visibility boundaries. Prompt profiles cannot enable hidden facts or state modification.
- Debug API contract remains isolated from player API. Debug data is gated and redacted by default.
- Contract docs and generated indexes list schema and contract metadata only. They do not include hidden fact text, raw prompt content, or raw GameState data.

## Possible Leak Paths

- A future compatibility shim could map an old hidden field into a visible field if it bypasses the central shim policy. This is a design risk, not observed in the current implementation.
- Legacy content packs without schema metadata require careful validation. They should continue to load through warning-producing legacy paths, not through silent mutation.
- Debug reports must remain separate from narrator/player surfaces.

## High-Risk Leaks

No high-risk visibility leak was identified for v1.8.

## Medium-Risk Leaks

- `docs/V1_8_ROADMAP.md` is absent, so the visibility audit uses implementation docs and tests rather than a roadmap source.
- Contract docs generator can only be as safe as its input constants and registry metadata. Do not add raw examples containing hidden content to generated docs.

## Small Issues

- Compatibility matrix output is intentionally high level. It should not be treated as a detailed migration report.

## Fix Recommendations

- Add tests when introducing any new shim that touches visibility-related fields.
- Keep hidden-to-visible mutations out of compatibility shims unless a rule-level migration explicitly authorizes them and tests cover the path.
- Keep player API tests checking that debug fields, hidden facts, and raw state deltas stay out of ordinary responses.

## Acceptance Impact

This audit does not block v1.8 acceptance. Current compatibility and migration paths preserve hidden/visible boundaries.
