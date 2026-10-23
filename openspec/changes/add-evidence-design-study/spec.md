# Design study behavior

## ADDED Requirements

### Three views
WHEN an object/action is selected THEN the inspector offers rhythm, ranges/numbers and phase/selection views, with scoped facts, calculations, hypotheses and gaps. Missing study data leaves the existing workspace usable. Old packages need no migration.

### Evidence and timing
WHEN an event has a verified source and explicitly confirmed coordinate THEN selection goes through the existing event/preview path; only a proven matching preview mapping can seek. Unknown, conflicting, stale or nonfinite coordinates do not move the model. Animation sampling frequency alone never proves a game clock.

### Provenance
WHEN a fact is displayed THEN it identifies its registered source, exact field and unit; zero, false and dynamic values remain distinct. Calculations require compatible known units. Hypotheses reference facts and retain a validation question. Changed evidence invalidates dependent facts and hypotheses.

### Context isolation
WHEN the object, action or workspace changes THEN old asynchronous responses cannot populate the new view. Playback only updates the current event indication; it never rebuilds study charts. Analysis edits are identified as hypotheses and cannot relabel original study facts.

### Local delivery
WHEN a study run is frozen THEN its private study overlay and registered dependencies are retained. Public Git contains generic implementation and synthetic tests only.
