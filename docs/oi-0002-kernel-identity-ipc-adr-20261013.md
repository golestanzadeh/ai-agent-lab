# ADR: OI-0002 authenticated Kernel–Identity IPC

ADR ID: `ADR-OI0002-KERNEL-IDENTITY-IPC-V1`  
Contract identifier: `oi0002.kernel-identity-ipc/1.0`  
Date: 2026-10-13  
Status: **PROPOSED / ADR_REMEDIATION_REVIEW_READY / NOT IMPLEMENTED / NOT ACCEPTED**
Baseline: `fbdc9660205d60800eda049d04b168bdd5a30049`

Independent review baseline: `dcfb6ab712b74b65b10a2e5206795061dce07c95`; review evidence `86a96d06b5c1091a273badadbe3b988831b8ea27`; decision `INDEPENDENT_ARCHITECTURE_FAIL`. This revision addresses F01–F06 without modifying that preserved FAIL report.

## Decision

Use a local Windows Named Pipe as the only public process boundary between the existing Deterministic Orchestrator Kernel and Identity Persistence Authority.

The Identity service, running as `AITaxIdentity`, owns a message-mode pipe with a fixed deployment-manifest name such as:

`\\.\pipe\AI-Tax-Agent\OI0002\Identity\v1`

The Kernel, running as `AITaxKernel`, is the only data-plane client. Recovery requests enter the existing Kernel authority first; `AITaxRecovery` never calls the Identity pipe directly. The Kernel remains the sole transaction coordinator and permission authority. Identity remains the sole writer of its protected database and audit anchor. `AITaxKeyCustodian` owns only the TPM-backed freshness witness defined below; it cannot authorize, order, prepare, commit or reconcile a domain transaction and is not a broker or transaction coordinator.

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
| Kernel service | `AITaxKernel` | Kernel DB/backup, Identity data-plane pipe, freshness read/advance endpoint | Identity DB, Identity audit anchor, HMAC key |
| Identity service | `AITaxIdentity` | Identity DB/backup; HMAC key read-only; data-plane pipe as server; freshness read endpoint | Kernel DB/backup; freshness advance |
| Key custodian | `AITaxKeyCustodian` | HMAC-key/TPM custody paths; narrow freshness endpoint | Kernel/Identity DBs; Identity data-plane pipe; transaction authority |
| Recovery operator | `AITaxRecovery` | Existing governed recovery surfaces | Identity data-plane pipe except through Kernel authorization |

The existing protected deployment manifest pins the four exact SIDs and the pipe contract version. Display names are never authorization identities.

Two non-exportable Windows CNG ECDSA P-256 keys are also pinned by public-key SHA-256 in that manifest. The Kernel continuity key may be opened for signing only by `AITaxKernel`; its public key is readable by Identity. The Key Custodian freshness key and TPM NV-counter authorization are usable only by `AITaxKeyCustodian`; their public verification material is readable by Kernel and Identity. Private keys, TPM authorization values and HMAC keys never cross either pipe or enter a database/backup. ECDSA signatures use fixed 64-byte `r || s` form and base64url without padding.

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

Each pipe message contains exactly one frame: a four-byte unsigned little-endian payload length followed by that many canonical JSON bytes. The length is the JSON byte count only, must be `1..65,532`, and the complete pipe message is therefore at most 65,536 bytes. The receiver reads until the message boundary, handling `ERROR_MORE_DATA` only while the accumulated message remains within the bound. EOF before the declared length, zero/oversize length, a second frame, bytes after the declared payload, `ERROR_MORE_DATA` beyond the bound, invalid UTF-8/JSON or any schema error causes a bounded denial audit where possible and immediate connection termination; no second message is accepted on that connection.

“Canonical JSON” normatively means RFC 8785 JSON Canonicalization Scheme with this stricter profile: UTF-8 without BOM; object keys sorted by their UTF-16 code units as RFC 8785 specifies; no duplicate keys; no insignificant whitespace; strings contain valid Unicode scalar values and are not normalized; the only escapes are the RFC 8785 forms; numbers and JSON `null` are forbidden everywhere; booleans, strings, arrays and objects are allowed; all protocol counters/years are canonical decimal strings matching their field-specific regex. Timestamps are strings in exact UTC form `YYYY-MM-DDTHH:MM:SS.ffffffZ` with six fractional digits. Parsers must reject lone surrogates, noncharacters, duplicate keys before object construction, nesting deeper than 12 and unknown fields. A digest is lowercase hex `sha256:` plus SHA-256 of the exact canonical UTF-8 bytes of the specified object. `request_digest` hashes the complete request object with only `request_digest` omitted; `response_digest` hashes the complete response object with only `response_digest` omitted. Digest comparison is constant-time.

