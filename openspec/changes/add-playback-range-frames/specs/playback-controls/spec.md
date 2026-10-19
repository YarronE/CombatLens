# Playback controls
## ADDED Requirements
### Requirement: Bounded playback and looping
Users MUST select a positive playback interval within the current proven animation segment through timeline handles and numeric controls. Playback MUST stop at its end or wrap with overshoot when loop is enabled, applying source play rate and observer speed exactly once. Selection is transient, independent of event edits/history and reset on clip/context replacement.
#### Scenario: Range playback
Choose a subrange, play to the end, toggle looping, and observe the same model and timeline playhead. Replaying from the end restarts at the selected beginning. Seeking outside the range remains available while paused; Play enters the selected range.
#### Scenario: Invalid or absent mapping
Invalid numeric range leaves the previous range intact with a concise message. Timeline range controls are unavailable when the selected coordinate cannot be proven to map to this clip. No animation/mapping means no fabricated linked playhead.
### Requirement: Frame inspection
Frame ticks MUST use registered animation sample times, preserving seconds and original event units. Frame stepping MUST seek the adjacent registered sample exactly; no real-time FPS assumption. Source-rate-two mapping MUST convert each clip frame to half as many action seconds.
#### Scenario: Exact samples
Switch between seconds and frames, step forward/back, resize/zoom/scroll, then drag an event and undo. The model and playhead retain the proven correspondence. Missing frame samples disables the frame mode explicitly.
### Requirement: Minimal editor surface
The default surface MUST retain only necessary action selection, viewport, playback, timeline and event properties. Repeated metadata/limitations and low-frequency existing tools MUST be accessible through details rather than tiny default text. Essential labels remain readable; errors remain visible.
#### Scenario: Regression and narrow layout
Existing source dialogs, graph, copy save/reopen and undo/redo remain usable; 390px has internal timeline scrolling and no document horizontal overflow. Existing games and newly generated workspaces use the same generic renderer. No game case enters public Git.
