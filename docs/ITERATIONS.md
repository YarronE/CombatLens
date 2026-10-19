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
