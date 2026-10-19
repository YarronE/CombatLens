# Unified action editor
## ADDED Requirements
### Requirement: One editing surface
A desktop user MUST see the model viewport and timeline in the same bounded editor panel. One shared transport MUST drive the existing animation clock; primary timeline time MUST show proven action time or an explicit unavailable state. Clip sampling and provenance MUST remain accessible in details.
#### Scenario: Prepared model
Opening an action shows model above timeline, navigation left and properties right. Playback and timeline seeking update the same model and playhead. Selecting another subject updates both surfaces without carrying the previous subject's time.
#### Scenario: No mapping
Missing model/mapping remains explicit, and no arbitrary FPS or game-time relationship is inferred.

### Requirement: Adjustable dock and readable tracks
The model/timeline divider MUST support pointer and keyboard resizing with bounded panel sizes. Ruler and track names MUST remain visible during timeline scrolling. Zoom MUST preserve source coordinates and editing history.
#### Scenario: Resizing and scrolling
Resize the divider, scroll/zoom the timeline, then move or resize an event. Coordinates, undo/redo and model linkage remain correct. Ruler clicks seek the model; track-label clicks do not seek.
#### Scenario: Narrow window
At 390px the fused panel remains usable with internal timeline scrolling; properties and source actions remain accessible without document-wide horizontal overflow.

### Requirement: Preserve research and copy workflows
Existing original read-only mode, analysis edits, history checkpoints, save/reopen, graph and source dialogs MUST continue to work. Layout state MUST NOT be serialized into game research or analysis data.
#### Scenario: Regression
Drag an event, undo/redo, save and reopen the copy using the new window. Original sources and server revisions remain protected. Unconfigured synthetic inputs retain a functional empty viewport.
