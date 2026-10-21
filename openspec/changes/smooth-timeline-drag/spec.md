# Spec

Dragging the ruler or empty Timeline seeks continuously without editing evidence, copies or undo history. Only the current proven animation/unit mapping may drive poses. Drag samples coalesce to the latest pointer position once per display frame. Pointer-up flushes the exact final position; Escape, blur and capture loss discard pending work and restore the starting playhead. Range and event gestures use the same coalescing, preserve their existing bounds and commit/cancel semantics. Event dragging creates one undo entry at release. Switching context invalidates pending seeks. Existing click-to-registered-frame, loop, sample step and source checks remain intact.

Acceptance uses actual browser pointer gestures, current native mapped poses and meaningful deterministic scheduler/cancel tests. Measure observed rendering and sampling costs separately; do not label scheduling counts as measured FPS.
