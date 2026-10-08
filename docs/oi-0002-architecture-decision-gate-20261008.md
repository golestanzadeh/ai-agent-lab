# OI-0002 architecture decision gate

Gate ID: `OI-0002-ARCHITECTURE-DECISION-GATE`  
Date: 2026-10-08  
Reviewed implementation SHA: `ad263284ff211d6d7d75234c03c3005d43b7d2df`  
Review-02 evidence commit: `fad333d732b2d0c8cbe4c0f39b90f78b9960d117`  
Status: `HUMAN_REQUIRED / ARCHITECTURE_DECISIONS_PENDING`  
Scope: architecture and governance only; no implementation or frozen-contract change

## Recovery and governing constraints

The exact implementation and reporting commits were verified. The current Kernel contracts, role catalog, identity adapter, protected storage adapters, evidence/approval/audit services, OI-0002 frozen design, both independent reviews and remediation evidence were inspected from a clean isolated worktree. OI-0002 remains OPEN. F01 and F04 remain independently verified PASS and must be preserved.

Authenticated admission capacity was 36% five-hour and 65% weekly remaining. This bounded documentation task preserves the 15-point five-hour reserve.

## F02 — identity administration authority

Root cause: `identity_permission_adapter.py` maps every lifecycle mutation to `write_derived_case_artifact` and identity reads to `read_derived_case_artifact`. Those generic capabilities belong to ordinary tax-analysis roles, including `TAX_LAW_AGENT`. The frozen Permission Matrix has no identity-administration permission or role.

### Proposed minimum authority contract

Add these narrowly defined capabilities in a versioned successor to the frozen Permission Matrix:

| Capability | Maximum tier | Required scope | Meaning |
|---|---:|---|---|
| `identity_create` | A4 | case, tax year, run, storage root | Create one unresolved/active identity through the registry service only. |
| `identity_read` | A3 | case, tax year, run, storage root | Read the minimum identity projection required for administration. |
| `identity_update` | A4 | case, tax year, run, storage root | Append an immutable non-status identity revision. |
| `identity_status_transition` | A4 | case, tax year, run, storage root | Execute an allowed lifecycle transition with reason/evidence. |
| `case_party_bind` | A4 | case, tax year, run, storage root | Create or correct an effective-dated party role. |
| `subject_fact_bind` | A4 | case, tax year, run, storage root | Bind a verified subject fact envelope. |

Create a dedicated `IDENTITY_ADMINISTRATION_AGENT` service role with only the six capabilities above plus `request_human_gate`. It is dispatched by the existing `CASE_ORCHESTRATOR_AGENT` for an exact registered task and short-lived manifest. Ordinary tax agents receive no lifecycle capability. They consume a case-scoped derived projection produced by the service; `read_derived_case_artifact` never authorizes raw identity administration.

Every decision requires the exact manifest actor, task, run, case, tax year and storage root. Missing context, unknown action, capability mismatch, expired/revoked manifest, Kill Switch, inactive identity or case/root mismatch resolves to DENY. Create/update/status/bind events record actor, manifest, task, run, old/new revision, evidence/authorization identities and the Kernel decision. Revocation applies at each decision, preserving F01.

Compatibility: existing Kernel manifest validation and `permission_decision()` remain the enforcement point. The adapter changes from generic capability translation to a closed action-to-dedicated-capability map. No parallel authority is introduced.

Classification: `OWNER_APPROVAL_REQUIRED`. Adding capabilities and a service role changes the frozen Permission Matrix and role catalog and triggers the existing `permission_expansion` Human Gate.

## F03 — immutable evidence resolution

Root cause: identity persistence validates only `sha256:` syntax. Existing components establish useful pieces but no single durable resolver proves that a declaration, confirmation, authorization or audit object exists and matches subject/case/year/semantic-key/revision after restart.

### Reusable infrastructure

- `CaseRegistry` and `CaseScopedDriveResolver`: exact case and protected root.
- `GoogleDriveMetadataAdapter`: explicit object lookup and deterministic ancestry; no broad search.
- `DocumentIdentityRegistry`: provider/object identity, case scope, observations and content fingerprint, but currently snapshot-based rather than a complete durable evidence authority.
- `InventoryEvidenceStore`: case/run evidence links, currently in-memory.
- `DurableApprovalStore`: durable case/run approval and audit records for its accepted approval domains; not a generic Owner-declaration authority.
- `AuditStore`, `ArtifactIdentity`, `HumanDeclaredFact`: audit/domain identity and canonical payload primitives.

