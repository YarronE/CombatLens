# Design

Add runtime/collection.py to resolve a catalog and cache Repository/PreviewRepository pairs by registered ID and fingerprint. Handler parses /workspaces/<id>/ before routing APIs or static files and uses request-local context, never a global current selection or cookie. LensHandler run-report routing must use the same context. Add web/workspace.js for API prefix construction and a single native select, used by editor, overview, theme and preview. The catalog registers only prepared runs in the same project. Do not accept browser-supplied filesystem paths.

Acceptance uses two synthetic research runs with distinct objects/assets/copies, stale hash and unsafe path rejection, legacy behavior, and native ZZZ multi-Boss browser verification. No game data enters tests.

Batch callers use analyze(..., activate=False), then publish the selected pointer only after every run and catalog is valid. The normal single-run call still activates by default.
