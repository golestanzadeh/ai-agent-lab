# C09 Kernel–Identity operational boundary and witness finality architecture

Date: 2026-10-22  
Contract: `oi0002.kernel-identity-c09/1.0`  
Status: `REMEDIATED_F01_F06 / INDEPENDENT_ARCHITECTURE_REREVIEW_REQUIRED / NOT IMPLEMENTED`

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

The Identity service creates one fixed deployment-scoped pipe using `PIPE_TYPE_MESSAGE`, `PIPE_READMODE_MESSAGE`, bounded instances, `PIPE_REJECT_REMOTE_CLIENTS` and `FILE_FLAG_FIRST_PIPE_INSTANCE`. Failure to acquire the first instance is a fatal start condition. The DACL omits Users, Administrators, Recovery and Key Custodian from data-plane access. Service installation pins the protected absolute image path and SHA-256 for the Identity executable; an approved binary update atomically replaces those manifest values under the existing Human Gate before service restart.

For every connection Identity calls `ImpersonateNamedPipeClient`, reads `TokenUser` from the thread token, compares the binary SID to the pinned Kernel SID and executes `RevertToSelf` in `finally` before dispatch. Kernel obtains the connected server PID, opens a query-only process handle immediately, re-reads the connected PID and rejects turnover, then verifies from that retained handle the exact Identity SID, protected normalized image path and SHA-256 against the manifest before sending a request. Failure to open/inspect the handle, path/hash mismatch, PID turnover or service-image update race closes the connection. Pipe DACL, first-instance ownership, local-only mode, token identity and retained-handle binary identity are independently mandatory. PID alone is never authority.

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
4. Identity `COMMIT` verifies the proof and exact prepared row and, in one `BEGIN IMMEDIATE` SQLite transaction, compares the live epoch/head to the prepared predecessor, atomically claims the unique `(deployment_id, predecessor_epoch, predecessor_head)` commit slot, consumes the one-time proof, applies the mutation once, appends its audit record and stores `IDENTITY_COMMITTED`. It also stores an authenticated staged receipt containing transaction/request/result digests, prior/new Identity heads, Kernel pending head, backup generation and the digest of an exact canonical **unsigned witness preimage**. Two preparations may project from one predecessor, but exactly one COMMIT can claim it; every loser returns `CONTINUITY_CONFLICT` without domain/audit mutation. The claim and all mutation effects roll back together on failure.
5. Kernel verifies the staged receipt and asks Key Custodian to authenticate only that exact preimage through the closed protocol below. The final record is the canonical preimage plus the returned authentication fields. Kernel requires exact preimage reproduction and binds both `preimage_digest` and `signed_record_digest`; adding or substituting any other field or serialization is denied. Kernel uses the existing writer credential to perform GCS conditional create for the exact epoch/sequence key, then uses the separately scoped reader credential to enumerate versions and read back the exact generation and bytes. It verifies schema, authentication, contiguous chain, previous commitment, generation uniqueness, no deletion ambiguity and every local-head binding.
6. Kernel records the verified witness key, generation and commitment in its durable transaction and requests Identity finalization with that exact evidence. Identity binds it to the staged receipt and advances to `COMMITTED_FINAL` without repeating the mutation.
7. Kernel rereads `COMMITTED_FINAL`, verifies result/head/receipt/witness bindings, records Kernel `COMMITTED`, releases the authorization reservation and only then acknowledges success.

An exact retry returns the recorded outcome. Reuse of a transaction or operation ID with different canonical bytes is a security denial. A fresh transaction cannot redefine an existing immutable identity/fact/evidence reference.

## Witness trust and key custody

The object key, canonical record and chain rules are exactly those in `WITNESS_PROTOCOL_SPEC.md`. Conditional create plus strong read/list consistency arbitrates one exact sequence position; version enumeration rejects replacement, extra generations and delete ambiguity. Startup and restore verify the complete contiguous chain and compare its final deployment/epoch/heads/generation to both local stores before enabling protected writes.