Normative primitive golden vectors are:

| Canonical JSON | UTF-8 byte count | Complete frame hex | SHA-256 |
| --- | ---: | --- | --- |
| `{"a":"é","z":true}` | 19 | `130000007b2261223a22c3a9222c227a223a747275657d` | `13b252049f10ae83cae57a1523146622d05d2cf435237982d6db1f1d1ee89298` |
| `{"a":"\u000f","b":["x",false]}` | 30 | `1e0000007b2261223a225c7530303066222c2262223a5b2278222c66616c73655d7d` | `cd9de0b0f795c4857886b4475f93da16bd4a94b17f74b2a1f7b85be525b2e1b9` |

Before implementation the contract tests must add full request/response golden vectors using the frozen schemas, plus UTF-16 key-order edges and the maximum legal frame, without changing this profile. Negative vectors cover alternate key order/spacing, BOM, duplicate keys, composed versus decomposed Unicode substitution, lone surrogate/noncharacter, numeric tokens including `-0`, `1.0` and exponent forms, timestamp offsets/precision changes, zero and oversize lengths, split prefix/body reads, early EOF, `ERROR_MORE_DATA`, concatenated frames and trailing bytes. Only the canonical vector is accepted; semantically similar noncanonical bytes are rejected before transaction creation.

Required request fields:

- `contract`: exact string `oi0002.kernel-identity-ipc/1.0`;
- `message_type`: one closed value from the allowlist below;
- `transaction_id`: Kernel-generated `tx:v1:<lowercase UUIDv4>`;
- `request_digest`: `sha256:` of the canonical request body excluding this field;
- `deployment_id`, `scope_kind`, `case_id`, `tax_year`, `run_id`, `task_id`, `manifest_id`;
- `actor_instance_id`, `role_id`, `capability`, `domain_operation`;
- `expected_epoch`, `expected_head` where state-bearing;
- `authorization_references`: sorted, bounded immutable references required by the domain operation;
- `expires_at`: UTC timestamp no later than the active manifest expiry;
- `payload`: operation-specific object validated against the exact contract version.

`scope_kind` is `CASE_YEAR` for reads and domain mutations. Physical backup/restore uses `DEPLOYMENT_STORE`; for that scope `case_id` and `tax_year` must be the literal `*`, never an individual case. This sentinel is scope metadata, not permission to bypass case isolation.

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

Identity trusts authorization only when the caller token is the pinned Kernel SID, the complete authorization envelope is valid, and the commit carries both proofs below. A caller-controlled boolean, unsigned Kernel claim, callback result or possession of the pipe token is not a proof.

### Durable continuity-reservation proof (F01)

After the Kernel PENDING transaction commits, the Kernel continuity component rereads the exact row through a new read-only transaction and emits `reservation-proof/v1`. It is canonical JSON signed with the Kernel continuity key and contains: contract/proof version, deployment ID, scope kind and scope identifiers, transaction ID, request digest, operation, expected and target Identity epoch/head, Kernel pending epoch/head, authorization-state baseline version, restore generation when applicable, nonce, `issued_at`, and `not_after`. The private signing operation is exposed only by the continuity component and accepts a database row identity, not caller-supplied fields; it signs only a reread row in durable `PENDING`. Signing failure does not change the row.

Identity verifies the pinned public-key digest, fixed signature encoding, complete canonical bytes, deployment/scope/transaction/request/operation/head/generation equality and a maximum 30-second proof lifetime against its own monotonic-adjusted UTC clock. It stores the proof digest with the prepared transaction. Missing, fabricated, expired, replayed or mismatched proof denies before domain or restore state changes. One proof is valid for one transaction and one projected head only; an exact retry of that transaction may reuse it only while reconciling the already-recorded result. After abort, finalization or generation change it cannot authorize new work. Identity never opens the Kernel database.

### Commit authorization fence (F02)