### Proposed evidence-resolution contract

Introduce one `ProtectedEvidenceResolver` adapter, not another repository. It composes the existing Case Registry, case-scoped storage adapter, document identity metadata, durable approval/audit services and the same authoritative OI-0002 SQLite deployment.

The same database may add a metadata-only `immutable_evidence_index` table keyed by immutable artifact reference. Each record contains: schema/type/version; content SHA-256; provider and opaque object identity; exact case, tax year, run and storage root; subject type/id; semantic key; effective interval; revision and predecessor; confirmation state/reference; authorization reference; audit reference; and lifecycle status. Protected document content remains in the protected case root and never enters Git or the metadata database.

Resolution must:

1. resolve the case through Case Registry and require exact year/run/root;
2. load the indexed immutable metadata and obtain the protected object by explicit object identity only;
3. verify ancestry, availability/status and content digest;
4. verify subject, semantic key, interval, revision/predecessor and declaration binding;
5. resolve confirmation/authorization through their designated durable authority and require exact actor, scope, purpose, status and non-revocation;
6. resolve audit lineage and require the referenced event to cover the same operation;
7. repeat these checks after restart and before every read/bind.

Missing, unavailable, changed, mismatched, superseded, revoked, cross-case or unresolvable objects fail closed and emit a security audit event without copying protected content. A syntactically valid digest is never sufficient.

Unresolved prerequisite: the repository contains no approved general-purpose durable Owner-declaration/confirmation authority and no approved mapping of declaration/confirmation artifact types to authoritative protected providers. The Owner must designate that authority and permit the metadata index in the existing SQLite deployment. Real evidence registration remains a later Human Gate.

Classification: `OWNER_APPROVAL_REQUIRED`. The adapter reuses existing boundaries, but designating authoritative evidence/confirmation sources and extending the frozen persistence schema are governance decisions.

## F06 — independent anti-rollback boundary

Root cause: the database and `.audit-anchor` belong to one replaceable recovery set. HMAC authenticates content but provides no freshness when both are restored to an older valid state.

### Proposed minimal compatible mechanism

Use the existing Deterministic Orchestrator Kernel control-plane store as the independent continuity authority through a narrow `IdentityContinuityAuthority` interface. Do not add a second orchestrator, cloud service or identity database.

The Kernel-owned record is outside the identity SQLite recovery set and contains deployment ID, monotonic epoch, audit head, previous head, database schema generation, backup/restore generation, operation state and timestamp. Only a dedicated Kernel broker action may compare-and-swap it. The identity service cannot rewrite or recreate continuity state.

Commit protocol:

1. Kernel authorizes the exact scoped operation and reserves epoch `n+1` with expected prior head (`PENDING`).
2. The identity transaction writes its rows, audit event, reserved epoch and new head atomically.
3. Kernel verifies the committed identity head and finalizes the reservation (`COMMITTED`).
4. On restart, identity state must equal the Kernel's committed state. A pending reservation is reconciled only when the exact database epoch/head matches; otherwise access fails closed for controlled recovery.

An old database-plus-anchor pair will carry an older epoch/head than the Kernel continuity record and be rejected. The sidecar becomes a local crash hint, not the freshness trust root. Kernel continuity state and the protected HMAC key must not be included in the identity backup set.

Backup/restore requires an exact, expiring Owner-approved restore authorization bound to deployment, backup identity, expected source epoch/head, target generation and operator. Restore never decrements the Kernel epoch: after verification it commits a new restore generation/head. If the Kernel continuity authority or protected key is unavailable, all identity reads/writes fail closed; offline bypass is forbidden.

Local-first compatibility: the interface initially uses the existing local Kernel store with separate OS ACL, backup policy and service account. A future cloud control-plane implementation may supply the same compare-and-swap interface only after separate authorization. The threat boundary protects against identity-database writers and replacement of the identity recovery set; compromise/rollback of the Kernel authority or key store remains an operational incident requiring independent recovery evidence.

