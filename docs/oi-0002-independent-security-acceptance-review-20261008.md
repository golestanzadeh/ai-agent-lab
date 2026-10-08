# OI-0002 independent security and acceptance review

Review date: 2026-10-08  
Reviewer role: independent security and acceptance reviewer  
Reviewed repository: `golestanzadeh/ai-agent-lab`  
Base: `d022-supervisor-loop-design` at `f9117f1ecccfd6995225ab99e2cc8e7748c6b397`  
Review branch target: `oi0002-identity-persistence`  
Reviewed SHA: `90d44a8b0a40ad5a29ffa6d5d7d63db7c3caa10a`  
Recommendation: **FAIL**

The target SHA was exactly the remote review-branch head and was inspected in a clean isolated worktree. The implementation worktree and every pre-existing dirty or untracked file were preserved. No implementation code, protected evidence, CASE-001 identity, external system, merge, release, downstream package, scheduler or Wake was changed or invoked.

Authenticated capacity was accessible at review start: five-hour 100% remaining (reset `2026-10-08T21:47:13Z`) and weekly 75% remaining (reset `2026-10-14T16:57:07Z`). These values are observations, not execution authority.

## Independent security findings

### F01 — HIGH — Active manifests remain authorized after expiry

- Evidence: `src/agent_lab/orchestrator_kernel.py:1223`–`1248`; `src/agent_lab/identity_permission_adapter.py:38`–`45`.
- Observed: `permission_decision()` checks manifest state and Kill Switch but not `expires_at`. The adapter delegates to that method and therefore continues allowing protected reads/writes after an already-active manifest expires.
- Reproduction: register and activate a valid synthetic A3 manifest, confirm `read_party` is allowed, advance the Kernel clock beyond the manifest's exact expiry, then call the same authorization callback. Result: `F5_EXPIRED_MANIFEST_STILL_ALLOWED True`.
- Correction: enforce current UTC expiry inside every `permission_decision()` call, atomically transition expired active manifests to an expired/revoked terminal state, record a tamper-evident audit event, and add active-to-expired read/write adapter tests.

### F02 — HIGH — Privileged raw identity operations bypass Kernel authorization and case scope

- Evidence: `src/agent_lab/identity_persistence.py:146`–`200`.
- Observed: public `save_identity()`, `load_identity()` and `restore_identity()` never call `_check_access()`, require no manifest/run/capability, and are global rather than case-scoped. A comment calling them privileged internal operations is not an enforcement boundary.
- Reproduction: construct `IdentityPersistence` with a default-deny/no authorizer, call `save_identity()` with a synthetic private display value, then call `load_identity()`. Result: `F1_RAW_AUTH_BYPASS True`.
- Correction: place identity lifecycle operations behind an explicit Kernel-authorized registry service with closed create/read/status-transition capabilities, exact trusted actor/run context, least-privilege projections, and audited denial. Keep unsafe storage primitives private and inaccessible to case callers.

### F03 — HIGH — Subject-fact persistence does not preserve or verify the frozen lineage envelope

- Evidence: `src/agent_lab/identity_persistence.py:103`–`110`, `289`–`338`.
- Observed: `subject_fact_binding` stores only request/case/year/subject, one artifact hash and authorization text. It omits semantic key, declaration artifact, confirmation reference, audit lineage, validity interval, revision and schema version. Readback returns hashes without loading the immutable fact or re-verifying confirmation, provenance or content integrity. Membership is sampled only at July 1 (`302`, `323`).
- Reproduction: bind a confirmed v1 fact, close/reopen the store without any fact repository, and call `read_fact_references()`. The hash remains readable although the source fact, confirmation and lineage are unavailable for verification. A role active only on July 1 is sufficient for an annual binding.
- Correction: implement the frozen versioned subject-fact envelope in full, retain an immutable resolvable fact/declaration reference and lineage, validate the relevant effective interval rather than a fixed midpoint, schema-version every row, and fail closed when the referenced fact cannot be loaded and verified.

### F04 — HIGH — Identity lifecycle status is not enforced on reads