Immediately before issuing COMMIT, the Kernel permission component opens a serializable authorization fence over the current Kill Switch, manifest, task, actor, role, capability, case/deployment scope, evidence statuses and required Human Gate. The same transaction verifies that the continuity row is exact `PENDING`, advances a monotonic `authorization_state_version` beyond the reservation baseline, reserves the one transaction use, and emits a signed `commit-permit/v1` containing the reservation-proof digest and all transaction/head bindings, authorization/evidence reference digests, Human Gate ID and use ID, new `authorization_state_version`, random challenge from Identity PREPARE, `issued_at`, and `not_after` no more than five seconds later. The signing API accepts only the committed fence row identity and signs fields reread after commit.

Kill Switch activation, manifest/task/role/capability revocation, evidence revocation and Human Gate revocation/consumption serialize against fences. They either commit before permit issuance (so issuance denies) or wait for the fence to reach terminal outcome/expiry; they cannot commit invisibly inside an active fence. Identity independently verifies the signed permit with the pinned Kernel public key, exact prepared challenge and bindings, its own clock and one-time-use ledger in the same SQLite transaction as the domain mutation. A permit is not a statement supplied by an arbitrary Kernel call site: authenticity, row-derived issuance, short lifetime, serializable fence and one-time binding are mandatory parts of the Kernel permission contract. Expiry or service restart before the Identity transaction commits denies and requires Kernel to revalidate and issue a fresh permit; reconciliation never extends or fabricates a permit.

For restore, the Owner/Human Gate use is first reserved by the fence and atomically marked `IN_PROGRESS` with the transaction. Identity consumes the permit use exactly once when replacement finality is established; Kernel marks the Human Gate consumed only after the verified final result. Crash recovery can only resume the same transaction/use ID. Abort or expiry releases an unused reservation through a separately audited Kernel transition; it never makes a consumed use reusable.

Identity durably stores the same transaction ID, request digest, context, reservation-proof digest and commit-permit use ID. Reuse of a transaction ID with any different byte-canonical request is a security denial. Exact retries return the previously stored outcome; they never repeat a mutation. Domain identifiers retain their existing idempotency rules, so a fresh transaction cannot silently redefine an existing identity, binding, fact or evidence reference.

Audit records on both sides correlate only by transaction ID, request/response digest, case ID, tax year, operation, outcome and epoch/head. They contain no taxpayer value, document content, key, credential or raw evidence payload.

## Mutation protocol

The protocol preserves the existing Kernel requirement that the next head is known before continuity reservation:

1. **Kernel authorization:** Kernel validates the request and creates its durable transaction record.
2. **Identity PREPARE:** Identity validates authorization, evidence, expected epoch/head and domain invariants. In one Identity transaction it records a `PREPARED` row containing the canonical mutation plan, exact future audit-event material, projected next epoch/head, request digest and expiry. No domain mutation occurs. An exact retry returns the same projection.
3. **Kernel PENDING and proofs:** Kernel commits the continuity reservation using the projected next head, rereads it and creates `reservation-proof/v1`; it then revalidates and fences current authorization and creates `commit-permit/v1` as specified above. Only these exact signed proofs may advance the transaction.
4. **Identity COMMIT:** Identity requires the exact prepared transaction and verifies both proofs. For a non-restore mutation it consumes the permit use in the same SQLite transaction that applies the domain mutation and appends the predetermined audit event. A restore instead marks that exact permit use `REPLACEMENT_STARTED` before selecting the staged generation and cannot use it for any other replacement. The transaction enters durable `ANCHOR_PENDING`, not final `COMMITTED`, with exact epoch/head, response digest and an HMAC-protected anchor-sync receipt.
5. **Freshness and anchor finality:** Kernel directs the Key Custodian to advance the TPM counter for the exact transaction digest. Identity verifies and durably binds the returned witness, flushes the new anchor temporary file containing that witness, atomically replaces the anchor, flushes the containing directory, rereads and verifies the published anchor against the DB head/epoch/receipt/witness, and then in a second SQLite transaction consumes the receipt and changes the transaction to `COMMITTED_FINAL`. Repeated witness or publication failure leaves `ANCHOR_PENDING`; all further writes and finalizable responses fail closed. Only the exact receipt/witness pair may be replayed after restart, once.
6. **Kernel COMMITTED:** `GET_TRANSACTION` returns `NOT_FINALIZABLE` for `PREPARED` or `ANCHOR_PENDING` and never includes a final result proof. Only `COMMITTED_FINAL` returns the durable result plus verified anchor and freshness-witness digests. Kernel verifies transaction ID, request digest, permit use, target epoch, returned head, anchor digest and TPM witness/value, then finalizes its continuity record and releases the authorization fence. A committed response is durable and replayable for exact retries.