The writer credential may create only new objects under the deployment prefix and cannot read, overwrite, delete, alter retention or administer IAM. The reader credential may list versions and read exact generations but cannot write or administer. Record-authentication authority and Owner restore authority are separate. Key Custodian signs/MACs only a Kernel-authorized canonical witness digest after verifying the exact staged receipt; it cannot choose an operation or sequence.

Independent custody, IAM bindings, durable key provisioning and retention locking are Human Gates. Until those gates are approved and operationally proven, this architecture may be implemented and tested only with synthetic fixtures and non-privileged mocks; it cannot claim C09 operational acceptance.

### Closed Kernel–Custodian authentication protocol

The Key Custodian owns a second fixed local message-mode Named Pipe. Its server uses first-instance, remote-rejection, DACL and actual-client-token checks identical to the Identity server, allowing only the pinned Kernel SID. Kernel verifies the retained Custodian server process handle, SID, normalized protected image path and executable SHA-256 exactly as above. Identity and Recovery cannot connect. No signing key or reusable secret crosses the pipe.

Request contract `ai-tax-agent.c09-custodian/1.0` has exactly: `message_type=AUTHENTICATE_WITNESS`, deployment ID, transaction ID, request digest, staged-receipt digest, unsigned-preimage digest and canonical unsigned preimage, expected epoch/sequence/previous commitment, Kernel pending head, Identity new head, backup generation, random 32-byte nonce, `issued_at`, `expires_at` (maximum five seconds), Kernel authorization-proof digest and Kernel signature. The Kernel signature is made from a reread durable PENDING row plus the Identity staged-receipt digest; Custodian verifies the pinned Kernel public key and every redundant equality before signing/MACing.

Response contains exactly contract, transaction ID, request/preimage/receipt digests, nonce, key ID, algorithm, authentication value, signed-record digest and one closed outcome (`AUTHENTICATED`, `VERIFIED`, `DENIED`, `CONFLICT`) with one privacy-minimized denial code. Algorithm is `HMAC-SHA-256` for v1; key ID is manifest-pinned and unknown, retired or mismatched IDs are rejected. Custodian durably records `(deployment_id, transaction_id, preimage_digest, nonce)` before returning. Exact retries return identical evidence; changed retries, expired requests, reused nonce/transaction for another digest, wrong sequence/head, wrong SID or invalid Kernel proof are denied and audited. Custodian cannot allocate sequence, select operations or advance Kernel/Identity state.

`VERIFY_WITNESS` is the only second request type. It contains the exact authenticated record bytes read from GCS, object key, generation, expected preimage/receipt/signed-record digests, expected chain predecessor, Kernel proof and fresh nonce/expiry. Custodian parses the record canonically, selects only the manifest-pinned active HMAC key, verifies the MAC in constant time, recomputes both digests, and returns `VERIFIED` bound to all inputs. It never returns the key. Exact retry is idempotent; changed bytes/generation/key/nonce or stale proof denies. Kernel may finalize only after its own object-key/generation/byte comparison and a matching `VERIFIED` response. Custodian outage or ambiguous response leaves Kernel PENDING.

## Frozen operational protocol appendix

The Identity pipe contract is `oi0002.kernel-identity-c09/1.0`; the development-only `oi0002.kernel-identity-ipc-dev/1.0` is always rejected operationally. It reuses the accepted canonical JSON/frame bounds (one frame, payload `1..65,532`, nesting at most 12, no duplicate/unknown fields) and exact UUID/digest/timestamp rules.

Every request has exactly: `contract`, `message_type`, `transaction_id`, `request_digest`, `deployment_id`, `scope_kind`, `case_id`, `tax_year`, `run_id`, `task_id`, `manifest_id`, `actor_instance_id`, `role_id`, `capability`, `domain_operation`, `expected_epoch`, `expected_head`, sorted unique `authorization_references`, `expires_at`, and closed operation-specific `payload`. Backup/restore uses `DEPLOYMENT_STORE` with literal `*` case/year and a complete ordered generation manifest; other operations use `CASE_YEAR`. Required strings are `1..256` UTF-8 bytes except canonical digests and UUIDs; arrays contain at most 64 entries; the restore generation manifest contains at most 1,024 unique sorted cases.

The exact message/operation/capability matrix is:

