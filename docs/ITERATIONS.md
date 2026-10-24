# Iteration record

## 2026-10-19 / Shared visual presentation

Request: improve the local research workspace continuously and ship reusable
results; use Swiss layout, aerospace-inspired typography and game-owned imagery.
Clarify whether REA is included.

Implemented: both pages share a renderer, grid, bundled OFL display font and
private visual manifest. Newly generated runs inherit the configured theme by
adapter ID. Missing imagery keeps the generic layout. No case or artwork is
published. CombatLens remains independent; REA is separately connected when
needed for investigation. Format support belongs to reviewed adapters/readers.

Observed: 47 Python and 22 Node checks pass. Actual browser confirmed artwork,
font load, overview tabs, subject isolation, model sampling and event positioning.
Overview/action pages fit 390px; action page also fit 1440px. A fresh synthetic
run rendered without broken images. Official-image color sampling and inspected
package-material coverage are recorded locally; unavailable texture color data
remains a gap, never a whole-package color claim.

Spec: openspec/changes/archive/2026-10-19-add-instrument-presentation/.
Future increments remain event drag/resize, undo/redo, richer 3C and numeric
analysis, then another independently verified game adapter.

## 2026-10-19 / Direct timeline editing

Request: drag events, resize intervals, add undo/redo and retain model linkage;
ship the generic result while keeping all game cases private. REA development
was conditionally authorized if it improves the investigation pipeline.

Implemented: body and edge gestures, configurable native-unit snapping, keyboard
nudging, overlap lanes and session-scoped event commands. Form/add/hide/restore
operations use the same history. Save checkpoints preserve server revisions.
Cancellation restores the preview without committing. Existing proven clocks and
context gates remain in use. No REA fork was needed for this client interaction.

Observed: 47 Python and 40 Node checks passed. Actual browser covered real model
seek with drag/resize/history, independent subject contexts, form and addition
history, saving/reopening and narrow scrolled drag. Pointer cancel/blur/Escape
coverage is automated against the shared lifecycle. Generic source/analysis
protection and conflict checks remain. No new game extraction is claimed.

Spec: openspec/changes/archive/2026-10-19-add-timeline-manipulation/ (archived after verification).


## 2026-10-19 / Unified viewport and sequencer

Request: follow UE5 Timeline conventions and action-editor practice; fuse model
animation and timeline into one working window. Implemented a compact three-panel
shell, shared transport, adjustable separator, native-unit zoom, pinned ruler and
outliner, and collapsible asset/event details. Existing clock, source mapping,
history and analysis schema are reused. No external implementation code is copied.

References: Epic Sequencer Toolbar documentation for transport/snapping controls;
SkillEditorDemo at a4e3e825f75a28c040de3dce6271c70e2411dc62 for typed
Playables configuration. Reference links and limits are in the design record.
No claim of reproducing the Unreal runtime or its full Sequencer feature set.

Observed: 47 Python and 45 Node checks passed. Actual browser verified a real model
and timeline simultaneously at 1440x1000, resized/zoomed drag and both interval
edges, undo/redo, separate copy save/reopen, mapped playback to segment end,
two-axis pinned headers, subject/graph/source navigation, 390px internal scrolling
and unsaved form retention on resize. A fresh synthetic run also rendered without
models or game theming. Real inputs and screenshots remain private.

Spec: openspec/changes/archive/2026-10-19-fuse-preview-sequencer/ (verified and archived).


## 2026-10-19 / Range, loop and frame inspection

Request: playback interval selection, looping, frame ticks and stepping, retaining
model/timeline linkage; remove repeated small text and honor the owner's minimal
project scope. The supplied screenshot continues the approved fused layout.

Implemented: bounded clip-time clock with modulo wrap, mapped timeline markers
and atomic numeric range application, sample-index ruler and exact adjacent-frame
steps. Registered sample times define frame indexes; no runtime FPS is guessed.
Frame display preserves native event units, source rate and copy history. Range
and loop reset with the clip/context and never serialize into research/copies.
Repeated metadata/limitations and existing view/file tools unfold on demand.
No new unrelated settings, output format, model/runtime simulation or REA fork.

Observed: 47 Python and 55 Node checks pass. Actual browser covered rate-one and
rate-two samples, stop at selected end, repeated looping, pointer/keyboard bounds,
invalid input preservation, source-context reset, event undo/redo and save/reopen,
390px two-axis scrolling and bounded numeric disclosure. No-model synthetic input
disables playback/frame controls without supplying a false clock. Case evidence
and screenshots remain local. Generic generated workspaces use the same renderer.

Spec: openspec/changes/archive/2026-10-19-add-playback-range-frames/ (verified and archived).

## 2026-10-19 / Designer-facing Notify details

Request: explain Notify effects, conditions and related values for combat designers;
select the corresponding animation frame, retain a minimal interface and never
guess missing evidence. Synchronize generic improvements and keep the pilot local.

Implemented optional reviewed guides bound to exact Build, registered execution
summary and all underlying source/table-proof hashes. Explanations use explicit
rule bindings plus original instance conditions. Numeric references preserve zero,
false and unknown units; analysis overrides cannot alter evidence eligibility.
Skill-stage evidence remains separate. Compact effect/condition/value blocks lead
the inspector, with raw proof and editing disclosures below. Event clicks pause
and select the first registered sample at/after mapped start in the proven current
segment. Existing exact-time gestures/history and sample-based playback remain.