Identity never changes domain state without an existing durable PREPARED record, exact reservation proof and live commit permit. Kernel never marks COMMITTED before receiving or recovering the exact `COMMITTED_FINAL` Identity result.

## Crash, restart and reconciliation table

| Failure boundary | Durable observation | Deterministic action |
| --- | --- | --- |
| Before Identity PREPARE | Kernel transaction only | Retry PREPARE or expire without Identity change |
| After PREPARE, before Kernel PENDING | Identity `PREPARED`, no domain change | Exact retry returns projection; Kernel reserves or explicitly aborts |
| After Kernel PENDING, before proof/permit | Kernel pending + Identity prepared | Kernel rereads PENDING, revalidates current authorization and issues fresh proofs or denies |
| After proof/permit, before Identity COMMIT | Kernel pending/fenced + Identity prepared | Expired permits are never replayed; Kernel revalidates and issues a fresh permit for the same transaction |
| During Identity SQLite transaction | Transaction rolls back completely | Exact COMMIT retry |
| After Identity DB commit, before TPM advance | `ANCHOR_PENDING` DB + exact receipt; old TPM value | Kernel requests the one exact advance; `GET_TRANSACTION` is non-finalizable |
| After TPM advance, before witness/anchor finality | Advanced TPM + exact transaction digest; `ANCHOR_PENDING` | Key Custodian returns/reconstructs only the exact witness; Identity restart completes and verifies exact anchor sync or remains fail-closed |
| After anchor finality, before response | Identity `COMMITTED_FINAL` + Kernel pending | `GET_TRANSACTION` returns exact durable result; Kernel finalizes |
| After response, before Kernel finalize | Same as above | Kernel verifies and finalizes once |
| After Kernel finalize | Both committed | Exact retry returns stored outcome; changed replay denied |
| State absent, mismatched or ambiguous | Non-correlating records | Kill operation path and require governed recovery; never guess |

Startup is fail-closed until each service verifies its own DB/audit integrity and both verify the independent TPM freshness witness below. Kernel then reconciles every pending transaction through `GET_TRANSACTION`. A prepared transaction never survives by silently extending authorization; a fresh permit requires full current-state revalidation. Identity cannot initiate Kernel state changes.

## Backup, restore and rollback

Physical backup and restore are deployment-store operations because Persistence Contract v1 uses one SQLite database per deployment. They require `scope_kind=DEPLOYMENT_STORE`, `case_id="*"`, `tax_year="*"`, exact `deployment_id` and `store_id`, and an ordered manifest of every contained `(case_id, tax_year, case_generation, case_head)` digest. A case/year capability or authorization can never invoke physical backup/restore. Case-scoped logical import/export is outside contract 1.0 and may not be simulated with file replacement.

`PREPARE_BACKUP` freezes an exact `COMMITTED_FINAL` Identity epoch/head and creates a SQLite online-backup snapshot plus the verified audit anchor and complete case-generation manifest. `COMMIT_BACKUP` returns a digest over the exact backup bytes, anchor, contract version, deployment/store identity, complete manifest, epoch/head, recovery generation and freshness-witness value. Kernel stores that digest/head/manifest/witness in its audit and continuity evidence.

Restore always begins at Kernel with an existing exact deployment-store Owner/Human Gate authorization. The authorization is reserved—not silently consumed—for one transaction and binds backup digest, source epoch/head, current expected epoch/head, source and target freshness values, strictly increasing recovery generation, complete affected-case manifest, operator, expiry, run/task/manifest and contract version. A missing case, extra case, changed case generation or case-scoped authorization denies before file staging. Kernel then calls Identity as the authenticated Kernel token:

1. `PREPARE_RESTORE` verifies the backup/anchor digest, audit integrity, complete store/case manifest, current independent freshness witness, authorization envelope and target generation without replacing live files; it returns a prepared challenge and projected restored continuity head.
2. Kernel records PENDING and obtains the exact reservation proof and commit permit. The permit binds the complete deployment-store scope and one-time restore use.
3. `COMMIT_RESTORE` first creates and durably verifies a protected pre-restore recovery set. It stages the database, WAL state and anchor in a new generation directory, fsyncs every file and directory, and writes a signed restore intent. An atomic generation-pointer replacement selects the whole staged set; individual live files are never replaced in place. Identity then verifies the selected set and publishes `ANCHOR_PENDING`; only exact anchor finality changes it to `COMMITTED_FINAL`.
4. Identity marks the restore permit use `CONSUMED` only as it records exact `COMMITTED_FINAL`. Kernel verifies that final result and independent freshness advancement, atomically marks the Human Gate consumed, finalizes continuity and closes the authorization fence. A retry observes the selected generation and never repeats pointer replacement or freshness advancement.

