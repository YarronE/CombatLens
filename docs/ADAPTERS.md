# Local adapter contract

Register a reviewed manifest with `python run.py register MANIFEST.json`.
Fields are `id`, `name`, `aliases`, `entrypoint`, `capabilities` and optional
`config`. Entrypoint is resolved relative to the manifest; configs are local-only.

`prepare(request, output_dir)` receives prompt text, config and project root.
It writes `research-package.json` (schema 1), `timelines.json`
(`timeline-source/1`), `source-root.json`, and optional `preview.json`
(`preview-source/1`). Sources need unique IDs, exact SHA256 and trusted roots.
Timeline package_fingerprint is SHA256 of research-package.json bytes.
Preserve native data, source coordinates, unknown time and instance conditions.

Return title, operation, coverage, gaps and findings. Findings have title,
description and source_ids. Operation must say whether this run extracted
resources, imported prior evidence, reconstructed a preview or observed a game.
Errors prevent activation. Partial output remains diagnostic, never active.

Presentation grouping uses object.presentation.subject_id and subject_name,
plus sequence.presentation_name. Native object identity stays unchanged.
Execution rules can use required_values with dotted paths into original raw_value.
No game-specific IDs or bindings belong in the generic frontend.

REA Evidence can be attached by the agent as registered files; preserve tool,
version, parameters, input digest, coverage and limitations. Session-only IDs
are insufficient for a portable evidence reference. A missing REA CLI does not
prove the agent MCP is absent. Inspect capabilities before issuing a new tool call.

Public distribution excludes real game cases. The project does not load
downloaded adapters or target-game code merely by reading a prompt.

## Optional private presentation

Both shared pages use the same Swiss grid and aerospace-inspired typography.
Provide `local/presentations/<adapter-id>/theme.json`; newly generated runs inherit
it by their adapter ID. A run-local `presentation.json` may pin a specific theme.
Assets always resolve beneath `local/presentations`, even for a run-local manifest.
Theme changes do not alter research fingerprints or saved analysis values.

```json
{
  "schema": "combatlens-presentation/1",
  "title": "Research subject",
  "subtitle": "Inspect actions and original evidence",
  "palette": {"accent": "#dfbb7f"},
  "hero": {
    "path": "reviewed-adapter/hero.png",
    "sha256": "exact SHA256 of local image bytes",
    "alt": "Description of the subject artwork",
    "credit": "Artwork owner / source",
    "source_url": "https://example.org/official-source"
  }
}
```

Palette keys: background, surface, text, muted, accent, line; values are six-digit
hex. Use sampled colors as evidence and adjust text/controls for readability.
Record input image hash, sample method and inspected package scope locally.
Missing textures are a coverage gap, not permission to invent a package palette.
Hero is optional. Only digest-checked local PNG/JPEG up to 12 MiB is served.
Paths, scripts and external image URLs are not accepted by the browser contract.
Missing/invalid themes use a generic layout with a diagnostic. Keep all game
theme manifests, visual assets, sampling reports and screenshots out of public Git.
