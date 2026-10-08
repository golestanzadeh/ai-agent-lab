# OI-0002 conditions verification gate

Gate ID: `OI-0002-CONDITIONS-VERIFICATION-GATE`  
Owner record: `ODR-OI0002-OWNER-DISPOSITION-20261008`  
Reviewed head: `2cb049eb57934657cdddf8a1747546270efe925b`  
Status: `BLOCKED / CONDITIONAL_RELEASE_NOT_READY`

## Evidence-provider/type mapping

| Artifact type | Existing candidate authority | Immutable identity and verification | Assessment |
|---|---|---|---|
| Owner declaration | Protected CASE-001 artifact location plus Case Registry root | Exact content SHA-256, explicit protected object identity, case/year/subject/semantic-key/revision | `BLOCKED`: protected files exist, but no approved durable service resolves this general artifact type after restart. |
| Owner confirmation | `HumanDeclaredFact` confirmation state | Separate confirmation record must bind declaration digest, Owner actor, scope, purpose, time and non-revocation | `BLOCKED`: the embedded enum is not an independently durable confirmation authority. |
| Identity authorization | `DurableApprovalStore` pattern | Exact approval identity/status/expiry/consumption bound to identity operation and Kernel context | `BLOCKED`: the current durable store supports migration/submission domains, not identity administration. It must not be relabelled as authoritative. |
| Audit lineage | identity audit plus `AuditStore`/durable-approval audit patterns | Exact event identity, operation, actor/manifest/task/run, inputs/outputs and continuity head | `BLOCKED`: general `AuditStore` is in-memory; identity audit lacks the independently released continuity boundary. |
| Supporting protected document | Case Registry, `CaseScopedDriveResolver`, `GoogleDriveMetadataAdapter`, `DocumentIdentityRegistry` | Explicit provider object ID, case-root ancestry, active status and content SHA-256 | `BLOCKED`: metadata/ancestry exist, but the adapter cannot retrieve and verify content digest and the registry is snapshot-based. |

Approved target mapping: one `ProtectedEvidenceResolver` composes these services and a metadata-only index inside the existing OI-0002 SQLite deployment. It may dispatch only to a provider explicitly registered for the artifact type. No fallback provider, digest-only proof, broad search or protected-content copy is permitted. Until the blocked authorities above exist under approved contracts, evidence-dependent implementation is not released.

## Evidence resolver trust boundary

For every lookup the resolver must require exact artifact type, immutable reference, provider/object ID, case, year, run, storage root, subject, semantic key, interval and revision. It verifies case/root first, explicit object availability/ancestry second, content identity third, then confirmation/authorization/audit bindings. A changed, missing, unavailable, revoked, mismatched, superseded or cross-case object returns one closed failure and security audit event. Restart repeats the complete resolution; cached syntax or prior success is never authority.

The metadata index contains only opaque provider identity, hashes, scope, version/status and lineage references. Taxpayer content, personal values, credentials and keys remain in protected authorities outside Git. `DocumentIdentityRegistry`, `InventoryEvidenceStore` and `AuditStore` cannot be called durable authorities until their persistence and integrity boundaries are explicitly implemented and reviewed.

## Kernel continuity and separate custody

The approved target boundary is an `IdentityContinuityAuthority` broker owned by the existing Kernel store, physically and logically outside the identity database/anchor recovery set. Its record contains deployment ID, monotonic epoch, previous/current audit head, schema and restore generation, reservation state, exact scoped operation and timestamps. Only Kernel compare-and-swap may mutate it.

Protocol: reserve expected epoch/head in Kernel → commit identity rows/audit/epoch in one transaction → verify and finalize in Kernel. Restart accepts only exact committed equality. An exact pending reservation may finalize only if the database matches; otherwise all access stops for governed recovery. Authority/key unavailability denies every identity read/write. Kernel state, key material and identity backups have distinct owners, paths, service accounts, ACLs and backup sets.

