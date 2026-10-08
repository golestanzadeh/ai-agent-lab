# OI-0002 Missing Authority and Custody Preparation
Date: 2026-10-08
Status: DESIGN_PREPARED / CONDITIONAL_RELEASE_NOT_READY
Authority: Owner-approved design and preparation only; no REMEDIATION-02 implementation, real taxpayer access, production activation, or condition release.
Implementation baseline: ad263284ff211d6d7d75234c03c3005d43b7d2df
Owner decision: docs/oi-0002-owner-architecture-decision-20261008.md
Conditions gate: docs/oi-0002-conditions-verification-gate-20261008.md

## Confirmed source inspection (read-only)
- src/agent_lab/durable_approval.py: SQLite-backed migration/submission approval domains; NOT an identity-authorization authority.
- src/agent_lab/approval.py: IntendedOperation currently contains PHYSICAL_MIGRATION; identity authorization needs separately governed versioned contract.
- src/agent_lab/audit.py: AuditStore uses process-local dict; NOT durable general audit authority.
- src/agent_lab/document_identity.py: source observations and registry exist, but metadata observations do not prove current protected-content digest.
- src/agent_lab/case_scoped_drive.py: case-root scope resolver exists; object ancestry and content verification need separate authoritative checks.
- src/agent_lab/orchestrator_kernel.py: SQLite-backed deterministic Kernel; proposed independent continuity control plane must extend this existing authority, not synthetic continuity.
- src/agent_lab/orchestrator_continuity.py: explicitly synthetic local continuity proof, not operational IdentityContinuityAuthority.
- src/agent_lab/identity_persistence.py: anchor path is database path plus .audit-anchor, same recovery directory; independently rolled-back DB+anchor is not detected.
- Windows observation: inspection executed as desktop-hvruqb7\\rezag; Docker Windows service was Stopped when checked. Neither fact proves actual runtime service-account topology.

## E-03: bounded target provider contracts (DESIGN ONLY)
1. OwnerDeclarationAuthority: durable immutable declaration record ID, exact provider object ID, content SHA-256, case/year/subject/semantic key/revision, owner actor and timestamp; signed/authorized creation; revocation/supersession.
2. OwnerConfirmationAuthority: distinct durable confirmation event binding exact declaration revision/digest, actor, scope, purpose, expiry and revocation; never infer confirmation from HumanDeclaredFact enum.
3. IdentityAuthorizationAuthority: extend existing DurableApprovalStore with explicitly versioned identity-operation domain, exact Kernel manifest/task/run, one-time consumption, expiry, revocation and audit; no reuse of PHYSICAL_MIGRATION.
4. DurableIdentityAudit: append-only identity-specific event chain in existing OI-0002 SQLite plus independent Kernel epoch/head. Existing in-memory AuditStore is not sufficient.
5. ProtectedContentVerifier: compose existing CaseRegistry, CaseScopedDriveResolver, GoogleDriveMetadataAdapter and DocumentIdentityRegistry; verify exact case-root ancestry and actual current protected object bytes/digest under explicitly authorized protected access. Never claim metadata-only digest proves content.
6. ProtectedEvidenceResolver: exact type-to-provider dispatch, no fallback; fail closed on missing, stale, cross-case, revoked, mismatched, unverifiable, or restart-unresolvable evidence. Persist only opaque metadata index in existing SQLite; no protected content in Git.

## C-02: deployment/custody evidence checklist (NOT YET VERIFIED)
- Identify canonical development deployment ID and absolute paths for Kernel DB, identity DB and anchor, without reading taxpayer rows.
- Determine actual runtime process/service identities and whether Kernel and identity are separately privileged. Interactive account is not proof.
- Collect redacted ACL matrix for each protected root; identity worker must not modify Kernel epoch/head or its backup.
- Specify OS secret provider, HMAC key reference, creation/rotation/recovery ownership. Do not read, log or commit key material.
- Inventory distinct backup roots and restore permissions for identity DB, Kernel control plane and key custody; demonstrate identity backup cannot overwrite Kernel/key.
- Define separate development/test versus production gate; no implied production readiness.

## C-06: operational proof and recovery (NOT YET VERIFIED)
- Create synthetic-only deployment/custody inventory, redacted ACL readbacks and operator responsibilities.
- Run synthetic crash points: before reserve, after pending reserve, after identity commit, before Kernel finalize, after finalize; verify fail-closed and reconciliation.
- Attempt rollback of old valid identity DB+anchor against newer Kernel epoch; must reject.
- Governed restore requires independent expiring Owner approval bound to deployment, backup digest, expected epoch/head, source epoch/head, restore generation, operator and purpose.
- Prove backup and key separation and document operational incident response; no live restore or protected-data inspection.

## Owner/governance decision still required
Authorize bounded creation or extension of the five missing evidence authority functions above under versioned successor contracts and approve the concrete redacted service-account/ACL/key/backup custody plan. This design-preparation authorization is NOT such implementation or operational approval.

