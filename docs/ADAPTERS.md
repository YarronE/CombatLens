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

## Optional reviewed event explanations

Provide a private `local/interpretations/<adapter-id>/event-guide.json`; subsequent
runs inherit it through run-report.adapter. A research-run `event-guide.json` takes
precedence for a pinned interpretation. Missing/invalid guides leave details
explicitly unknown. Guides are presentation overlays and do not change package
fingerprints or existing analysis copies. GET /api/event-guide uses the same local
API authorization as research endpoints and returns no filesystem paths.

The JSON schema is `combatlens-event-guide/1`. Required fields:

- `game_build`: exact current Build.
- `execution_source`: registered execution summary `id` and exact byte `sha256`.
- `evidence_files`: complete unique `{name, path, sha256}` records for the
  summary's source_files, plus every rules[].table_proofs snapshot. For a table,
  name is `table/<basename>#<first 12 characters of source_sha256>`. Paths must
  remain in the registered summary's approved roots; hashes must be current.
- `entries`: unique reviewed interpretations keyed by an existing `rule_id`.

Each entry has title, effect, nonempty conditions (string array), boundary and
numbers. A number is `{label, scope, path, unit, note}`; scope is `rule` or `event`,
and path is an own-field dotted path into the bound rule or original raw_value.
There are no literal/default numeric values. Missing fields remain unknown.
An optional integer action_id and scalar required_values further narrow original
instances; they cannot expand a rule's eligibility or refer to analyst overrides.

The frontend requires explicit event.execution_rule_ids and the execution rule's
existing class/action/Buff/required-value checks. Only static_cil_verified and
asset_data_cil_join_verified rules can explain effects. No class-name heuristic
is used. Stage rules are displayed separately from Notify callback explanations.
Every selection rechecks summary and dependency freshness. A changed/missing
dependency suppresses interpretation rather than retaining an old verified badge.

Author explanations from reviewed callback and table evidence. State branch
exceptions, duration modifiers and incomplete cleanup paths where relevant. The
reader verifies provenance; it cannot prove that prose faithfully describes code.
Review is required before local registration. Real case guides and their evidence
remain private; synthetic tests document the public contract. No target game code
executes when a guide is read, and no new extraction or runtime simulation is implied.

## Static geometry and native configuration scopes

A preview-source/1 asset may explicitly declare `kind: "static_mesh"` with
`clips: []`. It still requires registered object/sequence/source IDs, exact GLB
hash/length, format and local_path beneath local/preview. Include material_status,
source_paths.mesh, geometry, coordinates and assembly_status as evidence notes.
Each separate mesh stays separate when assembly transforms are unproven.

Static GLBs must contain visible finite geometry in the selected scene and no
skin, skin attributes or animations. Their vertices/indices and hierarchy receive
the same bounded checks as animated assets. The omitted/default kind remains
skinned_animation with all existing rig and clip requirements. Static geometry
does not enable a playback clock, frame indexes, bones or action-time mapping.

For native state/configuration datasets, object.presentation.sequence_label can
label the existing selector/count (default: 技能招式). It changes no source identity
or action grouping. Keep unrelated states separate; equal/similar names do not
prove a common AnimatorController or runtime binding. Use source_units when only
serialized coordinates are established. Preserve simultaneous native time fields
in raw_value; do not select their runtime precedence or infer a frame rate.

An event may provide native_links, each with kind, name, optional scope/raw_value,
boundary, registered source_ids and same-object sequence_ids. These are explicit
data-reference joins, displayed in folded raw evidence. They never establish an
execution rule. Exact original key plus original scope is required; missing or
ambiguous links stay unresolved. Analysis modifications cannot rewrite these links.

Use the shared freeze command for local case delivery. Keep game-specific adapter
code in ignored local directories or an explicitly authorized private game repo;
public CombatLens Git continues to contain generic implementation and synthetic
checks only. Native parsers should state which original bytes were re-read on
each generation rather than relabel an old validation report as a fresh check.

## Workspace collection

For large prepared cases, generate separate standard runs under `local/research/`.
In the selected/default run write `workspaces.json`:

```json
{"schema_version":"workspace-collection/1","label":"研究对象","default_id":"sample-one","entries":[{"id":"sample-one","title":"Synthetic object","directory":"synthetic-run-one","fingerprint":"<exact research-package.json SHA256>"}]}
```

