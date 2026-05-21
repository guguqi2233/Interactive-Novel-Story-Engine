# v2.0 Release Checklist

The v2.0 release checklist is a local-only freeze tool. It checks tests, frontend
build, contract docs, audits, package safety, compatibility readiness, and
release docs. It does not commit, tag, upload, or auto-fix anything.

Run:

```bash
python -m backend.app.tools.v2_release_checklist --json
```

High-risk blockers cannot be ignored. Missing v2 docs, tracked secrets, failing
compatibility checks, failing tests, failing frontend build, hidden leaks, and
package import security issues block release.

