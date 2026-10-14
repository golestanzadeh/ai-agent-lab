# OI-0002 non-operational IPC envelope validator — 2026-10-14

Status: **INDEPENDENT_IMPLEMENTATION_PASS / NON-OPERATIONAL / NO C03-C12 ACCEPTANCE CREDIT**

Baseline: `f9a0a3f49710b68ba982e113ee7bc1830e62a1db`

Final implementation SHA: `af99001d2dbe0f1cdfb9a136e870bd51d4019d10`

## Contract

The exact development contract identifier is `oi0002.kernel-identity-ipc-dev/1.0`. It reuses the accepted canonical JSON and framing primitives and has no transport or execution behavior.

Required envelope fields bind contract/message, lowercase UUIDv4 transaction, exact request digest, deployment/case/year/run/task/manifest, actor/role, capability/operation, expected epoch/head, sorted unique authorization references, exact UTC expiry and an empty payload.

The profile permits only `CASE_YEAR`; deployment-store scope, backup and restore are rejected. Payload must be `{}` so protected domain data or caller-supplied commands cannot cross this development boundary.

Closed message/operation matrix:

- `PREPARE_MUTATION`, `COMMIT_MUTATION`, `GET_TRANSACTION`, `ABORT_PREPARED`: the five mutation operations only;
- `READ_IDENTITY_STATE`: the three read operations only.

Every operation binds one existing dedicated capability. Unknown versions, messages, operations, fields, capabilities and mismatched pairs fail closed. The request digest covers every other canonical envelope field and is compared in constant time.

## Independent review and remediation

Initial implementation `6d0f6f724cc07b033c019405e89b791c3ce5d22c` failed independent review because `ABORT_PREPARED` and `GET_TRANSACTION` accepted read operations through fallthrough. That violated the closed state-machine claim and created future confused-dispatch risk.

Remediation `af99001d2dbe0f1cdfb9a136e870bd51d4019d10` introduced an explicit message-operation matrix. Tests exhaustively accept all 23 permitted pairs and reject all 17 forbidden pairs. Independent re-review returned PASS with no remaining finding.

## Verification

- focused wire/envelope tests: `114 passed`, exit 0;
- relevant wire/envelope/Kernel/continuity/Identity/evidence/custody regression: `211 passed`, exit 0;
- operational and unknown contract versions rejected;
- backup/restore and deployment-store scope rejected;
- missing, unexpected, malformed and substituted fields rejected;
- noncanonical/duplicate wire representations rejected by the reused primitives;
- source inspection confirms no transport, peer authentication, dispatch, persistence, transaction execution, mutation, finality, backup or restore surface.

## Preserved boundary and continuation

C09 remains OPEN / NOT ACCEPTED. No replacement freshness authority is approved. This package earns no operational IPC, frozen-matrix or OI-0002 acceptance credit.

The next independently executable candidate is a stateless request/response correlation validator with closed outcome and privacy-minimized denial codes. It must not become a dispatcher, authority, transaction store or finality mechanism, and requires fresh Limit Guard admission and independent review.
