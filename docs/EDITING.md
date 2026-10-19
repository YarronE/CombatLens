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