Directories are relative to this project's `local/research`, with no absolute paths or traversal.
IDs must be unique ASCII slugs (up to 80 characters). The server rejects stale package hashes.
Use `/workspaces/sample-one/viewer.html` or its overview URL. All evidence, previews and saves
use this URL scope, so separate tabs do not share a mutable selected object. The original
Host/Origin and source validation rules apply. The default run remains available at legacy URLs.
The catalog supports up to 500 entries and 512 KiB. `freeze` captures the selected run; it does
not bundle the entire collection. No game data belongs in the repository.

Batch integrations may call `analyze(..., activate=False)` to validate individual runs without changing the current entry. Publish the chosen research pointer only after every required run and catalog is ready. The default single-run call still activates immediately after its validation.

Rig animation may include source root and attachment transforms in the active scene.
Each clip must drive a registered joint or one of its real hierarchy ancestors;
unrelated helper-only clips, unreachable targets and invalid key data remain rejected.
Decoded padding past an authored clip endpoint must not extend that clip. Native
state/event clocks need independent proof; use separate source-backed clip sequences
when the native event clock or controller binding is unresolved.

Multiple source skins are supported. Each skinned node must reference its actual
skin; preserve per-skin inverse binds and vertex joint indices. The optional
joint_count counts unique node IDs across all skins. Source geometry may include
unskinned attachments, while the file still needs a real animated rig.


## Optional evidence design study

Write run-local `design-study.json` with `schema: combatlens-design-study/1`,
the exact `game_build`, `package_fingerprint`, and `entries`. Each entry has
`object_id`, `sequence_id`, `facts`, `calculations`, `hypotheses`, and `gaps`.
The optional `sequence.study_focus_track` chooses an initial rhythm filter;
the user can still select every original track.

Facts have a unique `id`, `label`, `view` (`rhythm`, `values`, or `phases`),
`kind` (`configuration`, `observation`, or `author_statement`), `source_id`,
an exact JSON `pointer`, optional `unit`, `note`, and `dependency_ids`.
Values are resolved from hash-checked registered JSON, never from adapter
literal claims. Register underlying binary/decompiler dependencies as well.
Unknown fields remain gaps; false, zero, and dynamic structures stay distinct.

Calculations declare `label`, `view`, `operation` (`difference` or `ratio`),
and exactly two fact IDs in `inputs`. Inputs must be finite numbers with the
same known unit; division by zero remains a gap. Hypotheses declare `view`,
`text`, `validation`, and supporting `fact_ids`. Changed support suppresses
the hypothesis. No arbitrary expressions are executed.

The overlay is bounded to 2 MiB and 500 entries; source JSON to 64 MiB.
The endpoint `/api/design-study` follows workspace/origin authorization.
Missing overlays retain the legacy workspace. Frozen bundles preserve the
overlay and its registered sources without changing the package fingerprint.

Study event selection accepts explicitly confirmed coordinate statuses
(`authored_montage_seconds`, `authored_frames`, `source_frame_only`,
`native_seconds`, `confirmed`, or `synthetic`) and current evidence. A native
coordinate alone cannot seek a model. A matching preview mapping and actual
`sample_times_seconds` are required. Sample rate never proves runtime FPS.
Unknown selections pause without moving the pose. Analysis mode displays the
original study and disables its seek actions; copy editing remains separate.


## Optional whole-game study

Write `game-study.json` with schema `combatlens-game-study/1`, `game_build`,
the exact `package_fingerprint`, `systems`, `tables`, and optional `lifecycle`,
`analyses`, `build`, and `gaps`. All case-specific content remains private.
Systems identify a label, phase, research question, description and gaps.
Lifecycle entries resolve a registered `source_id` and JSON `pointer`;
dated official descriptions must remain separate from fixed native snapshots.
Analyst interpretations have a system, title, interpretation, validation
question and supporting source IDs; changed support suppresses the explanation.

A table descriptor has `id`, `label`, `system_id`, `source_id`, a JSON pointer
to a row array, exact physical `count`, and `dependency_ids`. A standalone row
object may set `single_row`. Rows retain `id` and `fields`; source row index is
the authoritative physical ordinal. Preserve duplicate native IDs. Optional
`label_source_id` reads tool annotations in `Entries[{ID, Entries}]` format.
Group annotations never name individual rows with duplicated native IDs.
`display_fields` and `field_labels` affect presentation only.

