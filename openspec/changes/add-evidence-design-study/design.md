# Integration design

Use an optional run-local design-study.json overlay keyed by build, package fingerprint, object_id and sequence_id. Backend resolves explicit JSON pointers against registered source bytes and checks SHA256 dependencies; it returns resolved values, provenance and per-fact gaps. A source cannot be chosen by basename or class-name similarity. Bounded declarative calculations support difference and ratio only, with no evaluated expressions.

A dedicated frontend module renders accessible tabs in the existing inspector. Rhythm uses original timeline records and explicit timing_status; source_units are shown as native coordinates but do not claim an animation clock. Values show labeled original fields. Conditions display independent evidence rows rather than guessed sequence arrows or selection probabilities. SVG uses DOM text nodes, not HTML interpolation.

On study event selection reuse setSelection and seekSelectedPreview, including source freshness, preview segment bounds, async context gate and the shared AssetViewer clock. No second animation clock. Fetch study data only on action/context changes or explicit evidence refresh. Cancel stale responses by a monotonic context token.

Local adapters import existing research evidence without modifying source projects. For each selected case preserve native IDs and game build, compare source digests and record missing runtime bindings. Unavailable assets remain visibly unavailable. Large recovery and complete-game extraction remain outside this increment.