- mutation operations map exactly: `REGISTER_IDENTITY→identity_create`, `UPDATE_IDENTITY_STATUS→identity_status_transition`, `BIND_PARTY→case_party_bind`, `CORRECT_PARTY_ROLE→identity_update`, `BIND_FACT→subject_fact_bind`;
- `READ_CASE_IDENTITY`, `LIST_PARTIES`, `READ_FACTS` map exactly to `identity_read` and only `READ_IDENTITY_STATE`;
- `GET_TRANSACTION` and `ABORT_PREPARED` retain the capability of the original transaction and require exact task/manifest/run binding; no generic transaction capability exists;
- `BACKUP_DEPLOYMENT_STORE` and `RESTORE_DEPLOYMENT_STORE` are reserved and always `AUTHORIZATION_DENIED` in v1 because the accepted Permission Matrix contains no backup/restore capabilities. Enabling them requires a separately approved Owner/Human-Gate amendment naming exact capabilities, a contract minor-version change and independent re-review.

Unknown, aliased or crossed message/operation/capability combinations are denied. State transitions are exactly `NEW→PREPARED→IDENTITY_COMMITTED→COMMITTED_FINAL`; `PREPARED→ABORTED` is the only abort, and `IDENTITY_COMMITTED` cannot abort or return a final result. Exact retries may observe but not repeat a transition.

Every request contains `kernel_proof`, an object with exactly `proof_version`, `key_id`, `algorithm`, `pending_row_digest`, `authorization_state_version`, `nonce`, `issued_at`, `not_after`, and `signature`. COMMIT additionally carries `prepared_request_digest` and must equal the PREPARE digest stored by Identity; the mutation payload digest is frozen in that PREPARE row. GET/ABORT carry the original transaction/request digests and an empty payload. Proof omission, placement elsewhere, extra fields or a proof whose signature does not cover the complete outer request-without-signature is denied.

Operation-specific payloads are closed reference envelopes; protected values remain resolved by Identity from immutable references:

- `REGISTER_IDENTITY`: exactly `request_id`, `subject_id`, `identity_record_ref`, `evidence_refs`;
- `UPDATE_IDENTITY_STATUS`: exactly `request_id`, `subject_id`, `from_status`, `to_status`, `effective_date`, `evidence_refs`;
- `BIND_PARTY`: exactly `request_id`, `subject_id`, `party_role`, `valid_from`, `valid_to_exclusive`, `evidence_refs`;
- `CORRECT_PARTY_ROLE`: exactly `request_id`, `prior_binding_ref`, `replacement_binding_ref`, `effective_date`, `evidence_refs`;
- `BIND_FACT`: exactly `request_id`, `subject_id`, `fact_envelope_ref`, `valid_from`, `valid_to_exclusive`, `evidence_refs`;
- reads: exactly `subject_id`, `as_of_date`, with empty string permitted only for an operation-defined optional value;
- transaction control: exactly `original_request_digest`;
- reserved backup/restore: payload must be empty and is denied before dispatch in v1.

Identifiers/references are `1..256` bytes and match the existing registry formats; dates are canonical `YYYY-MM-DD`; statuses and party roles use their existing closed Persistence Contract enums; `evidence_refs` is sorted unique with `1..64` immutable references. Missing, duplicate, unknown, malformed or empty required values are denied. PREPARE and COMMIT must have byte-identical operation, scope and payload digests.

