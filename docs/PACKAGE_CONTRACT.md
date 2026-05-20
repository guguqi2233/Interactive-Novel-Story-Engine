# Package Contract

Current package contract version: `1.8`.

Local packages must include package id, package type, version, contract
version, engine/schema compatibility, included files, checksums, dependencies,
conflicts, creation time, and redaction policy.

Imports must perform dry-run validation, compatibility checks, checksum checks,
zip-slip checks, executable rejection, and secret-file rejection. Apply requires
explicit confirmation and must not execute package code.
