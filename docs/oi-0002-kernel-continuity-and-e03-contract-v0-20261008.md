# OI-0002 Kernel Continuity and E-03 Contract v0
Status: SYNTHETIC_PROTOTYPE / NOT REVIEWED / NOT RELEASED
Authority: Owner limited implementation and synthetic verification, 2026-10-08.

## Kernel continuity transaction contract
- Kernel is the only continuity authority. The current synthetic adapter uses a separately located SQLite file as a stand-in; no production Kernel service integration is claimed.
- Every identity mutation must bind case scope, exact expected epoch/head, new digest and authorized actor/task/manifest; refuse stale epoch/head and existing pending reservations.
- Reserve PENDING in Kernel custody; perform identity transaction; finalize Kernel epoch/head. PENDING after crash must remain fail-closed pending explicit governed reconciliation.
- On restart compare identity persisted epoch/head against Kernel COMMITTED head. Reject older DB+anchor even if internally consistent.
- Kernel head, backups and key custody must be separately protected from identity worker and replaceable identity recovery set. Distinct directories alone are not an ACL boundary.
- Governed restore requires independent Owner approval bound to exact deployment, source backup digest, expected and target epoch/head, operator, expiry and recovery generation. No automatic restore or implicit reset.

## E-03 durable evidence contract
- Current synthetic identity_evidence_authority.py provides metadata-only SQLite append for declaration, confirmation and authorization with exact case, subject and digest parent binding; NOT a verified owner authentication/permission provider.
- Each evidence event must ultimately bind a versioned source provider, authenticated actor identity, tax year, operation, task/manifest, exact document revision, expiry/revocation, immutable audit lineage and one-time authorization consumption where required.
- Existing DurableApprovalStore and in-memory AuditStore do not provide all of these semantics; do not silently treat them as authoritative.
- ProtectedEvidenceResolver must resolve exact case-root ancestry and independently compute current protected content digest through explicitly authorized read-only provider access. Source metadata or user-provided digest alone is insufficient.
- Failure to resolve, revoked evidence, cross-case reference, stale document revision, digest mismatch or ambiguous provider MUST deny authorization.
- No protected document bytes, secret material or taxpayer identifiers in Git, evidence fixtures or logs.

## Current synthetic test coverage and explicit gaps
- C-06 prototype: monotonic epoch/head, pending fail-closed on reopen, same-directory rejection.
- E-03 prototype: persisted declaration/confirmation/authorization chain, duplicate rejection, cross-case and digest mismatch rejection.
- Not implemented: integration into OrchestratorKernel API, Kernel service authentication/ACL, atomic crash recovery reconciliation, independently approved restore, real content verification, Owner authentication, durable revocation/expiry/consumption, independent audit, migrations and broader acceptance tests.
- E-03, C-02, C-06 remain BLOCKED; no REMEDIATION-02, OI-0003, production or real-data execution.