Reference rules declare exact `fields`, target `table`, optional `sentinels`
(default -1) and `mode` (`reference` or `pool`). All matching physical rows are
returned. A pool is a candidate set, never an applied effect list. Unique,
ambiguous, missing and stale targets remain distinct. No inferred suffix joins,
weight normalization, arbitrary expressions or user-supplied file paths.

`profile_fields` registers scalar distribution fields. Counts describe physical
rows, including zero, false, null and absent fields. Clicking an original value
filters the table. Integral JSON floats and integers compare numerically while
booleans remain distinct. A table `projection` declares x/y and nonempty
`frame_fields`; plots require a selected identical frame and retain native units.
No world-map composition or navigation calculation is inferred.

Read-only endpoints use the existing host/origin and workspace scope:

- `/api/game-study` returns metadata and source-dependent status.
- `/api/game-study/rows?table=&q=&native_id=&offset=&limit=` searches/paginates.
  Registered `field=JSON_scalar` in q filters an exact original value.
- `/api/game-study/record?table=&ordinal=` resolves a physical row and references.
- `/api/game-study/profile?table=&field=` returns literal category counts.
- `/api/game-study/projection?table=&frame=` returns same-frame native coordinates.

Bounds: 2 MiB overlay, 120 tables, 200,000 rows per table, 200 rows per page,
240-character query, 192 MiB per source JSON, and four cached documents bounded
to 224 MiB of source bytes. Parsed object memory is additional. Large sources
load only when queried. Register raw inputs, definitions and decoder dependencies.

Build metadata supplies kind labels, modes and declarative validation settings:
role limits; field-equality mode restrictions; item/container color capacities
partitioned by declared fields; and direct-reference tables to trace. These are
configuration checks, not full engine validation. Unselected containers and
unknown unlock/character rules remain explicit gaps. Drafts use schema
`combatlens-build/1`, source fingerprint, name, mode, party size, notes and at
most 24 `{table, ordinal}` selections. Exported comparisons contain two drafts;
foreign fingerprints and invalid identities are rejected. Imported records are
revalidated instead of trusting serialized source values.

Missing study files retain legacy behavior. Private freeze copies the overlay
and registered source closure. A frozen bundle remains a fixed local installation.


## Optional gameplay reading

Within `game-study.json`, `reading` uses schema `combatlens-game-reading/1`, a
title/scope, at most 96 facts and 16 chapters. No case content belongs in public
Git. An absent reading preserves existing behavior; invalid reading registration
does not disable original tables.

Facts have unique IDs, labels, notes and optional dependency IDs. `type: excerpt`
reads a registered source ID and JSON pointer, with a 4,000-character serialized
limit. Its source kind comes from the fingerprinted research package, never an
untrusted fact label or the reduced runtime registry. `type: record` specifies
table, physical ordinal and 1-16 exact field names. `type: measure` specifies
table and `count` or `distinct`, with an exact scalar `native_id` filter and up to
four scalar field equalities in `where`. Distinct measures require `field`;
missing/complex values fail rather than becoming invented categories. False,
zero, null and strings remain distinct. Measures count physical rows or distinct
raw field values; they carry scope and are never runtime probabilities.

Chapters have unique IDs, title/short_title/question, system_ids, validation,
gaps, and non-empty fact_ids. Supported content consists of player_choice,
interpretation paragraphs, connection to the next choice, counterexamples and
tradeoffs with option/gain/cost/condition. Each chapter independently suppresses
that content if any required fact fails source, dependency or field checks.
Titles, validation questions and gaps remain diagnostic. Narrative connections
describe analyst reasoning, not proven native joins. Current facts expose source
SHA, pointer/dependencies and optional exact record location for drilldown.

The reading view is selected by `#view=reading&chapter=<id>` and becomes the
default only for compatible packages. Chapter changes cancel pending detail
requests. Raw configuration and Build notebook links retain existing identity
rules. Refresh revalidates the reading; browser navigation restores the chapter.
Private freeze retains the overlay and all registered reading sources.
