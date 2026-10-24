# Whole-game study requirements

## ADDED Requirements

### System coverage
WHEN the optional study is present THEN the game workspace presents lifecycle steps and systems spanning preparation, character/controls, relics/progression, equipment/effects, exploration/maps, encounters/cooperation, and rewards/modes. Official descriptions, decoded configuration and analyst hypotheses identify their own evidence class and version applicability.

### Records and references
WHEN searching or opening a row THEN only registered, current, bounded sources are used. Physical ordinal is part of record identity; duplicate native IDs return all candidates. References identify the original field and distinguish exact, ambiguous and absent targets. Unknown/null/zero/false stay distinct. Names from third-party tooling are labeled as annotations.

### Spatial evidence
WHEN projecting coordinates THEN points must share an explicit coordinate frame/group. No route, distance unit, navigation or safe-zone conclusion is inferred from raw positions. A missing transform produces a gap instead of a composed world map.

### Build notebook
WHEN composing a build THEN selections preserve native keys and source fingerprint, mode and party conditions. Direct effect references and repeated selections are reviewable without summing unknown modifiers. Known mode restrictions are shown separately from unresolved color/slot and stacking rules. A/B comparison lists literal changes, with no optimal-build or damage claim. Drafts export/import as bounded JSON and persist only in a fingerprint-scoped local namespace; imported foreign fingerprints are rejected.

### Isolation and failure
WHEN switching table, record, system or workspace THEN late requests cannot overwrite current UI state. Changed evidence invalidates dependent records and relationships. File paths and executable expressions are never accepted from HTTP query parameters. GET uses existing host/origin checks. Freeze retains the overlay and closes over registered dependencies. Legacy runs without study data remain usable.
