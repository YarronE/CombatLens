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

Spec: openspec/changes/add-instrument-presentation/.
Future increments remain event drag/resize, undo/redo, richer 3C and numeric
analysis, then another independently verified game adapter.
