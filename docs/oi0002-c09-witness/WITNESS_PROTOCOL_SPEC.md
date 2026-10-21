# C09 external freshness witness protocol v1 — non-operational design

Status: `DESIGN / LOCAL_SIMULATION_ONLY / C09_OPEN`

## Security objective and trust boundary

Before any protected operation is acknowledged, a witness outside the rollback domain of both local stores must contain one authenticated successor record. The Kernel remains the sole transaction coordinator. The witness only arbitrates a unique append position; it cannot authorize an Identity mutation, schedule work or replace Kernel policy.

Required independent assumptions are: (1) provider conditional-create and strongly consistent reads/listing behave as documented; (2) the witness account, retention administration and record-authentication key are outside the local backup/restore domain; and (3) an attacker cannot simultaneously control the provider administration plane and the independent signing/Owner-restore keys. Violation of an assumption yields denial or loss of rollback detection; no object-store design proves correctness against provider compromise.

## Record contract

Canonical JSON is UTF-8, lexicographically sorted by key, with no insignificant whitespace, duplicate keys, floats or Unicode normalization ambiguity. Maximum encoded size is 4096 bytes. The exact object key is:

`witness/v1/<deployment-id>/epoch-<20-digit-epoch>/sequence-<20-digit-sequence>.json`

Required fields are: protocol `ai-tax-agent.c09-witness/1`; deployment ID; positive epoch and sequence; SHA-256 previous-record commitment; Kernel audit/head commitment; Identity audit/head commitment; nonnegative backup generation; opaque operation ID; closed record type (`COMMIT` or separately governed `RESTORE`); optional Owner-authorization digest; and `HMAC-SHA-256` over domain separator `AI-TAX-AGENT\0C09-WITNESS\0` plus the canonical unsigned record.

Identifiers contain no case, taxpayer, document or personal value. Heads and authorization references are cryptographic commitments. Operational deployment should replace the simulation HMAC with an independently custodied signing/MAC service profile; choice of HSM/KMS/key ownership is an Owner architecture decision.

## Append and fork rule

For one deployment and epoch, sequence starts at 1 and has no gaps. The writer creates the one exact sequence key only with provider conditional-create (`ifGenerationMatch=0` on GCS; `If-None-Match: *` on S3). A second writer for the same sequence must fail. Verification enumerates all versions, rejects delete markers, multiple versions, missing sequences, duplicate sequences, invalid authentication, wrong previous commitment and unexpected epoch transitions.

This is linearizable only under the provider's per-key conditional-write plus strong read/list consistency guarantees and a policy that prevents deletion/version substitution throughout the required evidence lifetime. A generic append-only namespace with arbitrary record names is **not** a global linearizable head: concurrent writers can create two valid successors. A compromised cloud writer without the authentication key can pre-create invalid/future keys and cause fail-closed denial of service, but cannot forge a valid successor. Compromise of both writer and authentication authority defeats this profile.

## Protected-operation state machine

1. Kernel validates exact case/task/manifest/run/operation authority and durably records `PENDING` with expected local heads and operation ID.
2. Identity performs one authenticated idempotent local commit bound to that `PENDING`; the operation is locally committed but not final.
3. Kernel constructs and durably stages the canonical witness record; no user acknowledgement is allowed.
4. Witness conditional-create succeeds, then exact generation/version and bytes are read back and verified. The operation is externally anchored but not yet locally final.
5. Kernel durably records `COMMITTED`, exact witness key/version/commitment and new local heads.
6. Only after step 5 may the operation be acknowledged as finalized.

Witness failure or ambiguity leaves the operation unacknowledged and fail-closed. Identity commit without witness requires governed reconciliation; it must never be silently replayed. Witness acceptance without Kernel finalization is completed on recovery only after exact pending/Identity/head verification.

## Existing reuse and missing integration

Reuse: Kernel `PENDING→COMMITTED` continuity primitives, exact task/manifest/run binding, Identity idempotency, audit heads, backup generation, one-time expiring restore authorization, canonical JSON/framing and closed IPC outcomes.

Missing: provider adapter, independent key custody, provider policy/configuration verifier, version-aware readback, operational service identity, durable staged-witness receipt, recovery integration, Owner restore signature profile, live provider tests and four-principal independent acceptance. No production path is changed by the simulator.
