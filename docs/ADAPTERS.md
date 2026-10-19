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
