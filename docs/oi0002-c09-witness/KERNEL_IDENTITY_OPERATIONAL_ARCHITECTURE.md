# C09 Kernel–Identity operational boundary and witness finality architecture

Date: 2026-10-22  
Contract: `oi0002.kernel-identity-c09/1.0`  
Status: `PROPOSED / INDEPENDENT_ARCHITECTURE_REVIEW_REQUIRED / NOT IMPLEMENTED`

## Decision and authority boundary

The existing Deterministic Orchestrator Kernel remains the sole transaction coordinator and permission authority. The Identity Persistence Authority remains the sole writer of its database and audit anchor. They communicate only through one local, message-mode Windows Named Pipe owned by the Identity service. The existing external GCS witness is a narrow append/read freshness service outside both local rollback domains; it cannot authorize, schedule, prepare, commit, abort or reconcile a domain transaction.

This specification reuses the accepted canonical framing, envelope and response validators and the shared C09 witness protocol. It creates no second orchestrator, shared database, queue, scheduler or generic broker. Implementation and operational activation are forbidden until an independent security reviewer returns PASS on the exact specification commit.

## Deployment principals and storage separation

The protected deployment manifest pins the binary Windows SIDs and executable hashes for the existing four principals:

- `AITaxKernel`: Kernel database, Kernel audit and continuity state; pipe client; witness writer request initiator.
- `AITaxIdentity`: Identity database, Identity audit/anchor and staged transaction receipts; pipe server.
- `AITaxKeyCustodian`: witness-record authentication service only; no domain or transaction decision authority.
- `AITaxRecovery`: governed recovery entry through Kernel only; never a direct Identity data-plane client.

Kernel cannot open Identity storage. Identity cannot open Kernel storage. Key Custodian and Recovery cannot open either data store. The pipe DACL grants connect/read/write only to the manifest-pinned Kernel SID; display names, group membership, Administrator status and process IDs are never sufficient authority.

## Authenticated transport

The Identity service creates one fixed deployment-scoped pipe using `PIPE_TYPE_MESSAGE`, `PIPE_READMODE_MESSAGE`, bounded instances, `PIPE_REJECT_REMOTE_CLIENTS` and `FILE_FLAG_FIRST_PIPE_INSTANCE`. Failure to acquire the first instance is a fatal start condition. The DACL omits Users, Administrators, Recovery and Key Custodian from data-plane access.

For every connection Identity calls `ImpersonateNamedPipeClient`, reads `TokenUser` from the thread token, compares the binary SID to the pinned Kernel SID and executes `RevertToSelf` in `finally` before dispatch. Kernel verifies the server process token against the pinned Identity SID using query-only rights before sending a request. Either token check, DACL check or local-only property failing closes the connection. PID is diagnostic only.

Each connection carries exactly one existing canonical frame. The operational contract version is distinct from the development-only contract. Unknown versions, duplicate/unknown fields, noncanonical bytes, excess size/depth, additional frames or trailing bytes are rejected before transaction creation. No password, signing key, raw evidence, SQL, path, callable or free-form command crosses the pipe.

## Closed operations and authorization

The default-deny message allowlist is:

- `PREPARE_MUTATION`, `COMMIT_MUTATION`, `GET_TRANSACTION`, `ABORT_PREPARED`;
- `READ_IDENTITY_STATE`;
- `PREPARE_BACKUP`, `COMMIT_BACKUP`, `PREPARE_RESTORE`, `COMMIT_RESTORE`.

Domain operations remain the accepted Identity APIs only. Each message/operation pair maps to one dedicated Kernel capability. Before creating `PENDING`, Kernel validates the active non-expired manifest, Kill Switch, task, actor instance, role, capability, exact deployment/case/tax-year/run/task/manifest scope, immutable evidence status and any required Human Gate. Identity accepts authorization only from the authenticated Kernel token plus a canonical, short-lived, one-time Kernel proof derived from a reread durable Kernel transaction row. A caller boolean, callback result or possession of the pipe token is insufficient.

The proof binds contract version, deployment, transaction ID, request digest, operation, exact scope, expected and projected Identity epoch/head, Kernel pending head, authorization-state version, immutable authorization-reference digests, issue/expiry times and a nonce. Identity verifies the pinned Kernel public key, exact bindings, expiry and one-time use in the same SQLite transaction as the mutation. Revocation and Kill Switch transitions serialize against proof reservation. Restart or expiry requires fresh Kernel revalidation; reconciliation cannot extend a proof.

## Durable transaction and staged-receipt protocol

1. Kernel authorizes the exact request and creates a transaction identity.
2. Identity `PREPARE` verifies current head and domain invariants and stores an idempotent `PREPARED` row with request digest, projected head and canonical mutation plan. It does not mutate domain state.
3. Kernel records durable `PENDING` with the exact projection, rereads it, and issues the row-derived one-time commit proof.
4. Identity `COMMIT` verifies the proof and exact prepared row, applies the mutation once, appends its audit record and stores `IDENTITY_COMMITTED` plus an authenticated staged-receipt containing transaction/request/result digests, prior/new Identity heads, Kernel pending head, backup generation and the exact canonical witness-record bytes. This state is not externally final and cannot be acknowledged.
5. Kernel verifies the staged receipt and asks Key Custodian to authenticate only those exact witness bytes. Kernel uses the existing writer credential to perform GCS conditional create for the exact epoch/sequence key, then uses the separately scoped reader credential to enumerate versions and read back the exact generation and bytes. It verifies schema, authentication, contiguous chain, previous commitment, generation uniqueness, no deletion ambiguity and every local-head binding.
6. Kernel records the verified witness key, generation and commitment in its durable transaction and requests Identity finalization with that exact evidence. Identity binds it to the staged receipt and advances to `COMMITTED_FINAL` without repeating the mutation.
7. Kernel rereads `COMMITTED_FINAL`, verifies result/head/receipt/witness bindings, records Kernel `COMMITTED`, releases the authorization reservation and only then acknowledges success.

