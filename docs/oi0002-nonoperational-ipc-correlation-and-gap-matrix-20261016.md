# OI-0002 non-operational IPC correlation and operational gap matrix

Date: 2026-10-16  
Implementation baseline: `f0926a0223136fc9908c5d5da585b6b67443dee7`  
Implementation commit: `6a8ca48e10bbaed96dadacc24609d5daa0f6724f`  
Status: `INDEPENDENT_IMPLEMENTATION_PASS / NON-OPERATIONAL`

## Admission and scope

Authenticated Codex telemetry measured 98% five-hour and 100% weekly remaining at `2026-10-16T18:21:53.838459Z`. The existing deterministic `BOUNDED (15/5)` Limit Guard returned `RUN_OPERATION_FITS`, preserving the mandatory 15-point five-hour reserve. The clean isolated worktree and remote baseline were exact before implementation; unrelated worktrees and changes were not touched.

This package adds only a pure, stateless response validator. It creates no transport, listener, credential, peer authentication, authorization decision, dispatch, persistence, mutation, finality, backup or restore surface.

## Protocol result

`src/agent_lab/ipc_response.py` reuses the accepted canonical JSON and single-frame primitives and correlates responses to an already validated `ValidatedEnvelope`. The response schema is closed to these exact fields: contract, message type, transaction ID, request digest, outcome, response digest, Identity epoch/head and denial code.

- Correlation binds the exact contract, request message type, transaction ID and canonical request digest.
- The request-message/outcome matrix is closed: five request message types admit only their explicitly enumerated outcomes.
- Denials use exactly eight privacy-minimized codes: `AUTHORIZATION_DENIED`, `SCOPE_DENIED`, `TRANSACTION_CONFLICT`, `REQUEST_INVALID`, `CONTINUITY_CONFLICT`, `EXPIRED`, `UNSUPPORTED`, and `TEMPORARY_FAILURE`.
- A denial must contain one allowed denial code and must not disclose Identity epoch/head. A non-denial must contain no denial code and must contain a valid epoch/head.
- The response digest covers every other canonical response field. Noncanonical frames, duplicate/unexpected/missing fields, mismatches, malformed identifiers/digests/state, unsupported values and ambiguous combinations fail closed.
- Existing complete-frame limit `65,532` bytes and canonical nesting limit `12` are reused; no competing encoding or framing authority was introduced.

## Verification and independent acceptance

Implementation verification:

- focused wire/envelope/response suite: `205 passed`, exit `0`;
- relevant Kernel/Identity/continuity/evidence/custody regression: `302 passed`, exit `0`;
- `git diff --check`: PASS.

Independent reviewer `/root/ipc_response_independent_review` reviewed exact commit `6a8ca48e10bbaed96dadacc24609d5daa0f6724f`, made no changes and returned `INDEPENDENT_IMPLEMENTATION_PASS` with no findings. The reviewer independently reproduced `205 passed` focused and `302 passed` relevant regression results, verified five request types, 14 permitted relationships, 16 forbidden relationships and all eight denial codes. This acceptance is limited to the development-only component and grants no C09, frozen C01-C13 or operational IPC acceptance credit.

## Operational IPC dependency matrix

The classification records the strongest current evidence. “ACCEPTED” below means accepted only for the explicitly bounded development component unless the dependency column says otherwise.

| Component | Classification | Exact acceptance dependency | Responsible authority |
|---|---|---|---|
| Canonical wire/framing | ACCEPTED | Development primitive is independently accepted; operational use still requires an accepted authenticated transport profile and integration evidence. | Independent implementation/security reviewer; operational Owner gate remains separate. |
| Versioned envelope validation | ACCEPTED | Development contract `oi0002.kernel-identity-ipc-dev/1.0` is independently accepted; operational contract/version and authenticated dispatch remain gated. | Independent implementation/security reviewer; Owner for operational architecture. |
| Correlation and outcome validation | ACCEPTED | Exact-SHA independent PASS for the stateless development validator; operational outcomes require real Kernel-owned dispatch and durable transaction evidence. | Independent implementation/security reviewer; Kernel authority for later integration. |
| Authenticated peer identity | BLOCKED | Approved portable operational peer-authentication profile and real-token evidence are absent; Named Pipe/service activation is not authorized. | Owner architecture decision, then independent architecture/security review. |
| Least-privilege capability enforcement | TESTED | In-process Kernel permission controls have tests, but cross-process enforcement depends on authenticated peer identity and Kernel-owned dispatch. | Deterministic Orchestrator Kernel plus independent security reviewer. |
| Kernel-owned dispatch | NOT STARTED | Requires independently accepted operational IPC architecture and authenticated peer context; Kernel must remain sole coordinator. | Owner architecture gate, Kernel implementer, independent reviewer. |
| Transaction isolation and idempotency | TESTED | Component-level persistence/continuity tests exist; cross-process proof requires Kernel dispatch, durable request identity and crash/replay campaign. | Kernel and Identity authorities, then independent acceptance. |
| Durable audit and evidence lineage | TESTED | Existing authorities have component tests; IPC correlation and cross-service durable audit continuity are not operationally integrated. | Evidence/Identity authorities and independent security review. |
| Protected persistence | BLOCKED | Current instruction forbids activation; requires accepted peer authentication, dispatch, custody and operational campaign. | Owner/Human Gates and independent operational acceptance. |
| Recovery and rollback-resistant finality | BLOCKED | No approved independently non-rollbackable freshness authority exists on this host; GitHub history is insufficient and TPM is not available/mandatory for development. | Owner architecture decision followed by independent ADR review. |
| Windows/Docker deployment | NOT STARTED | Operational service topology, token authentication and least-privilege deployment need an accepted portable architecture before implementation. | Owner architecture gate, deployment/security reviewer. |
| Future laptop/VPS migration | BLOCKED | Requires approved freshness/restore authority, monotonic-generation policy and governed migration evidence; silent reinitialization is forbidden. | Owner/Human Gate and independent recovery review. |

## Continuation decision

No further operational-gap package is prerequisite-ready without a new Owner architecture decision. The next direct dependencies—authenticated peer identity and Kernel-owned dispatch—would cross the unaccepted operational architecture boundary, while another synthetic validator lacks a demonstrated architectural need. The exact next action is therefore: Owner selects a portable independently non-rollbackable freshness/restore authority compatible with the existing Windows/Python/Docker baseline and future laptop/VPS migration; the IPC ADR is then revised and independently security-reviewed before any operational implementation. C09 remains `OPEN / NOT ACCEPTED` but does not block unrelated independently safe development.
