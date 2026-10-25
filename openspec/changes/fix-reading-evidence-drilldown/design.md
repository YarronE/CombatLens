# Implementation design

Use a bounded `fact` query parameter on the existing rows endpoint. Resolve the
registered reading with its existing evidence checks, find the measure in a
chapter, and require its table to match. Apply its typed where/native predicates
before legacy search and paging. Return its label, chapter, operation, field,
value and resolved conditions as scope metadata. Extend measure scope with an
explicit has_native_id flag so a null native ID differs from no constraint.

The frontend stores fact and focus IDs in the hash. Pure navigation helpers clear
scope and selection on context changes, preserve them for supported paging/search,
and restore the selected evidence on return. A compact block above the rows names
the source statistic, shows exact conditions and provides return/remove actions.
It uses the existing colors and layout. Distinct-value counts display their unit;
the pager continues reporting physical rows. Row buttons carry table/ordinal keys.

Accept with synthetic typed filtering, invalid/stale scope, HTTP, navigation and
race tests plus the existing pilot's filtered statistic, pagination, refresh,
back/return, search and row selection in the browser. Public files contain only
generic contracts and synthetic data. Screenshots and concrete case receipts stay
local. Record measured outcomes without claiming runtime behavior.


Query resolution verifies only the selected measure's source content. Other
facts retain registration checks without loading unrelated tables or returning
partially verified prose. An automated check covers this bounded query behavior.
