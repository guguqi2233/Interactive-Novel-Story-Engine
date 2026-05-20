# Save Migration Contract

Current save migration contract version: `1.8`.

Migration supports status, dry-run, apply, failure reporting, and
pre-migration backup restore. Apply must preserve the original save on failure,
record a pre-migration checksum when possible, keep EventLog data, and preserve
hidden visibility classification.

Dry-run never writes. Restore requires explicit confirmation.
