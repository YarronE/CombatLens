# Tasks
- [x] T1 Implement local presentation API and boundary tests (D2; private visual scenarios).
- [x] T2 Apply shared Swiss/aerospace renderer and bundled OFL font (D1/D3/D4).
- [x] T3 Validate local artwork, palette scope, future-run inheritance and generic fallback.
- [x] T4 Update installation and adapter contract; verify prerequisite scenario.
- [ ] T5 Run automated checks, desktop/narrow browser interaction checks and public file scan; commit and push generic changes.

Evidence: local/validation/presentation-python.log (47 passed) and
presentation-node.log (22 passed). Real browser image/font load and tab navigation
passed; model sampling advanced to 0.0167s and selected event positioned animation
to its source-backed time. Both pages fit 390px, action page fit 1440px. Separate
unconfigured synthetic run rendered with no broken image. Theme inheritance and
invalid registrations are covered by synthetic tests. No game identifiers or
screenshots are included in this record. T5 awaits publication verification.
