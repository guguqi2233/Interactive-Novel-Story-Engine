# Deprecation Policy

Deprecated fields must declare field path, introduced version, deprecated
version, optional removal version, replacement, migration strategy, and warning
level.

Validators should warn before removal. Fields must not be deleted without a
migration path, and deprecated hidden/debug data must never become
player-visible through compatibility handling.
