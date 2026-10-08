# OI-0002 Review Candidate

Status: REVIEW_CANDIDATE, NOT ACCEPTED. No real CASE-001 identities, merge, release or external transfer authorized.

Changed modules: identity_persistence.py, identity_permission_adapter.py, test_identity_persistence.py, docs/README.md.

Security: SQLite v1, transactional writes, SHA-256 integrity detection, case-scoped role/fact reads, default-deny callback, Kernel permission_decision adapter, success/denial/integrity audit.

Important boundaries: raw save_identity/load_identity are privileged internal registry operations. Only read_case_identity is suitable for case-scoped callers. Authorization references are not credentials. Kernel manifest/run must be trusted. SQLite is not encrypted; SHA-256 does not prevent malicious replacement of both data and digest; audit table is not independently tamper-evident.

Independent review must verify actual active and expired Kernel manifests, audit trust boundary, deployment filesystem and backup, migration, full regression on exact commit, and T01-T12 evidence. CASE-001 Person A/B remains HUMAN_REQUIRED.

## T01-T12 evidence coverage

- T01: identity persistence, idempotency, restart covered by tests.
- T02: strict primary owner and separate role path covered.
- T03: effective-date boundaries and restart covered.
- T04: overlapping role denied, adjacent non-overlap covered.
- T05: inactive, archived and unresolved identities denied.
- T06: confirmed v1 fact reference binding covered.
- T07: wrong case/year, unconfirmed fact, reused ID and cross-case denial covered; altered artifact lineage needs deeper review.
- T08: replay and transactional rollback covered; crash injection not yet covered.
- T09: scoped case identity read and cross-case denial covered; actual separate deployment roots not tested.
- T10: digest/schema failure and audit covered; independent tamper-evident audit not yet covered.
- T11: unit Regression to be captured from final run.
- T12: real CASE-001 bootstrap deliberately absent, remains HUMAN_REQUIRED.

These are coverage notes, not a claim that all twelve acceptance criteria have passed.

## Kernel integration smoke test

A synthetic ACTIVE manifest for the existing TAX_LAW_AGENT role was registered, validated, and activated in the real OrchestratorKernel with a synthetic Human-owner test authority. Exact case C1/year 2025/run RUN1 read and write capabilities were allowed; cross-case C2 was denied. No live manifest or case was modified. The dedicated test suite passed 22 tests. This does not grant real-world standing authority.
