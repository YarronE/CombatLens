# Independent local workspaces

An optional workspace-collection/1 catalog in the current research directory registers up to 500 unique slug IDs, display titles, relative directories under repo/local/research, and exact research-package SHA256 fingerprints. The catalog is limited to 512 KiB. Paths, IDs, schema and fingerprints are checked before resolving a workspace.

URLs under /workspaces/<id>/ use a request-local repository and preview context. Each source, preview, run report and analysis operation follows that context. Host/Origin protections, immutable evidence, fingerprint-scoped copies and source byte checks remain unchanged. Separate tabs have independent URL scopes. Existing single-workspace URLs remain supported.

The shared renderer exposes one catalog select when a catalog exists. All API and preview requests retain the current workspace prefix. A prepared run with activate=False is validated without publishing it; callers publish a batch catalog only after all required runs are ready. A frozen bundle captures the selected workspace, not the full collection.