Classification: `OWNER_APPROVAL_REQUIRED`. Adding a Kernel continuity broker/state and restore authorization policy changes the accepted control-plane contract, even though it reuses the existing Kernel and introduces no new service.

## F05 — effective-dated role correction requirements

Root cause: role insertion enforces overlap but no immutable operation can close/correct an open interval. Evidence references are not resolved.

Required implementation:

- Add a Kernel-authorized `correct_case_party_binding` operation under `case_party_bind`.
- Never update/delete the original binding. Append a correction revision with predecessor binding/revision, correction reason, effective closing date, verified evidence/authorization and audit event.
- Materialize the effective timeline from immutable revisions; require strictly monotonic revision, same case/subject/role, `valid_from < corrected_valid_to_exclusive`, and no gaps/conflicts introduced by the correction plus successor.
- Apply cardinality to the resulting timeline across all subjects. Same-day half-open closure/successor is permitted; overlap, backdating beyond evidence, changed predecessor, duplicate request and cross-case substitution fail closed.
- Open-ended closure, adjacent replacement, correction replay, competing corrections, evidence revocation, restart and history preservation require tests.

Affected modules: `identity_persistence.py`, `identity_permission_adapter.py`, persistence schema/migration and identity tests. Dependency: approved F02 capability contract and F03 resolver.

Classification: `WITHIN_EXISTING_AUTHORITY` once F02/F03 are approved. Immutable effective-dated corrections are already required by the frozen OI-0002 design; no role semantics are expanded.

## F07 — atomic migration requirements

Root cause: v1 table deletion commits before v2 schema creation/insertion, so a crash can destroy the legacy schema.

Required implementation:

- Prefer one SQLite `BEGIN IMMEDIATE` transaction: validate all legacy rows, create versioned shadow tables, copy/transform, verify counts/digests/foreign references, swap table names, update `user_version`, create continuity/audit records, then commit once.
- If platform constraints prevent a safe transactional swap, use a same-filesystem staged database: immutable source backup, copy and migrate, full verification, fsync file and parent directory, then atomic replace; retain the source until post-restart verification.
- Never drop or mutate the only accepted legacy copy before a verified successor exists. Unsupported/nonempty v1 fact lineage remains fail-closed and Human-gated.
- Inject crashes before/after validation, each table copy, verification, swap, `user_version`, commit/finalization and first reopen. Every point must yield either intact v1 or fully verified v2, never a mixed/empty state.
- Test corrupt JSON/date/enum/digest, disk-full/I/O failure, retry/idempotency, backup restore, WAL/SHM handling, wrong schema and continuity-authority outage.

Affected modules: `identity_persistence.py`, migration helpers, operations guide and identity tests. Regression risks: v1 compatibility, audit continuity, F01/F04 behavior, restart and backup/restore.

Classification: `WITHIN_EXISTING_AUTHORITY`. This corrects an implementation defect without changing the frozen persistence choice; nonempty lineage migration remains a separate Human Gate.

## Decision matrix

| Finding | Existing reuse | Minimal correction | Frozen-contract impact | Security consequence | Tests / dependency | Classification |
|---|---|---|---|---|---|---|
| F02 | Kernel manifests, exact scope, expiry/revocation | Dedicated capabilities and service role | Permission Matrix and role catalog successor | Removes tax-agent lifecycle privilege | Capability/role/scope/expiry/revocation; precedes F03/F05 | `OWNER_APPROVAL_REQUIRED` |
| F03 | Case/Drive resolver, document identity, durable approval/audit, ArtifactIdentity | Composite resolver plus metadata index in same SQLite | Designation of evidence authorities and schema extension | Eliminates fabricated/unresolved lineage | Missing/changed/mismatched/revoked/restart; depends F02 | `OWNER_APPROVAL_REQUIRED` |
| F05 | Effective-dated binding and overlap engine | Immutable correction revisions | Implements existing frozen requirement | Maintains valid history without bypassing cardinality | Boundary/concurrency/replay/history; depends F02/F03 | `WITHIN_EXISTING_AUTHORITY` |
| F06 | Kernel store, HMAC audit head, approval model | Kernel-owned monotonic continuity broker | Kernel control-plane/restore contract extension | Detects old valid recovery-set rollback | two-phase crash/rollback/restore/outage; precedes final backup tests | `OWNER_APPROVAL_REQUIRED` |
| F07 | SQLite transactions, schema versioning, backup | Single transaction or verified atomic swap | No frozen design change | Prevents destructive partial migration | phase-by-phase crash/corruption/retry; depends F06 for final continuity | `WITHIN_EXISTING_AUTHORITY` |

