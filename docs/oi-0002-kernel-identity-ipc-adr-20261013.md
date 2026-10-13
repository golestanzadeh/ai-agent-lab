# ADR: OI-0002 authenticated Kernel–Identity IPC

ADR ID: `ADR-OI0002-KERNEL-IDENTITY-IPC-V1`  
Contract identifier: `oi0002.kernel-identity-ipc/1.0`  
Date: 2026-10-13  
Status: **PROPOSED / ADR_REVIEW_READY / NOT IMPLEMENTED / NOT ACCEPTED**  
Baseline: `fbdc9660205d60800eda049d04b168bdd5a30049`

## Decision

Use a local Windows Named Pipe as the only public process boundary between the existing Deterministic Orchestrator Kernel and Identity Persistence Authority.

The Identity service, running as `AITaxIdentity`, owns a message-mode pipe with a fixed deployment-manifest name such as:

`\\.\pipe\AI-Tax-Agent\OI0002\Identity\v1`

The Kernel, running as `AITaxKernel`, is the only data-plane client. Recovery requests enter the existing Kernel authority first; `AITaxRecovery` never calls the Identity pipe directly. `AITaxKeyCustodian` supplies no IPC authority. The Kernel remains the sole transaction coordinator and permission authority. Identity remains the sole writer of its protected database and audit anchor.

This ADR defines a public protocol and implementation constraints only. It does not implement or activate a pipe, service, account, ACL, Scheduled Task, database migration or production component.

## Context and preserved invariants

The frozen closure matrix is `docs/oi-0002-final-closure-matrix-20261012.md`. REMEDIATION-02, Persistence Contract v1, the four Windows principals, protected custody topology, sealed real-token run `run-20261012T174008Z` and their accepted evidence remain unchanged.

Current `IdentityContinuityAuthority` is explicitly synthetic and accepts an in-process `OrchestratorKernel`. `IdentityPersistence` accepts generic authorization/evidence callbacks but has no authenticated cross-process Kernel client. Directly granting Identity access to the Kernel database, running both stores as Administrator, sharing a database or treating synthetic callbacks as operational authorization would violate the accepted custody boundary.

## Why Windows Named Pipes

Named Pipes are native to the target operating system, support local-only message transport, discretionary ACLs, server-side client impersonation and process identity inspection, and require no cloud service, message queue, scheduler, shared database or general broker. The protocol is narrow and deployment-local.

Rejected alternatives:

- Loopback TCP/HTTP: port ownership does not by itself authenticate the Windows caller token and adds firewall/listener surface.
- `multiprocessing.connection` authentication keys: authenticates possession of a shared secret, not the actual Windows security token.
- Shared files/directories: become an unreviewed queue, weaken transaction ordering and require cross-writable custody.
- Direct cross-database access: violates principal and database separation.
- COM, gRPC or a general broker: unnecessary framework/service surface for this bounded interface.

## Process and custody model

| Component | Windows principal | May open | Must not open |
| --- | --- | --- | --- |
| Kernel service | `AITaxKernel` | Kernel DB/backup and Identity Named Pipe as client | Identity DB, Identity audit anchor, HMAC key |
| Identity service | `AITaxIdentity` | Identity DB/backup; HMAC key read-only; Named Pipe as server | Kernel DB/backup |
| Key custodian | `AITaxKeyCustodian` | HMAC-key custody paths | Kernel/Identity DBs; data-plane pipe |
| Recovery operator | `AITaxRecovery` | Existing governed recovery surfaces | Identity data-plane pipe except through Kernel authorization |

The existing protected deployment manifest pins the four exact SIDs and the pipe contract version. Display names are never authorization identities.

## Transport authentication and confinement

The implementation must satisfy all of the following:

1. Create the pipe with `PIPE_TYPE_MESSAGE`, `PIPE_READMODE_MESSAGE`, bounded instances and `PIPE_REJECT_REMOTE_CLIENTS`.
2. Use a protected DACL that grants pipe connect/read/write only to the exact manifest-pinned `AITaxKernel` SID; Identity and `SYSTEM` may administer the server object. Administrators, Users, Recovery and Key Custodian receive no data-plane connect ACE.
3. Use `FILE_FLAG_FIRST_PIPE_INSTANCE`; failure to acquire the first instance is a fatal service-start condition, never a fallback to another name.
4. On every connection the Identity server calls `ImpersonateNamedPipeClient`, obtains `TokenUser` from the thread token and compares the binary SID to the pinned Kernel SID. Anonymous, remote, deny-only, wrong-token or insufficient-impersonation connections fail closed. `RevertToSelf` executes in `finally` before request processing continues.
5. The Kernel client calls `GetNamedPipeServerProcessId`, opens the server process/token with query-only rights and verifies the exact pinned `AITaxIdentity` SID before sending sensitive request fields. If server-token verification is unavailable, the connection fails closed.
6. Client/server process IDs are diagnostic correlation only; PID is never authority.
7. Pipe creation, DACL and both token checks are independently mandatory. Passing one does not compensate for another.

No password, HMAC key or reusable application secret crosses the pipe.

## Frozen wire envelope

