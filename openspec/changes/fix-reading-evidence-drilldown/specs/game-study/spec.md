# Evidence drilldown behavior

- Opening a measure shows only its supporting physical rows, using every typed
  predicate and any explicit native ID. Missing fields differ from null; booleans,
  numbers and strings retain their original identities.
- Count and distinct-value measures retain different units. A distinct measure
  opens supporting rows, not a fabricated list with one row per distinct value.
- The fact ID is resolved from the current registered reading. Unknown, changed,
  unsupported or wrong-table facts fail visibly; they never fall back to all rows.
- Pagination, search, refresh and browser history preserve the fact scope. A
  visible control removes it. Changing table or system removes the old scope.
- Return to reading selects the originating chapter and fact. Selecting a native
  row highlights that physical row; leaving the context clears obsolete details.
- Existing source checks, duplicate rows, legacy searches and original action
  workspaces retain their behavior. Unfiltered distribution/projection tools are
  explicitly labeled as whole-table context.