## Exact Owner Decision Requests

No implementation may start until the Owner answers all three requests explicitly.

1. **ODR-OI0002-02-PERMISSIONS:** Approve a versioned successor to the frozen Permission Matrix and role catalog containing the six dedicated identity capabilities and `IDENTITY_ADMINISTRATION_AGENT` boundary specified above; explicitly deny those capabilities to `TAX_LAW_AGENT` and every ordinary tax-analysis role.
2. **ODR-OI0002-03-EVIDENCE:** Approve `ProtectedEvidenceResolver` as the single composition layer over the existing case-scoped protected storage, identity metadata and durable approval/audit authorities; approve the metadata-only immutable evidence index in the existing OI-0002 SQLite deployment; designate the authoritative provider/type mappings for declarations, Owner confirmations, authorizations and audit records. No protected content enters Git.
3. **ODR-OI0002-06-CONTINUITY:** Approve the existing Kernel control-plane store as the independent monotonic continuity authority, the reservation/finalization protocol, separate custody from identity backups, and exact Owner-approved restore authorization. This approval does not authorize production activation or any cloud service.

If any request is declined or materially altered, return to architecture review. Silence is not approval.

## Proposed OI-0002-REMEDIATION-02 sequence

1. Record the three Owner decisions; version the affected contracts only as approved, with contract tests.
2. Implement F02 dedicated Kernel capability mapping and denial/audit coverage.
3. Implement F03 resolver/index against synthetic protected fixtures; no real CASE-001 evidence.
4. Implement F06 Kernel continuity broker and fail-closed two-phase recovery.
5. Implement F05 immutable role corrections using the approved authority and resolver.
6. Implement F07 atomic migration and crash matrix, then update operations documentation.
7. Run F01/F04 preservation tests, all F02/F03/F05/F06/F07 adversarial probes, T01-T12, relevant and complete regression.
8. Publish one exact `REVIEW_READY` commit and obtain a new separate independent review. Do not start OI-0003.

## Acceptance criteria

- **F02:** only a valid dedicated service manifest can invoke each lifecycle operation; generic derived-artifact roles, missing context, wrong scope, expiry, revocation and Kill Switch always deny and audit.
- **F03:** every required lineage object resolves through its designated authority and binds exact content, subject, case, year, semantic key, interval and revision after restart; absence or mismatch always denies.
- **F05:** immutable revisions close/correct open intervals while preserving original history and enforcing cardinality across subjects at exact boundaries.
- **F06:** restoring any older valid identity database/anchor pair is rejected against independent Kernel continuity; crash reconciliation never silently loses or advances history; unauthorized restore is impossible.
- **F07:** every injected migration interruption yields intact v1 or fully verified v2, and unsupported legacy lineage remains preserved and blocked rather than destroyed.
- F01/F04 remain PASS; T01-T12, focused, relevant, complete and documentation regressions pass; a separate reviewer independently reproduces the security invariants.

## Continuation

Current state is `HUMAN_REQUIRED / ARCHITECTURE_DECISIONS_PENDING`. The exact next authorized action is Owner disposition of ODR-OI0002-02-PERMISSIONS, ODR-OI0002-03-EVIDENCE and ODR-OI0002-06-CONTINUITY. `OI-0002-REMEDIATION-02` must not begin before all required approvals are durable. OI-0002 remains OPEN; OI-0003 and downstream work remain blocked.

## Capacity handoff

- Authenticated ending observation at `2026-10-08T18:02:28Z`: five-hour 28% remaining, reset `2026-10-08T21:47:13Z`; weekly 64% remaining, reset `2026-10-14T16:57:07Z`.
- Source: signed-in Codex account rate-limit service. The result was read back unambiguously and remained above the mandatory reserve; no reset credit was used.