Required operational records before release: canonical deployment IDs and absolute protected roots; identity-service and Kernel-service accounts; ACL read/write matrices; HMAC key provider/reference, rotation and recovery roles; separate backup inventories/retention; crash-reconciliation operator; and evidence that the identity backup cannot overwrite Kernel continuity or key custody. None of these protected values belongs in Git.

## Governed restore procedure

1. Stop identity access and preserve current database, anchor and Kernel continuity evidence.
2. Verify an explicit, expiring Owner restore approval bound to deployment ID, backup identity/digest, expected current epoch/head, source epoch/head, target restore generation, operator and purpose.
3. Kernel reserves a new monotonic restore generation; it never decrements epoch.
4. Restore database/anchor in staging, verify schema, HMAC, audit, evidence references and backup identity, then atomically place it.
5. Write a new identity restore audit event/head at the reserved generation; Kernel verifies and finalizes it.
6. Reopen and independently verify exact equality. On any mismatch or unavailable authority, retain the pre-restore state and fail closed.

Possession of files, an ordinary backup approval or identity-service permission never grants restore. A rollback of the Kernel authority/key store is outside the identity recovery threat boundary and is a security incident requiring separate control-plane recovery and independent review.

## Condition assessment

| Condition | Result | Evidence / remaining requirement |
|---|---|---|
| E-01 reuse existing services | PASS (architecture) | Single composition adapter; no parallel repository. |
| E-02 metadata-only persistence | PASS (architecture) | Same SQLite index; protected content excluded. |
| E-03 explicit provider mappings | BLOCKED | General declaration, confirmation, identity authorization and durable audit authorities do not yet exist; content verification is absent. |
| E-04 independent verification | PASS (specification) | Exact lookup and binding algorithm specified; implementation not authorized. |
| E-05 fail closed | PASS (specification) | Closed outcomes and restart behavior specified. |
| E-06 reviewable evidence | PASS (documentation) | Mapping, boundaries and acceptance requirements are explicit. |
| C-01 independent trust boundary | PASS (architecture) | Existing Kernel store is the sole proposed continuity authority. |
| C-02 separate custody | BLOCKED | Actual service accounts, ACLs, key provider and separate backup evidence are unavailable. |
| C-03 reservation/finalization | PASS (specification) | Epoch/head protocol and crash outcomes are explicit. |
| C-04 governed restore | PASS (specification) | Exact Owner-bound restore procedure specified. |
| C-05 anti-rollback verification | PASS (specification) | Old database/anchor rejects against Kernel; remaining Kernel-compromise threat stated. |
| C-06 operational evidence | BLOCKED | Custody, ACL, key management and recovery evidence has not been produced or assessed. |

These PASS values accept the architecture/documentation only. They do not claim implemented or operational controls.

## Bounded remediation-02 plan

After conditional release only: version the already approved F02 contracts; implement the released evidence authorities/resolver; implement Kernel continuity; implement immutable role corrections; replace v1 migration with one transaction or verified atomic swap; preserve F01/F04; execute adversarial, crash, T01-T12, focused/relevant/full/documentation tests; publish `REVIEW_READY`; obtain a separate independent review.

## Decision and continuation

Recommendation: **DO NOT AUTHORIZE REMEDIATION-02 YET**. E-03, C-02 and C-06 are unresolved. The next authorized action is an Owner/governance decision that either (a) authorizes bounded creation/extension of the missing durable declaration, confirmation, identity-approval, audit/content-verification authorities and supplies/approves the separate-custody operational plan, or (b) selects already authorized concrete providers and supplies their evidence. Only the Owner may release the conditional approvals after those records are reviewed.

OI-0002 remains OPEN; remediation-02 and OI-0003 remain BLOCKED. No implementation, protected-data access, external action or production activation occurred.

## Capacity handoff

- Authenticated ending observation at `2026-10-08T18:18:36Z`: five-hour 21% remaining, reset `2026-10-08T21:47:13Z`; weekly 63% remaining, reset `2026-10-14T16:57:07Z`.
- Source: signed-in Codex account rate-limit service. Readback was unambiguous and remained above the 15-point reserve; no reset credit was used.
