# Analysis timing and history

Original events are read-only. Enter analysis mode before dragging. An event body
moves both times by the same delta; edge handles change one endpoint. Points stay
points. Events without established timing remain in the untimed list until an
analyst explicitly supplies a hypothesis in the form. Overlap display lanes never
change source track IDs. Selecting an event preserves timeline scrolling.

Snap choices use native axis units: 0.01/0.1 for seconds and other numeric units,
1/5 for frames, or free pointer movement. There is no inferred FPS conversion.
Left/right arrows adjust a focused event or endpoint; Shift multiplies the step
by ten. Free-mode keyboard adjustment uses the fine step. Pointer movement stays
within the displayed domain; use the form for values beyond that domain.

Move, resize, form changes, add, delete/hide, unhide and reset use event-scoped
commands. Each pointer gesture commits once on release. Escape, window blur,
pointer cancellation or lost capture discard the gesture and restore the prior
preview position. A short click selects without a command. Only the current
pointer owns its gesture.

Undo/redo applies only to the current analysis copy, across subject navigation.
New edits after undo discard redo. Saves preserve history and mark a clean state;
undo after saving makes the copy dirty, and redo to the saved checkpoint clears
that flag. Server revision, copy identity and original evidence never rewind.
During a save, edits and copy replacement are disabled; errors retain unsaved data.

History is session-only and limited to 100 commands. Loading/importing a copy,
creating one or saving-as starts fresh history. Refresh does not erase saved
values. Use buttons, Ctrl/Cmd+Z, Ctrl/Cmd+Shift+Z or Ctrl+Y outside text fields.
Native field undo and modal dialogs retain their own keyboard behavior.

Dragging previews the moved start or manipulated endpoint through the existing
proven animation mapping. Undo/redo seeks the restored selected event. Missing
mapping, unsupported units and times outside a registered segment retain the
existing explanation; no game-time correspondence is fabricated. Changes are
analyst hypotheses and do not run game callbacks or write back to the game.


## Unified viewport and sequencer

The center dock keeps the model above the event timeline. Drag the horizontal
separator, or focus it and use Up/Down; Home/End choose the 25%/75% limits. Resizing
keeps the current renderer and animation time. Layout choices do not enter edit
history. The shared transport controls the existing preview clock; the adjacent
readout uses mapped action coordinates. Unproven mapping stays explicitly absent.

The timeline ruler stays at the top while tracks scroll vertically. Native track
labels stay on the left while time scrolls horizontally. Zoom/fit changes pixel
scale, preserving event times, units and undo commands. Window resizing adapts the
axis unless a form draft or pointer gesture is active; the next render applies the
new width. Track-name clicks do not seek animation.

Asset/clip selectors, source proof and the optional clip sampling slider are in
the right inspector. Clip seconds remain distinct from the timeline's action unit.
The collapsed event catalog contains untimed records, additions and hidden-event
restoration. Its open state survives timeline rerenders. On narrow screens, details
stack below the dock and the axis scrolls internally. The graph view and source
dialogs retain their original behavior.


## Playback range and frames

Drag the two markers above the ruler to select playback bounds. Focus a marker
and press Left/Right to adjust it. In frame mode, keys select the adjacent
registered sample; pointer markers snap to the nearest sample. The Range menu
applies both numeric values together; Full segment restores the mapped bounds.
Reversed/outside values keep the previous selection and show a concise error.
Range gestures cancel through the existing capture lifecycle and restore time.

Play starts inside the range. With Loop off it stops exactly at the end; with
Loop on it wraps and retains overshoot. Source rate and observation speed apply
once. Changing clip/subject resets range and looping. Paused seeks and frame
inspection may leave the selected playback interval. Range/loop are transient
preview settings and never enter copy JSON or undo history.

Choose seconds or frames on the timeline. Frames are zero-based indices of the
registered animation sampling sequence, not runtime FPS or assumed uniform time.
Previous/next frame seek exact samples; frame ruler positions use the proven
clip/action mapping, including trimmed and rate-two segments. Fractional range
values preserve subframe selection by interpolating neighboring registered times.
The existing event snap and stored event units remain unchanged by display mode.
Missing mapping disables linked range/frame display; missing registered samples
disables frame stepping. No model disables playback. All evidence remains in
Action information / Asset sources; normal limitations no longer fill the dock.

View tools and file operations unfold on demand. Graph, source dialogs, original
values and analysis forms remain available. The working surface adds only range,
loop and frame controls requested for this iteration.

## Event details and frame selection

Selecting an event pauses preview and seeks the first registered animation sample
at or after its mapped start (with a small floating-point comparison tolerance).
The sample must lie within the currently proven segment. The displayed frame is
an animation sampling index, not a runtime callback observation. No inferred FPS
or cross-segment search is used. Unavailable mapping retains the pose and explains
the gap. Dragging, scrubbing and history retain their existing exact-time behavior.
Late validation responses cannot move a newer selection or another subject.

The compact inspector shows effect, conditions and numbers only when a reviewed
local guide matches current Build, execution summary, underlying evidence and the
original event's explicit rule binding. Original class, action, Buff and required
values restrict eligibility; analyst overrides cannot establish evidence. Values
come from referenced original fields, preserving zero and false. Missing values
or units stay unknown. Skill-stage rules appear separately in the evidence fold.

In analysis mode, explanations are labeled original-instance evidence. The sampled
position follows the effective analysis time; changing parameters does not simulate
the callback. Raw fields, sources and the edit form unfold on demand. Guide data
never enters research packages, saved copies or undo history.
