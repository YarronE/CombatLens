# Tasks
- [x] T1 Pure timing/history implementation and synthetic behavior tests (D1).
- [x] T2 SVG pointer/keyboard interaction, cancel paths and preview (D2/D4).
- [x] T3 All event-edit entry points use history; save checkpoint/isolation and UI (D3).
- [x] T4 Real browser verification: drag, interval edges, cancel, undo/redo, model, save/reopen and narrow view.
- [x] T5 Update generic docs/spec and local project evidence, scan public files, push and verify remote refs; archive change.

Evidence: local/validation/timeline-python.log (47 passed), timeline-node.log
(40 passed); real browser confirmed body/edges, copy history and model seek,
save/reopen, text-field undo, additions/deletion/reset, narrow scrolled movement
and subject isolation. Shared pointer cancellation lifecycle has deterministic
EventTarget tests. Source revalidation passed. T5 scan passed; implementation 8be81cc3465b927921c915c4cd47d57e2591b39f pushed and both remote refs verified. Shared capability spec synced and this change archived in the delivery commit.