Each message is a four-byte unsigned little-endian length followed by UTF-8 canonical JSON. Maximum frame size is 65,536 bytes. Reject truncated frames, trailing bytes, duplicate JSON keys, non-integer numbers, unknown fields, invalid Unicode and nesting deeper than 12. Payloads contain identifiers and bounded domain values only; protected document bytes are resolved inside Identity through the accepted evidence resolver.

Required request fields:

- `contract`: exact string `oi0002.kernel-identity-ipc/1.0`;
- `message_type`: one closed value from the allowlist below;
- `transaction_id`: Kernel-generated `tx:v1:<lowercase UUIDv4>`;
- `request_digest`: `sha256:` of the canonical request body excluding this field;
- `deployment_id`, `case_id`, `tax_year`, `run_id`, `task_id`, `manifest_id`;
- `actor_instance_id`, `role_id`, `capability`, `domain_operation`;
- `expected_epoch`, `expected_head` where state-bearing;
- `authorization_references`: sorted, bounded immutable references required by the domain operation;
- `expires_at`: UTC timestamp no later than the active manifest expiry;
- `payload`: operation-specific object validated against the exact contract version.

The response repeats contract, message type, transaction ID and request digest, and adds `outcome`, `response_digest`, `identity_epoch`, `identity_head`, and a privacy-minimized error code when denied. Free-form exception text is never returned or audited.

## Default-deny operation allowlist

Transport message types are exactly:

- `PREPARE_MUTATION`
- `COMMIT_MUTATION`
- `GET_TRANSACTION`
- `ABORT_PREPARED`
- `READ_IDENTITY_STATE`
- `PREPARE_BACKUP`
- `COMMIT_BACKUP`
- `PREPARE_RESTORE`
- `COMMIT_RESTORE`

Mutation domain operations are exactly the accepted Identity APIs: `REGISTER_IDENTITY`, `UPDATE_IDENTITY_STATUS`, `BIND_PARTY`, `CORRECT_PARTY_ROLE`, and `BIND_FACT`. Read operations are `READ_CASE_IDENTITY`, `LIST_PARTIES`, and `READ_FACTS`. Each maps to one existing dedicated Kernel capability. Unknown contract versions, message types, operations, fields, capabilities or operation/capability combinations are rejected before domain execution and produce a bounded denial audit.

The wire interface never exposes SQL, filesystem paths supplied by a caller, arbitrary Python callable names, shell commands or generic method invocation.

## Authorization and transaction identity

The Kernel validates kill-switch state, active non-expired manifest, task, actor, role, capability, exact case/year/run scope and required Human Gate before creating a transaction. It generates the transaction ID and durably records:

- request digest and exact authorization context;
- expected Identity epoch/head;
- target epoch;
- state and timestamps;
- Identity result digest/head when known.

Identity trusts authorization only when the caller token is the pinned Kernel SID and the complete authorization envelope is valid and unexpired. It durably stores the same transaction ID, request digest and context. Reuse of a transaction ID with any different byte-canonical request is a security denial. Exact retries return the previously stored outcome; they never repeat a mutation. Domain identifiers retain their existing idempotency rules, so a fresh transaction cannot silently redefine an existing identity, binding, fact or evidence reference.

Audit records on both sides correlate only by transaction ID, request/response digest, case ID, tax year, operation, outcome and epoch/head. They contain no taxpayer value, document content, key, credential or raw evidence payload.

## Mutation protocol

The protocol preserves the existing Kernel requirement that the next head is known before continuity reservation:

1. **Kernel authorization:** Kernel validates the request and creates its durable transaction record.
2. **Identity PREPARE:** Identity validates authorization, evidence, expected epoch/head and domain invariants. In one Identity transaction it records a `PREPARED` row containing the canonical mutation plan, exact future audit-event material, projected next epoch/head, request digest and expiry. No domain mutation occurs. An exact retry returns the same projection.
3. **Kernel PENDING:** Kernel calls its existing continuity reservation using the projected next head and records the transaction ID/request digest in the pending envelope. Only then may commit proceed.
4. **Identity COMMIT:** Identity requires the exact prepared transaction and atomically applies the domain mutation, appends the predetermined audit event and marks the transaction `COMMITTED` with the exact epoch/head and response digest.
5. **Anchor synchronization:** the same Identity database transaction creates an HMAC-protected pending anchor-sync receipt. After SQLite commit, Identity atomically replaces the external audit-anchor file and consumes that receipt. On restart, only an exact valid receipt whose DB head matches may complete anchor synchronization; every other mismatch fails closed.
6. **Kernel COMMITTED:** Kernel verifies transaction ID, request digest, target epoch and exact projected/returned head, then finalizes its continuity record. The committed response is durable and replayable for exact retries.

Identity never commits a mutation without an existing durable PREPARED record. Kernel never marks COMMITTED before receiving or recovering the exact durable Identity result.

## Crash, restart and reconciliation table

