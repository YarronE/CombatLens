# Timeline editing
## ADDED Requirements
### Requirement: Direct editing of analysis timing
Only a current analysis copy MUST permit moving known timed events and resizing interval edges. Move MUST preserve duration; handles MUST NOT invert intervals. Dragging MUST use the displayed coordinate unit and domain, with a visible configurable snap step. Unknown timing MUST NOT be manufactured. Original and stale evidence views MUST remain read-only.
#### Scenario: Move or resize
A pointer drag on the event body moves its timing; dragging either edge changes that edge only. Overlapping events MUST remain individually targetable. One completed gesture creates one undo entry. A click without movement only selects. Escape, pointer cancel, lost capture or window blur cancels without a new edit and restores preview.
#### Scenario: Keyboard and scaled view
Focused events/handles accept left/right adjustment with the chosen step and Shift for ten steps. Coordinates work with SVG scaling and horizontal scroll. The original view cannot mutate through these controls.

### Requirement: Scoped reversible analysis editing
Undo/redo MUST cover timing, form parameters, add, hide, restore and reset. It MUST preserve source values, copy identity and current server revision. New edits after undo discard redo. Switching objects MUST retain history within the same copy; opening/importing/creating another copy MUST clear it. Save MUST keep history and a clean checkpoint. History is session-only with 100 retained commands.
#### Scenario: Undo after save
Save a changed copy, undo and redo. Values and dirty status return to the matching checkpoint without rewinding server revision. Reload restores saved values, with fresh history.
#### Scenario: Form and branch
Undo a form edit or deletion and restore the same event/parameters. Unhiding an original event preserves its prior analysis timing and parameters. A new edit after undo invalidates redo. Text fields retain native keyboard undo; workspace shortcuts do not intercept typing or modal dialogs.
#### Scenario: Save isolation
An in-flight save disables edits and copy replacement. Failed save retains history and unsaved data. No delayed response overwrites later edits.

### Requirement: Model synchronization remains evidence based
Movement/edge previews and undo/redo MUST use the existing proven time mapping and current object/sequence gates. Unsupported units or times outside the registered clip MUST report the existing gap and MUST NOT invent animation correspondence.
#### Scenario: Supported mapping
Drag/resize an event and observe the model time at the manipulated start/edge; undo/redo seeks the selected restored time. Model context stays within its subject.
#### Scenario: Missing mapping
An event can remain a local analysis hypothesis; preview refuses unsupported correspondence and the original event remains unchanged.