- Evidence: `src/agent_lab/identity_persistence.py:253`–`287`.
- Observed: party readback verifies only that the identity exists. `read_case_identity()` returns inactive, archived or unresolved records. No authorized/audited lifecycle transition API exists; storage hashes are unkeyed and can be recomputed by a writer.
- Reproduction: bind an active synthetic spouse, change the stored identity status to `ARCHIVED` with a correspondingly recomputed digest, then perform an authorized case read. Result: `F3_ARCHIVED_READ_ALLOWED True`.
- Correction: add governed immutable lifecycle revisions and enforce `ACTIVE` at every party/fact/identity read and write boundary. Use an integrity authority that a database writer cannot recompute silently.

### F05 — MEDIUM — Conflicting overlapping family roles are accepted across subjects

- Evidence: `src/agent_lab/identity_persistence.py:237`–`244`; submitted coverage at `tests/unit/test_identity_persistence.py:39`–`50` tests overlap only for the same subject.
- Observed: conflict lookup includes `subject_id`, so two different people can simultaneously hold overlapping `SPOUSE_OR_PARTNER` bindings for the same case. Evidence and authorization references are only checked for non-emptiness.
- Reproduction: create P2 and P3, bind both as `SPOUSE_OR_PARTNER` for C1 over the same open interval, and list the parties. Result: `F2_OVERLAPPING_SPOUSES True`.
- Correction: define role-specific cardinality/conflict rules under the frozen party model; reject conflicting same-case/role intervals across subjects unless an explicit governed multi-role rule allows them; validate canonical immutable evidence and authorization references.

### F06 — MEDIUM — Audit and row integrity are not tamper-resistant or complete

- Evidence: `src/agent_lab/identity_persistence.py:29`–`34`, `95`–`130`, `146`–`338`.
- Observed: row digests are plain SHA-256 over data stored beside the digest, so a database writer can replace both. `identity_audit` is an ordinary mutable table with no hash chain, signature, write-once sink or continuity checkpoint. Invalid lifecycle, overlap, fact-scope and lineage attempts are not consistently audited.
- Reproduction: execute valid operations, delete every `identity_audit` row and commit. Reopen/read proceeds without detecting missing history. Result: `F4_AUDIT_TAMPER_UNDETECTED True`.
- Correction: bind rows and append-only audit events to a protected integrity key or independently anchored hash chain; verify continuity on open/read; audit all privileged attempts and validation failures; test deletion, reordering, payload-plus-digest replacement and restart recovery.

### F07 — MEDIUM — Migration, crash recovery and deployment durability remain unproven

- Evidence: `src/agent_lab/identity_persistence.py:61`–`113`; `docs/oi-0002-review-candidate.md:11`–`28`.
- Observed: the adapter creates schema v1 and rejects every other populated schema; it supplies no reviewed migration transaction, backup/restore proof or deployment filesystem control. Transaction rollback is tested, but process/power-loss injection at every party/fact/audit boundary is not.
- Correction: provide explicit forward migration and rollback policy, crash-injection/reopen tests, backup/restore verification, filesystem ACL and non-synced-database deployment evidence, and corruption handling for malformed JSON/dates/enums as well as simple digest changes.

## T01–T12 acceptance matrix