Interrupted restore follows the same transaction and receipt reconciliation rules. Expired, revoked, consumed, wrong-operator, wrong-digest, wrong deployment/store, incomplete case manifest, stale generation/witness and old-head requests are denied. An ambiguous pointer, partial staged generation or missing protected pre-restore set prevents service start and requires governed recovery.

### Independent rollback freshness authority (F05)

C09 is enforced by one TPM 2.0 NV counter provisioned for this deployment and owned by `AITaxKeyCustodian`. The counter index, TPM endorsement/public identity, freshness public-key digest and deployment/store identity are pinned in the protected manifest and Owner acceptance evidence. Kernel and Identity have read-only access to a narrow verifier; neither can reset, decrement, define, undefine or increment the counter. `AITaxRecovery` has no counter-management authority. Firmware/TPM clear, NV-index loss, ownership change, unavailable attestation or public-identity mismatch is a Human Gate and fail-closed recovery event, never automatic initialization.

The Key Custodian exposes only `READ_FRESHNESS` and `ADVANCE_FRESHNESS(expected_value, transaction_digest, recovery_generation)` through a separate local Named Pipe. It applies the same first-instance, remote-rejection, exact-token impersonation, server-token verification, framing and fail-closed rules as the data-plane pipe. Its DACL permits the exact Kernel SID to read/advance and the exact Identity SID to read only; no other principal, including Recovery or Administrators, receives a connect ACE. It accepts an advance only from the Kernel SID and only from the current value to exactly the next value, then signs a canonical `freshness-witness/v1` containing deployment/store, previous/current NV value, recovery generation, transaction digest, Kernel/Identity projected heads and timestamp. It has no domain payload, database access, permission matrix, transaction ordering choice or retry policy; the Kernel remains the sole coordinator. Exact retries return the same signed witness; a different digest or generation for the same expected/current value is denied.

Every final Identity mutation and every restore binds its projected head to the current witness and may become `COMMITTED_FINAL` only after the Kernel-directed next-value witness is published and verified by both services. The Kernel may finalize only that same witness. Both databases and the external anchor store the witness digest/value, but the authoritative monotonic value remains in TPM outside both recovery sets. Startup compares both stores and anchor with a fresh TPM read and signed witness; any older, newer, missing or differently bound state fails closed. Thus rolling Kernel and Identity stores/anchors back together cannot roll back the TPM value.

TPM counter advancement is irreversible. Before requesting it, Identity must already have durable `ANCHOR_PENDING` state and Kernel durable PENDING; after advancement, recovery may only finish anchor finality and Kernel finalization for the exact transaction digest. It may never abort to a prior generation. If the TPM reports advancement but the signed witness is unavailable, the Key Custodian reconstructs only the exact witness from its protected append-only request/result journal and TPM value; mismatch or journal loss requires Owner-governed recovery. Key Custodian journal backup is separately retained and is not part of either Kernel or Identity recovery set.

No file counter, registry value, comparison of the two databases, administrator assertion or software-only HMAC may substitute for the TPM witness. Before implementation, the operational campaign must prove the host TPM supports an NV counter with the required ACL/policy and loss/recovery behavior. If it does not, status is `BLOCKED_ARCHITECTURE` until the Owner approves a different independently non-rollbackable authority; implementation may not weaken C09.

## Compatibility and lifecycle

- Contract `1.0` is exact; there is no version negotiation, downgrade or permissive unknown-field handling.
- A future version uses a different pipe name and contract identifier and requires explicit compatibility tests and governed activation.
- Unsupported clients receive `UNSUPPORTED_CONTRACT` without execution.
- Internal database schemas, filesystem paths and Python classes are not public API.
- Later modules may use only the versioned Kernel-facing interface; they may not connect directly to the Identity pipe or either database.
- After acceptance, non-breaking improvements are tracked separately. OI-0002 reopens only for a demonstrated defect invalidating acceptance evidence.

## Required implementation verification

Unit/contract tests must cover the normative golden wire vectors, closed enums, size/depth limits, version rejection, digest validation, transaction conflicts, idempotent exact retries, permission mapping and every crash boundary.