Responses have exactly: `contract`, request `message_type`, `transaction_id`, `request_digest`, `outcome`, `response_digest`, `identity_epoch`, `identity_head`, `staged_receipt_digest`, `witness_preimage_digest`, `signed_record_digest`, and `denial_code`. Closed outcomes are `PREPARED`, `IDENTITY_COMMITTED`, `COMMITTED_FINAL`, `READ_OK`, `ABORTED`, `DENIED`, `CONFLICT`, `NOT_FINALIZABLE`. Closed denial codes are `AUTHORIZATION_DENIED`, `SCOPE_DENIED`, `TRANSACTION_CONFLICT`, `CONTINUITY_CONFLICT`, `REQUEST_INVALID`, `EXPIRED`, `UNSUPPORTED`, `TEMPORARY_FAILURE`. Nonapplicable fields are the empty string, never omitted/null; DENIED/CONFLICT disclose no heads. The exhaustive allowed matrix is: PREPARE→`PREPARED|DENIED|CONFLICT`; COMMIT→`IDENTITY_COMMITTED|COMMITTED_FINAL` (exact retry only)`|DENIED|CONFLICT|NOT_FINALIZABLE`; READ→`READ_OK|DENIED|CONFLICT`; GET→the exact durable state outcome or `DENIED|CONFLICT`; ABORT→`ABORTED|DENIED|CONFLICT|NOT_FINALIZABLE`; reserved backup/restore→`DENIED` only in v1. Every other pair is invalid before audit/result persistence.

Kernel proofs use manifest-pinned ECDSA P-256/SHA-256 fixed 64-byte `r||s`, base64url without padding, domain separator `AI-TAX-AGENT\0C09-KERNEL-PROOF\0`, key ID and exact canonical unsigned-proof bytes. Unknown algorithm/key, downgrade, retired key, noncanonical signature or key rotation during a transaction is denied; rotation requires a governed manifest generation and no nonterminal transactions. Golden vectors must freeze complete requests, responses, Kernel proofs, Custodian requests/responses and witness preimage/final records before implementation acceptance.

## Independent Owner restore authorization profile

Owner restore authority is not a rollbackable Kernel row. Canonical contract `ai-tax-agent.owner-restore/1.0` contains exactly: authorization ID, deployment ID, source witness key/generation/commitment, source epoch and both local heads, target epoch, backup digest/generation, complete ordered case-generation-manifest digest, recovery-operator SID, random 32-byte nonce, `issued_at`, `not_before`, `expires_at`, Owner key ID, algorithm and signature. The signature is ECDSA P-256/SHA-256 fixed `r||s` over domain `AI-TAX-AGENT\0OWNER-RESTORE\0` plus canonical unsigned bytes. The pinned Owner public key is readable by Kernel/Custodian; the private key is offline and outside local/cloud service backups and all four runtime principals.

Kernel verifies signature, key ID, scope, source witness and time before reserving. A signed revocation using the same key and authorization ID may be placed in the witness control prefix; inability to enumerate and verify the control prefix denies restore. Revocation or expiry before witness creation aborts the inactive staging. The RESTORE witness record carries the authorization digest, making consumption externally non-rollbackable; startup rejects any authorization digest already present in the verified chain even if local consumed state was rolled back. A governed key rotation pins old/new public keys and activation time in an Owner-signed transition; unknown, prematurely active or retired keys deny. No local database row alone establishes Owner authority.

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

Restore is deployment-store scoped. It requires an unexpired, one-time Owner authorization bound to source/target epoch, complete case-generation manifest, backup digest/generation and expected witness head. Kernel first reserves that authorization as `RESTORE_RESERVED` for one restore transaction. Both services independently stage and fsync exact generation directories and record `RESTORE_STAGED`; neither active pointer changes. Identity verifies the complete staged store and returns its projected head. Kernel constructs and obtains authentication for the exact `RESTORE` witness preimage, conditionally creates and reads back the witness, then durably records `RESTORE_WITNESSED`.

Activation order is Identity pointer first, then Kernel pointer, each by atomic replace plus directory flush and reread, recording `IDENTITY_ACTIVATED` and `KERNEL_ACTIVATED`. While either pointer differs from the witnessed generation both services remain recovery-only and protected reads/writes are denied. On restart, the exact witnessed record plus staged-generation hashes authorizes completing missing pointer activations; absence/ambiguity of witness before activation causes staged data to remain inactive; one active pointer without the exact witness halts for Human recovery and never rolls back or accepts mixed state. After both pointers and heads match the witness, Kernel marks `RESTORE_FINAL`, Identity marks the authorization use consumed, and Kernel marks the Owner authorization consumed. The same reserved use may resume only this transaction; it cannot authorize another generation. Reuse, partial-store restore or any mismatched case/generation entry is denied. Retention lock or destructive recovery remains a separate Human Gate.

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
