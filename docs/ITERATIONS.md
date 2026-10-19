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

Spec: openspec/changes/add-timeline-manipulation/ (archived after verification).