Observed: 56 Python and 66 Node tests passed. Actual browser checked known and
unknown same-class instances, critical branch limits, rate-two sampling, early-load
selection, playback pause and frame step, original-vs-analysis evidence, undo/redo,
save/reopen, 390px width and no-guide/no-model fallback. Original package fingerprint
and source hashes remain unchanged. No new extraction, runtime observation or REA
fork is claimed. All case notes, evidence and screenshots remain local.

Spec: openspec/changes/archive/2026-10-19-add-designer-event-details/ (verified and archived).

## 2026-10-20 / Local bundles and independently prepared native case

Request: preserve the completed local case in its own analysis package, then reuse
existing unpacking practice for a second case; improve the generic workflow and
deliver its integration to the authorized private case repository. Game data must
remain outside public Git.

Implemented a source-current, exclusive freeze command with hashed copied evidence,
pinned runtime and optional reviewed overlays. Research bytes/fingerprint and
copy revisions remain unchanged. Explicit static GLB mode retains actual geometry
while disabling unproven clocks/frames. Native configuration scopes retain their
own selector label and raw field references. Exact data links appear before long
raw JSON. The second-case check exposed mixed-game copy listings; these are now
scoped to current Build/package, preserving other files on disk.

Observed: 67 Python and 69 Node checks passed. Actual browser verified frozen
prior-case explanations/sampling and saved-copy listing, static source meshes,
native coordinate editing/history/save/reopen, scoped exact references and AI
links, object clearing and narrow layout. Previously exported native payloads
were independently re-read; results are reuse/verification, not new extraction.
No FPS, complete assembly, skeletal binding or runtime callback was fabricated.
No game inputs, names, findings, adapters or screenshots enter this public change.

Spec: openspec/changes/archive/2026-10-20-add-local-bundles-static-preview/ (validation complete;
delivery and archival tracked in Tasks).

Source-backed skeletal playback: accept active-scene root/helper channels when a clip drives a registered joint or its real ancestor. Unrelated-only and unreachable channels remain rejected. Adapter extraction must preserve authored endpoints and keep independent clip time separate from unproven native event clocks. Validation: 80 Python and 74 Node checks passed; native case assets remain local.

Multiple native skins retain independent joint arrays and inverse bind matrices.
Each mesh binding is checked against its own skin; shared geometry is checked
against every binding. No source bind space is merged or retargeted.

## 2026-10-20 / Source-authored frame coordinates

Request: bind native event instances to real clip poses without guessing missing clocks, keeping the compact editor and local-only case evidence.

Added explicit authored-frame coordinate scale, separate from playback rate. The server and client reject missing, inconsistent or mismatched unit proofs. Range, loop, cursor and frame seek retain the declared action unit, with registered sample numbering independent of source authoring frames. Float32 rounding does not advance an extra sample. Synthetic validation uses different authoring and sample rates. Static pose positioning does not claim runtime callback execution, transition mixing or hit-stop reconstruction. Real mappings and all case inputs remain local.

## 2026-10-21 / Smooth Timeline dragging

Request: improve free dragging and reduce stutter while retaining model/Timeline linkage.

The prior empty-axis path sought only after a completed click and rebuilt the workspace before updating the pose. Loaded-context scrubbing now follows captured pointer input directly. Latest-position coalescing covers scrub, event and range gestures; pointer-up flushes the final input, while cancellation drops pending work. Event movement still creates one undo entry. Identical-time seeks avoid redundant pose evaluation. Existing event selection, unit proofs, playback range and case isolation remain intact.

Validation: 81 Python and 85 Node checks passed, including synthetic burst, final-flush, cancellation, context and history cases. Actual browser input verified intermediate pose updates, unchanged DOM during scrubbing, event undo/redo and range handles. All local measurements and case screenshots remain outside Git.


## 2026-10-24 — Evidence design study

The approved v0.1 review requested three production views and animation seeking
only for confirmed event coordinates. The shared inspector now resolves facts
from registered fields, retains evidence gaps, and reuses existing selection and
preview controls. Action-scoped asynchronous loading prevents old responses from
crossing contexts. Calculations and hypotheses keep their own evidence status.
Two reviewed local imports exercised animated-second and native-frame/static
paths. Browser acceptance confirmed both outcomes. Case material stays local.


## 2026-10-24 — Whole-game analysis

The user requested broader gameplay analysis beyond individual actions. The
shared workspace now connects preparation, session systems and progression to
registered native rows and explicit references, with a build comparison notebook.
Local evidence exposed repeated native pool IDs and group-level tool annotations;
both retain physical-row identity rather than selecting an arbitrary first row.
Native table shape mismatches remain import gaps instead of relaxed decoding.
Source summaries and analyst hypotheses are independently labeled. The existing
visual language and action workflow remain available without a case-specific
frontend fork. Routine decisions were delegated to the agent under the current
collaboration rule; no human review is claimed for the engineering design.


## Source-bound gameplay reading

The user requested designer-readable relationships across preparation,
exploration rewards, equipment effects and builds. Added an optional reading
layer with player choices, conditional tradeoffs, exceptions and source gaps.
Evidence can be inspected beside prose and opened at its original physical row.
Counts are recomputed and dependent prose fails closed on invalid evidence.
An actual package exposed source-kind loss in the reduced registry; the resolver
now reads classification from the fingerprinted package, with regression coverage.
Generic checks cover partial invalidation, typed counts, closure and hostile
registration. Case interpretation and imported evidence remain local.
