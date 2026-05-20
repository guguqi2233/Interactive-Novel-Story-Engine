# Deprecated Fields

Deprecated fields must include replacement and migration metadata.

| Field | Deprecated | Replacement | Migration Strategy |
| --- | --- | --- | --- |
| `content_pack.manifest.content_schema_version` | `1.8` | `schema_version` | Map content_schema_version to schema_version during legacy content-pack loading. |