| Failure boundary | Durable observation | Deterministic action |
| --- | --- | --- |
| Before Identity PREPARE | Kernel transaction only | Retry PREPARE or expire without Identity change |
| After PREPARE, before Kernel PENDING | Identity `PREPARED`, no domain change | Exact retry returns projection; Kernel reserves or explicitly aborts |
| After Kernel PENDING, before Identity COMMIT | Kernel pending + Identity prepared | Kernel restart queries exact transaction and resends COMMIT |
| During Identity SQLite transaction | Transaction rolls back completely | Exact COMMIT retry |
| After Identity DB commit, before anchor replacement | Committed DB + valid pending anchor receipt | Identity restart completes exact anchor sync; otherwise fail closed |
| After Identity COMMIT, before response | Identity committed + Kernel pending | `GET_TRANSACTION` returns exact durable result; Kernel finalizes |
| After response, before Kernel finalize | Same as above | Kernel verifies and finalizes once |
| After Kernel finalize | Both committed | Exact retry returns stored outcome; changed replay denied |
| State absent, mismatched or ambiguous | Non-correlating records | Kill operation path and require governed recovery; never guess |

Startup is fail-closed until each service verifies its own DB/audit integrity. Kernel then reconciles every pending transaction through `GET_TRANSACTION`. Identity cannot initiate Kernel state changes.

## Backup, restore and rollback

`PREPARE_BACKUP` freezes the exact committed Identity epoch/head and creates a consistent SQLite backup plus audit anchor. `COMMIT_BACKUP` returns a digest over the backup bytes, anchor, contract version, epoch/head, deployment/case/year and generation. Kernel stores that digest/head in its audit and continuity evidence.

Restore always begins at Kernel with an existing exact Owner/Human Gate authorization. The authorization is reserved—not silently consumed—for one transaction and binds backup digest, source epoch/head, current expected epoch/head, target generation, operator, expiry, case/year/run/task/manifest and contract version. Kernel then calls Identity as the authenticated Kernel token:

1. `PREPARE_RESTORE` verifies the backup/anchor digest, audit integrity, authorization envelope and strictly increasing target generation without replacing live files.
2. Kernel records PENDING with the projected restored continuity head.
3. `COMMIT_RESTORE` performs an atomic replace with a recoverable receipt and preserves the pre-restore generation as an independent recovery artifact.
4. Kernel verifies the exact result, consumes the one-time authorization and finalizes continuity.

Interrupted restore follows the same transaction reconciliation rules. Expired, revoked, consumed, wrong-operator, wrong-digest, wrong-case/year, stale-generation and old-head requests are denied. Replacing only the Identity DB/anchor, only Kernel state, or both with an older internally consistent pair is detected by the monotonic Kernel generation/head binding and fails closed.

## Compatibility and lifecycle

- Contract `1.0` is exact; there is no version negotiation, downgrade or permissive unknown-field handling.
- A future version uses a different pipe name and contract identifier and requires explicit compatibility tests and governed activation.
- Unsupported clients receive `UNSUPPORTED_CONTRACT` without execution.
- Internal database schemas, filesystem paths and Python classes are not public API.
- Later modules may use only the versioned Kernel-facing interface; they may not connect directly to the Identity pipe or either database.
- After acceptance, non-breaking improvements are tracked separately. OI-0002 reopens only for a demonstrated defect invalidating acceptance evidence.

## Required implementation verification

Unit/contract tests must cover canonical framing, closed enums, size/depth limits, version rejection, digest validation, transaction conflicts, idempotent exact retries, permission mapping and every crash boundary.

The disposable operational campaign must use the four actual Windows principals and preserved custody topology:

- `AITaxKernel`: mutual-authenticated positive connection and authorized operations;
- `AITaxIdentity`: server ownership, own-store-only access and rejection of self-client authority;
- `AITaxKeyCustodian`: pipe connection denied; key custody remains unchanged;
- `AITaxRecovery`: data-plane pipe connection denied; exact authorized restore succeeds only through Kernel;
- unrelated user/Administrator/remote client: connection or token authentication denied;
- both services: process termination at every tabled boundary, restart reconciliation, communication interruption and exact retry;
- populated backup/restore, interrupted restore, unauthorized restore and old-generation rollback;
- cross-case/year/task/manifest/capability substitutions and transaction-ID replay;
- audit correlation with no sensitive payload;
- focused, security and complete regression suites.

Operational evidence must bind contract version, exact implementation SHA, service executable hashes, manifest/deployment identity, principal SIDs, transaction IDs, scenario outcomes and result hashes. It must not contain credentials, key bytes or taxpayer data.

## Security properties and residual decisions

This design intentionally provides no distributed atomic transaction. Safety comes from Kernel coordination, durable prepare/idempotency records, exact head projection, recoverable anchor receipts and deterministic reconciliation. Availability is subordinate to integrity: ambiguity stops the affected operation.

Implementation may choose Win32 bindings already available to the project runtime or a minimal reviewed `ctypes` boundary. It may not substitute a shared secret for token authentication or silently add a third-party IPC framework. Exact service installation/start authority remains governed separately from code implementation and testing.

No unresolved architecture decision remains inside the Owner-approved scope. Implementation is nevertheless forbidden until an independent architecture/security reviewer returns PASS on the exact commit containing this ADR.
