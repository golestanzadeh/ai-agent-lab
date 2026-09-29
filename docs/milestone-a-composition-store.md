# Milestone A Composition and Store

`MA-02-COMPOSITION-AND-STORE` adds one narrow composition facade and a durable local synthetic workflow journal. The Case Registry remains the sole case-identity authority; the new SQLite store contains only `case_id`, tax year, run identity, stage, artifact identity, and hash-chained transition metadata. It is not a case-data, document, approval, or Orchestrator store.

Transitions are atomic, ordered, idempotent by `transition_id`, and scoped by exact `case_id`/tax year/run identity. Only `SYNTHETIC-*` cases and `RUN-SYNTHETIC-*` runs are accepted. Unknown schema versions, stale stages, transition rebinding, cross-case lookup, and journal/head corruption fail closed. Reopening the same database verifies integrity before returning state.

No provider, credential, network, Gemini, real case data, ERiC engine, submission, or external transfer capability exists in this package.

Verification: focused MA-02 and adjacent suites `39 passed`; full unit regression `883 passed, 1 warning`; independent acceptance `PASS`. Durable Kernel checkpoint `sha256:7434e9ef9fc227ddb6a808629c647644d637d225ecf5524b49f0d5ebb8071663` selects `PKG-MA-03-INTAKE-REVIEW-DECLARATION` next.