The disposable operational campaign must use the four actual Windows principals and preserved custody topology:

- `AITaxKernel`: mutual-authenticated positive connection and authorized operations;
- `AITaxIdentity`: server ownership, own-store-only access and rejection of self-client authority;
- `AITaxKeyCustodian`: pipe connection denied; key custody remains unchanged;
- `AITaxRecovery`: data-plane pipe connection denied; exact authorized restore succeeds only through Kernel;
- unrelated user/Administrator/remote client: connection or token authentication denied;
- both services: process termination at every tabled boundary, restart reconciliation, communication interruption and exact retry;
- populated backup/restore, interrupted restore, unauthorized restore and old-generation rollback;
- cross-case/year/task/manifest/capability substitutions and transaction-ID replay;
- PREPARE followed by missing, fabricated, expired, wrong-transaction/head/deployment or pre-durable-PENDING reservation proof;
- authorization/Kill Switch/manifest/task/role/capability/evidence/Human Gate revocation or expiry between PREPARE and COMMIT and during either restart order;
- anchor create/flush/replace/directory-flush/reread/receipt-consumption faults, proving Kernel remains PENDING until `COMMITTED_FINAL`;
- a two-case deployment where case-A authority attempts physical replacement, plus missing/extra/changed entries in the complete case-generation manifest;
- coordinated rollback of matching Kernel DB, Identity generation and anchor after TPM advancement, plus Kernel-only, Identity-only and mixed-generation rollback;
- TPM unavailable/cleared/reprovisioned, wrong public identity, skipped value, substituted transaction digest, repeated advance and journal-loss scenarios;
- exact canonical JSON golden vectors and every malformed/split/concatenated frame listed in the wire section;
- audit correlation with no sensitive payload;
- focused, security and complete regression suites.

Operational evidence must bind contract version, exact implementation SHA, service executable hashes, manifest/deployment identity, principal SIDs, transaction IDs, scenario outcomes and result hashes. It must not contain credentials, key bytes or taxpayer data.

## Independent-review remediation traceability

| Finding | Contract correction | Mandatory acceptance evidence |
| --- | --- | --- |
| F01 | Row-derived signed `reservation-proof/v1`, issued only after durable PENDING reread and verified by Identity without Kernel DB access | Missing/fabricated/pre-commit/wrong-binding/expired proof denied; exact proof survives restart reconciliation once |
| F02 | Serializable signed `commit-permit/v1`, five-second fence, complete authorization revalidation and restart-safe one-time restore use | Every authorization dimension revoked/expired between PREPARE and COMMIT is denied under both restart orders |
| F03 | `ANCHOR_PENDING` is explicitly non-finalizable; only verified published anchor plus consumed receipt becomes `COMMITTED_FINAL` | Fault every anchor durability boundary and prove Kernel remains PENDING |
| F04 | Physical restore is deployment-store scoped and binds the complete affected-case generation manifest | Case-only authorization and missing/extra/substituted case entries cannot replace a multi-case store |
| F05 | TPM 2.0 NV counter and Key-Custodian-signed witness live outside both rollbackable recovery sets | Coordinated old Kernel+Identity+anchor pair is detected after TPM advancement; unavailable/reset TPM fails closed |
| F06 | RFC 8785 strict profile, exact digest bytes, one-frame-per-message rules and normative vectors | Cross-implementation golden vectors and all malformed/split/oversize/Unicode/numeric cases agree or reject |

## Security properties and residual decisions

This design intentionally provides no distributed atomic transaction. Safety comes from Kernel coordination, row-derived signed reservation/authorization proofs, durable prepare/idempotency records, exact head projection, non-finalizable anchor state, the independently monotonic TPM witness and deterministic reconciliation. Availability is subordinate to integrity: ambiguity stops the affected operation.

Implementation may choose Win32 bindings already available to the project runtime or a minimal reviewed `ctypes` boundary. It may not substitute a shared secret for token authentication or silently add a third-party IPC framework. Exact service installation/start authority remains governed separately from code implementation and testing.

F01–F06 are addressed at architecture-contract level in this revision, but this is self-review evidence only. Implementation is forbidden until a new independent architecture/security reviewer returns PASS on the exact remediation commit. TPM capability and custody must be proven in that review/operational preflight; absence is `BLOCKED_ARCHITECTURE`, not a fallback authorization.