## Release rule
E-03, C-02, C-06 remain BLOCKED. Design document existence is not PASS. No remediation implementation until conditions are independently verified and Owner explicitly releases the conditional gates. OI-0002 OPEN; OI-0003 BLOCKED.

## Read-only Windows evidence verification (2026-10-08)
Scope: existing authorized workstation DESKTOP-HVRUQB7; no taxpayer records, secrets, task action arguments or database rows accessed. Read-only source and configuration metadata only.

### Step 1: deployment roots and identity/Kernel persistence
- Git implementation worktree C:\\Users\\rezag\\ai-agent-lab-oi0002-implementation at ad263284ff211d6d7d75234c03c3005d43b7d2df; only this preparation document is untracked.
- Main repository C:\\Users\\rezag\\ai-agent-lab exists. C:\\ProgramData\\ai-agent-lab and C:\\Users\\rezag\\AppData\\Local\\ai-agent-lab do not exist at inspected paths. Absence at those paths does NOT establish absence elsewhere.
- IdentityPersistence receives runtime SQLite path and HMAC integrity_key from its caller; creates .audit-anchor alongside SQLite. backup_to() copies SQLite and companion anchor, not an independently controlled Kernel head.
- OrchestratorKernel receives runtime database_path from its caller; no canonical active deployment DB path was established by this inspection. No .db/.sqlite files at either inspected repository top level. No claim of global absence.
- RESULT: implementation paths understood; canonical active deployment IDs, DB paths, independent Kernel head path and backup roots NOT VERIFIED.

### Step 2: actual service identities and NTFS ACL
- Current inspection principal desktop-hvruqb7\\rezag.
- Scheduled tasks AI-Tax-Agent Local Sync (Ready), AI-Tax-Agent Tunnel (Running), AI-Tax-Agent Windows Relay (Ready) all show RunAs=rezag and LogonType=Interactive. These are project-related tasks, not proof of dedicated Kernel/identity services.
- Implementation worktree root inherited NTFS Allow FullControl for SYSTEM, Administrators and desktop-hvruqb7\\rezag.
- Main repository root additionally has Modify for CodexSandboxUsers and two unresolved SIDs; current user, Administrators and SYSTEM retain FullControl. SID ownership was not inferred.
- No independent Kernel service principal or protected root with separate ACL was verified. Do not change ACLs until exact deployment roots, required access and recovery accounts are approved.
- RESULT: C-02 BLOCKED. A worktree root is not a protected continuity authority.

### Step 3: backup/key custody
- No project-related HMAC/SECRET/BACKUP/KERNEL/IDENTITY environment variable names were returned from the current process environment; absence here does not prove absence in other providers.
- No .db/.sqlite/.bak files were found at the inspected main repository top level, and no such files at implementation repository top level.
- Scheduled tasks with generic Backup names exist on Windows, but they were not attributed to this project and are NOT accepted as project backup evidence.
- Neither key-provider reference, key custody ACL, separate backup inventory, retention policy, restore operator nor recovery rehearsal was verified.
- RESULT: C-02 and C-06 BLOCKED; do not generate or inspect real key material and do not attempt live restore.

### Step 4: decision-ready evidence matrix
| Requirement | Verified evidence | Status | Minimal next proof |
|---|---|---|---|
| E-03 durable declarations/confirmations | HumanDeclaredFact / existing metadata providers not durable general authorities | BLOCKED | approve versioned provider mappings, implement only after separate release, synthetic restart tests |
| E-03 identity authorization | DurableApprovalStore scoped to existing approval domains | BLOCKED | owner-authorized identity domain contract and exact manifest/actor scope |
| E-03 audit/content verification | AuditStore in-memory; document observations metadata only | BLOCKED | durable identity audit and current protected content verifier |
| C-02 service/ACL custody | project tasks run interactively as rezag; repo root full control | BLOCKED | canonical deployed Kernel/identity service principals, protected roots and redacted ACL proof |
| C-02 HMAC and backups | no provider or independent custody evidence verified | BLOCKED | provider reference, separate custodian/ACL, backup inventories and restore permissions |
| C-06 rollback/recovery | same-directory anchor; synthetic continuity module only | BLOCKED | independently held Kernel epoch, synthetic crash/rollback and governed restore tests |

### Design conclusions, not implementation approval
- Keep existing SQLite-backed OrchestratorKernel as the sole continuity control plane; a versioned Kernel-owned identity epoch/head must be independently stored outside the replaceable identity DB+anchor set, with separate custodial controls.
- Do not repurpose synthetic orchestrator_continuity.py as the production authority.
- Separate bounded identity approval, durable declaration/confirmation, identity audit and content verification contracts; reuse existing services where actually authoritative.
- Production activation, real identities, protected content reads, ACL/key changes, restore execution, REMEDIATION-02 and OI-0003 remain forbidden under current Owner authorization.
- No condition was released. This document is LOCAL ONLY pending governed review/publication.