An exact retry returns the recorded outcome. Reuse of a transaction or operation ID with different canonical bytes is a security denial. A fresh transaction cannot redefine an existing immutable identity/fact/evidence reference.

## Witness trust and key custody

The object key, canonical record and chain rules are exactly those in `WITNESS_PROTOCOL_SPEC.md`. Conditional create plus strong read/list consistency arbitrates one exact sequence position; version enumeration rejects replacement, extra generations and delete ambiguity. Startup and restore verify the complete contiguous chain and compare its final deployment/epoch/heads/generation to both local stores before enabling protected writes.

The writer credential may create only new objects under the deployment prefix and cannot read, overwrite, delete, alter retention or administer IAM. The reader credential may list versions and read exact generations but cannot write or administer. Record-authentication authority and Owner restore authority are separate. Key Custodian signs/MACs only a Kernel-authorized canonical witness digest after verifying the exact staged receipt; it cannot choose an operation or sequence.

Independent custody, IAM bindings, durable key provisioning and retention locking are Human Gates. Until those gates are approved and operationally proven, this architecture may be implemented and tested only with synthetic fixtures and non-privileged mocks; it cannot claim C09 operational acceptance.

## Crash, restart and reconciliation

| Durable state at failure | Required deterministic action |
| --- | --- |
| Kernel request only; no Identity PREPARED | retry PREPARE or abort without Identity change |
| Identity PREPARED; no Kernel PENDING | expire/abort exact prepare; never mutate |
| Kernel PENDING; Identity PREPARED | revalidate authority and retry exact COMMIT |
| Identity `IDENTITY_COMMITTED`; no witness | verify staged receipt and local heads; retry exact witness append/readback; fail closed on outage or ambiguity |
| Witness exists; Identity not final | exact generation/bytes and staged receipt permit finalizing the same transaction only |
| Identity final; Kernel PENDING | exact final result and witness complete Kernel COMMITTED |
| Both local stores claim final but witness disagrees/missing | startup stays fail closed; no silent repair or reinitialization |

Provider timeout is treated as ambiguous: read the exact key/version before retrying create. Conflicting valid successors, gaps, forks, invalid authentication, deletion/version ambiguity, stale heads or an unverifiable Identity-ahead state halt protected writes. Recovery never replays an already committed Identity mutation.

Restore is deployment-store scoped. It requires an unexpired, one-time Owner authorization bound to source/target epoch, complete case-generation manifest, backup digest/generation and expected witness head. Replacement is staged, verified, and followed by a `RESTORE` witness record starting the authorized successor epoch. Reuse, partial-store restore or any mismatched case/generation entry is denied. Retention lock or destructive recovery remains a separate Human Gate.

## Audit and privacy

Kernel and Identity audit independently record transaction ID, request/response digests, operation, privacy-minimized outcome/denial code, exact scope identifiers and epoch/head commitments. Witness records contain only opaque operation IDs and commitments—never taxpayer values, document content, credentials or key material. Each success, denial, retry, crash reconciliation, restore and rollback decision must be reconstructable across the two audit chains and exact witness generation.

## C01–C13 mapping

| Criterion | Architectural enforcement | Required acceptance evidence |
| --- | --- | --- |
| C01 | Kernel alone authorizes, orders and finalizes | trace every operation; prove witness/custodian cannot coordinate |
| C02 | separate SIDs, stores and DACLs | four-principal effective-access denial matrix |
| C03 | local Named Pipe, bilateral token checks, closed contract | wrong SID, remote, squatted pipe and impersonation failures denied |
| C04 | canonical transaction/request identity and durable idempotency | replay, mismatch, concurrency and restart tests |
| C05 | `PENDING → IDENTITY_COMMITTED → witness → COMMITTED_FINAL → COMMITTED` | process kill at every boundary; no early acknowledgement |
| C06 | staged receipt binds Identity/Kernel heads and backup generation to witness | substituted/stale head, receipt and generation denied |
| C07 | tabled deterministic reconciliation | both restart orders, outage and ambiguous-write tests converge or halt |
| C08 | whole-store, one-time Owner-authorized restore | populated restore plus expiry/revocation/reuse/partial-store negatives |
| C09 | external authenticated append chain outside local backups | local and coordinated rollback, fork/gap/version/deletion attacks denied |
| C10 | only accepted Identity APIs; immutable lineage unchanged | existing lifecycle/family/fact regression through boundary |
| C11 | correlated, independently chained, privacy-minimized audit | reconstruct every campaign scenario and tamper negatives |
| C12 | frozen version, canonical bytes, closed enums | golden vectors, unsupported version and compatibility rejection |
| C13 | exact-SHA four-principal campaign and separate final review | focused/security/full regression and independent PASS |

## Required verification sequence

After independent architecture PASS only:

1. implement transport and protocol with mocks/synthetic stores;
2. run canonical, authorization, replay, cross-scope and no-early-ack tests;
3. inject failures at every database, receipt, provider and finalization boundary;
4. run synthetic concurrency, outage, process-kill, restart and rollback campaigns;
5. stop for Owner approval before IAM, new identities, durable key custody, retention lock or other privileged cloud changes;
6. run the approved four-principal and live-provider campaign without taxpayer data;
7. freeze exact SHA/evidence and obtain a different independent final acceptance authority.

Passing architecture review authorizes implementation within these bounds only. It does not accept C09, OI-0002, protected persistence or production operation.