| ID | Expected behavior | Actual observed behavior / evidence | Result | Remaining risk |
| --- | --- | --- | --- | --- |
| T01 | Two identities persist with stable IDs/digests across restart. | Submitted restart tests pass; independent regression passes. | PASS | Raw global reads/writes lack authorization (F02). |
| T02 | Owner association remains strict; spouse uses explicit role path. | Wrong owner is rejected and spouse role is separate. | PASS | Role path still has conflict/evidence weaknesses (F05). |
| T03 | 2024/2025 role history, boundaries and open intervals are correct. | Half-open boundary and restart behavior pass. | PASS | No governed lifecycle-revision API. |
| T04 | Conflicting overlapping same-case roles fail closed; corrections preserve history. | Different subjects can hold overlapping spouse roles; evidence refs may be arbitrary strings. | FAIL | Family topology can be contradictory. |
| T05 | Unknown, ambiguous, archived/unresolved identities and owner mismatch fail closed. | Initial non-active binding and owner mismatch reject, but archived identity is returned after status change. | FAIL | Lifecycle status is not enforced on reads (F04). |
| T06 | Confirmed v1 fact binds to exact subject without changing original digest. | Original digest is retained, but the required versioned lineage envelope is not persisted or verifiable after restart. | FAIL | Confirmation/provenance/content cannot be reconstructed (F03). |
| T07 | Wrong scope/subject/state/digest and changed replay fail closed. | Basic negative tests pass; altered/unavailable source fact after registration is not reverified and July-1 membership is insufficient. | FAIL | Stored hash can outlive its trust evidence (F03). |
| T08 | Replay is idempotent and crashes cannot create orphaned rows. | Idempotency and ordinary transaction rollback pass; crash/power-loss boundaries were not executed. | BLOCKED | Atomic recovery across row/audit boundaries is unproven (F07). |
| T09 | Shared subjects remain isolated by exact case authorization and storage root. | Synthetic cross-case reads deny through the callback and distinct roots are checked. | PASS | Database rows do not persist the root identity; deployment proof remains needed. |
| T10 | Corruption/schema/lineage failures block readback and are durably audited. | Simple digest/schema changes reject, but audit is mutable, lineage is incomplete, and no migration exists. | FAIL | Malicious replacement/deletion and malformed rows are not durably detectable (F03/F06/F07). |
| T11 | Legacy identity/case/fact/tax regressions remain green and accepted identities unchanged. | Full unit suite: 1080 passed, 5 skipped; diff is limited to candidate modules/tests/docs. | PASS | Passing regression does not cover the new security defects. |
| T12 | Real CASE-001 Person A/B bootstrap remains HUMAN_REQUIRED; no identities fabricated. | No live identity was created; candidate explicitly retains the Human Gate. | PASS | OI-0003 and later stages remain blocked. |

Overall: 6 PASS, 5 FAIL, 1 BLOCKED. OI-0002 is not acceptable.

## Regression and review evidence

All commands ran at reviewed SHA `90d44a8b0a40ad5a29ffa6d5d7d63db7c3caa10a` in a clean isolated worktree.

1. Focused security/persistence/Kernel regression:
   - Command: `PYTHONPATH=src python -m pytest tests/unit/test_identity_persistence.py tests/unit/test_orchestrator_kernel.py tests/unit/test_person_entity_registry.py tests/unit/test_case_identity_association.py tests/unit/test_human_declared_fact.py tests/unit/test_durable_approval.py -q`
   - Result: 88 passed; exit code 0; 11.20 seconds.
2. Complete unit regression:
   - Command: `PYTHONPATH=src python -m pytest tests/unit -q`
   - Result: 1080 passed, 5 skipped; exit code 0; 236.04 seconds.
3. Independent in-memory/temp-SQLite adversarial probe:
   - Result: all five attempted violations reproduced: raw authorization bypass, overlapping spouse roles, archived identity read, audit deletion, and post-expiry manifest authorization.
   - Exit code: 0. No repository or protected artifact was mutated.

## Remediation order

1. F01: enforce manifest expiry at every Kernel permission decision and add expired read/write tests.
2. F02: remove or strictly encapsulate unauthenticated global identity operations behind real Kernel capabilities.
3. F03: implement and verify the complete immutable subject-fact lineage envelope and effective-period semantics.
4. F04: add governed identity lifecycle revisions and enforce active status on every read/write.
5. F05: implement cross-subject role-conflict/cardinality and canonical evidence validation.
6. F06: add independently anchored, append-only audit/integrity verification and complete security-event coverage.
7. F07: provide migration, crash, backup/restore and protected deployment evidence.

## Final handoff

Recommendation: **FAIL**. Return the findings to the OI-0002 implementation worker. Remediation must produce a new commit; a separate independent review must inspect that new exact SHA. Keep OI-0002 OPEN. Do not start OI-0003, merge, release or execute external actions.
