# F07 governed runtime activation preparation

## Final bounded F07 integration outcome — 2026-10-27

Overall mission: `BLOCKED_SPEC_GAP / LOGICAL_CONTINUITY_BOOTSTRAP`. Safe components: `INDEPENDENT_BOUNDED_IMPLEMENTATION_PASS` at exact4052b5b32b48617920959bbc2c822f06caf5cced, separate read-only reviewer `/root/c09_architecture_independent_review`. No full F07 implementation/operational PASS is claimed. No residual defect was reproduced in the bounded components. Source/contract/fixtures at the reviewed commit are unchanged by final reporting.

| Phase | Actual completed scope / boundary |
| --- | --- |
| A client/transport | Operational read-only closed schema/proof/response validation, golden-vector compatibility, strict configured scope and canonical bytes; native authenticated server exchange. No proof signer or authority grant. |
| B deadline/cancel | Shared monotonic connect/write/read deadline, explicit cancellation, peer-process/token retention, bounded cancellation acknowledgement, buffer/handle quarantine and sticky transport halt on ambiguous unacknowledged I/O; no automatic retry. Cleanup acknowledgement has a bounded one-second grace after operation expiry. |
| C dispatcher | Actual Kernel token checked before parsing; signed schema validated; existing IdentityPersistence durably records privacy-minimized refusal before returning correlated DENIED/TEMPORARY_FAILURE. Cannot call domain read, return READ_OK or consume an operational proof. |
| D SCM/stateful composition | Not implemented/accepted: blocked at logical-continuity/genesis contract mapping below. Existing fail-closed entrypoints remain; no fake replacement runtime was wired. |
| E verification | Worker final372 F07/IPC/host,88 Kernel/Identity/F06/F07 regression and18 documentation passed; independent73 focused/native passed; no real four-principal/SCM or protected-data acceptance. |
| F independent review | Bounded PASS only; no self-approval, service/cloud/protected-state action or operational acceptance. |

Implementation lineage: c5b494712b609dfa3cc81d586920e282aeb9351e (client/schema/native transport), 9fa9394d78c8c5cadb53de8043bb8aa46650611e (audited denial and precise state-mapping stop), 4052b5b32b48617920959bbc2c822f06caf5cced (adversarial/read-specific/audit-failure evidence and normalized errors). Independent initial9fa review found medium malformed outgoing frame ValueError leakage before the closed PipeSecurityError boundary;4052 corrected c09_pipe_transport.py lines76–77. No residual bounded finding remained.

Independent commands, PYTHONPATH=src;tests/unit, exact4052:

- `python -m pytest -q -p no:cacheprovider --basetemp C:\Users\rezag\ai-agent-lab\.tmp-f07-independent-review tests/unit/test_f07_operational_read.py`:63 passed, exit0.
- Same command with `tests/unit/test_f07_native_transport.py`:10 passed, exit0; actual Windows Named Pipes outside process isolation, current-user-only ephemeral endpoints, not service principals.
- `git diff --check 9fa9394d78c8c5cadb53de8043bb8aa46650611e 4052b5b32b48617920959bbc2c822f06caf5cced`:exit0.

Final worker command `python -m pytest -q tests/unit/test_f07_operational_read.py tests/unit/test_f07_native_transport.py tests/unit/test_f07_contract_resolution.py tests/unit/test_ipc_wire_primitives.py tests/unit/test_ipc_envelope.py tests/unit/test_ipc_response.py tests/unit/test_c09_named_pipe.py tests/unit/test_c09_pipe_transport.py tests/unit/test_c09_identity_boundary.py tests/unit/test_c09_service_host.py tests/unit/test_c09_scm_factory_wiring.py`:372 passed,exit0. Existing Kernel/Identity/runtime regression88 and documentation18 commands/results below remain valid. Native/proof/audit fault cases are development evidence, not operational activation.

Read-only SCM query opened only SCM_CONNECT and SERVICE_QUERY_STATUS for AITaxKernel and AITaxIdentity: both Windows error1060, both fixed config paths absent, current token Owner SID ending1001. No operational Kernel/Kill Switch state is available; UNKNOWN must not be interpreted as RUNNING or permission. An initial inventory invocation lacked PYTHONPATH and exited1/no evidence; corrected query exited0. No service installation, process impersonation as a service, existing ACL mutation, credential/key/cloud/provider/real taxpayer operation occurred.

### Exact next Owner decision (not approved by this report)

Choose/authorize the bounded logical-continuity contract clarification before stateful implementation. Two materially different models remain possible: **A**, one Identity-owned logical epoch/head per deployment, with exact case/year authorization and a separately bound audit head; **B**, logical epoch/head per case/year plus a defined aggregate deployment commitment for the existing Witness. Neither is silently selected; the current Kernel table is case/year-scoped while Witness has one deployment chain and conflates audit/head wording. The decision must also explicitly authorize the initial enrollment/genesis evidence of an existing populated Identity DB, then freeze canonical genesis/next-head preimages, separate audit commitments and atomic proof/domain/head/audit effects. Live enrollment remains an Owner Human Gate, not implied by approving design. No new database, orchestrator, protocol authority or arbitrary trusted-head callback is permitted.

After that bounded clarification receives independent contract acceptance, continue the same mission with versioned state in the existing service DBs, authenticated READ_OK dispatcher, Kernel proof reservation/signing and actual SCM runtime composition; then exact-SHA independent implementation and separately gated real-principal deployment tests. No new ordinary development approval or quota reset is required to repair this already-authorized mission, but unresolved contract semantics cannot be invented by the worker.

Quota is not the stop reason. Telemetry observed a reset from12%/69% to93%/99% without any agent reset call or reported service interruption. Authenticated reporting snapshot2026-10-27T13:55:03Z: five-hour88%,reset2026-10-27T18:50:02Z; weekly98%,reset2026-11-03T13:50:02Z. Owner's mission-only reserve/positive-threshold exception remains binding; no general policy was weakened. No active OPEN_ITEMS row closes. Approval, Submission, protected persistence/data/provider operations and C09/OI-0002/OI-0003 operational acceptance remain disabled/unaccepted.

## Operational integration implementation in progress — 2026-10-27

### Independently confirmed state-mapping boundary

Separate read-only reviewer `/root/c09_architecture_independent_review` confirmed `CONTRACT_DECISION_REQUIRED` for stateful operational continuity. Exact governing sources: operational architecture line 127 preserves read projected epoch/head; lines 131/181 require durable proof consumption and independent success/denial/retry audit. IdentityPersistence lines 395–425 count/MAC every audit row, so audit head advances on reads. Mapping it to logical identity_head would create stale live-head comparisons; skipping audit is prohibited. The architecture's no-caller-head/missing-authority rule (line 125), witness/local-store startup comparison (line 58), closed operation list (lines 35–38/91), and synthetic-only initialization API (identity_continuity_authority.py lines 1/23–32) prevent manufacturing genesis. Owner restore lines 153–177 require an already witnessed source and cannot authorize first enrollment.

Smallest required decision is a bounded clarification of the existing Identity-owned continuity record, not another database/authority: (1) exact deployment or case/year scope key; (2) canonical genesis preimage and authorized enrollment of existing populated v3 state, with live Owner/Human Gate; (3) canonical noncircular next-head derivation; (4) one transaction coupling domain mutation/logical head/proof consumption/audit, with reads preserving logical continuity; (5) distinct audit versus continuity commitments in witness/startup/restore. No option is marked approved. The developer cannot pick an arbitrary trusted_head callback or promote the synthetic adapter. This is a specific specification boundary, not a global development/security or quota stop.

The ambiguity is observable across the existing Witness contract too: WITNESS_PROTOCOL_SPEC.md line 17 names an `Identity audit/head commitment` without distinguishing the logical commitment that must remain stable on reads. A contract correction must define the existing field's exact commitment/preimage or obtain review for a versioned change; adding an undocumented wire field is not permitted. The Owner decision needed is authorization/approval of that precise continuity/genesis contract clarification, not another generic development approval or quota reset.

Safe interface completion adds only a denial-only operational dispatcher: actual Kernel principal first, closed signed read schema, exact configured scope, then durable metadata-only refusal through existing IdentityPersistence. The response is correlated DENIED/TEMPORARY_FAILURE with no heads/results; no accepted-domain API is invoked. Failure to persist the denial closes the request without a response. Restart readback verifies the denial audit. This does not claim proof-consumption, READ_OK dispatch, SCM/runtime composition or operational acceptance. Focused read/native/dispatcher 66 passed; existing Identity/read regressions 100 passed (exit 0). Separate exact-SHA implementation review remains pending.

Additional affected verification: `python -m pytest tests/unit/test_f07_operational_read.py tests/unit/test_f07_native_transport.py -q` now passes 73, exit 0. This adds six READ-specific crypto/scope substitutions (so mutation rejection cannot mask proof-validation checks), actual server receipt before cancellation/timeout with exactly one request, and audit-before-commit fault injection proving no response or partial audit. Malformed operational transport frames are normalized to PipeSecurityError. No new source of authority/state is introduced.

Owner's explicit current-mission exception supersedes the attachment's 15-point reserve/5% positive-threshold stop rules. Monitor authenticated telemetry but continue while execution is technically available; no automatic resets or platform bypass. This does not change security/activation/independent-review gates or other missions' quota policy.

Phase A/B candidate code extends the existing client/Named Pipe transport and adds the operational **read-only** schema profile. It validates actual canonical/digest/projection/low-S proof/result bytes against frozen synthetic evidence; no signing key, authority grant, fallback or mutation dispatcher is introduced. The client retains the authenticated server process/token through I/O, verifies SID/path/hash/PID, and uses one shared monotonic deadline for connect/write/read/authentication progress. Native overlapped I/O is cancelled and acknowledged before buffer release. If cancellation is not acknowledged, native resources are retained and transport halts instead of freeing kernel-owned buffers or retrying an ambiguous exchange. This is fail-closed diagnostic state, not another recovery authority.

Actual Windows verification uses ephemeral current-user-only test pipes and the real current Python executable token/path/hash; it does not use/activate the four frozen service principals. Ten native cases cover reply, absent endpoint, silent peer, disconnect, wrong SID/path/hash, malformed/oversized response and cancellation. Initial native execution failed five cases because the existing production first-instance constant referenced win32con instead of win32pipe; corrected and rerun. A later fixture prematurely disconnected and discarded an unread queued reply (one failure); keeping the test server alive until client completion resolved it. No origin/security check was relaxed.

Commands use PYTHONPATH=src;tests/unit:

- `python -m pytest -q tests/unit/test_f07_operational_read.py tests/unit/test_f07_native_transport.py tests/unit/test_c09_named_pipe.py`: final 75 passed, exit 0, including injected cancellation-quarantine failure.
- F07 contract + new read/native + existing IPC/named-pipe/client/SCM suite: 361 passed, exit 0 before the two last added cases; later affected focused tests above passed.
- `python -m pytest -q tests/unit/test_orchestrator_kernel.py tests/unit/test_identity_persistence.py tests/unit/test_runtime_activation.py tests/unit/test_production_runtime.py`: 88 passed, exit 0.
- `python -m pytest -q tests/unit/test_documentation_index.py`: 18 passed, exit 0 before this reporting update.

This is a coherent tested candidate milestone during continuous execution, not final handoff or F07 implementation PASS. Exact-SHA independent review, durable authority/dispatcher integration and existing SCM composition remain. No new Owner architecture decision is inferred merely from missing tables/APIs: the frozen persistence contract permits reviewed versioned extensions in the existing service databases. Head/audit binding must be resolved against actual sources before implementation; synthetic adapters cannot be promoted. No service, protected operation, credential, existing ACL or taxpayer data was changed.

## F07 contract-resolution review evidence — 2026-10-27

Scope is only existing operational contract `oi0002.kernel-identity-c09/1.0`; the development contract remains separate. Baseline c763b82502893632d8cc17c05b55c7ce69236867 and development composition 77fd630ffad62e97515c69e384b51387e77262fd were verified against remote. No production source, SCM service, privilege, key custody, protected data or operation activation changed. Architecture remains in `docs/oi0002-c09-witness/KERNEL_IDENTITY_OPERATIONAL_ARCHITECTURE.md`; no alternative architecture is created.

Gap A resolves exact outer/proof fields, top-level prepared_request_digest semantics and message/capability combinations. Gap B freezes request/content/projection digest exclusions, complete-outer domain-separated P-256 signing, low-S encoding, verification and proof renewal. Gap C uses embedded serialization of existing PersonRecord/EntityRecord, CasePartyRole and SubjectFactEnvelope returns, exact optionality, order, privacy, size limits and response digest coverage. Result-reference persistence was rejected as unsupported new domain behavior, not an equally authorized alternative.

Independent reviewer `/root/c09_architecture_independent_review` has a separate read-only context and did not author corrections. Exact initial candidate 695fb161d3a90963ed6667683206794f6c86cb3b received INDEPENDENT_FAIL:

| Finding | Exact initial location | Reproduction / correction |
| --- | --- | --- |
| F07-R01 HIGH | Architecture line 125; proof fields line 93; offline helper line 106 | Replace opaque pending_row_digest with all-zero SHA, recompute request digest and valid test-key signature: accepted without an available projection preimage. Correction transmits a closed signed kernel_projection, recomputes its hash/content/scope, and specifies own-PREPARED-plan comparison and pinned Kernel durable-row signature authority. Frozen arbitrary-digest and projection-scope substitutions now reject. |
| F07-R02 HIGH | Architecture lines 112, 120 | Replace s with n-s in a valid signature: second canonical request verified. Correction normalizes low-S generation and rejects s>floor(n/2), including the frozen mathematically valid high-S twin. |
| F07-R03 MEDIUM | Architecture line 54 versus lines 118–122 and recovery lines 159/161 | Fresh five-second proof or PREPARE→COMMIT changes bytes despite blanket changed-byte reuse denial. Correction defines immutable transaction content, stable per-stage digest, separately consumed nonce attempts, original PREPARE linkage, current reauthorization and no repeated domain effects. Tests cover expiry, fresh renewal, COMMIT renewal, changed content and consumed nonce. |

Corrected exact candidate 6c6a4d7d51070637a18517d17d418d082078b85e received `INDEPENDENT_PASS` from the same separate read-only reviewer after independent re-execution. R01/R02/R03 are closed; no scoped defect remains. Mission result is `F07_CONTRACT_INDEPENDENT_PASS`, never F07_OPERATIONAL_PASS. Reviewer did not author or approve its own corrections. The later concurrent reporting-only modification of this document was visible to the reviewer and is not part of the exact reviewed contract SHA; contract, helper and frozen vectors remain unchanged after that verdict. No active OPEN_ITEMS row closes.

Independent corrected-SHA commands (PYTHONPATH=src;tests/unit):

- `python -m pytest -q tests/unit/test_f07_contract_resolution.py`: 54 passed in 1.94s, exit 0.
- `python -m pytest -q tests/unit/test_f07_contract_resolution.py tests/unit/test_ipc_wire_primitives.py tests/unit/test_ipc_envelope.py tests/unit/test_ipc_response.py tests/unit/test_c09_named_pipe.py tests/unit/test_c09_pipe_transport.py tests/unit/test_c09_identity_boundary.py tests/unit/test_c09_service_host.py tests/unit/test_c09_scm_factory_wiring.py`: 299 passed in 2.83s, exit 0. Same initial-candidate list yielded 293 passed.
- `python -m pytest -q tests/unit/test_documentation_index.py`: 18 passed in 0.82s, exit 0.
- `git diff --check HEAD^ HEAD`: exit 0.
- Independent adversarial reproductions: replace/re-sign arbitrary projection digest; substitute/re-hash/re-sign projection case; replace s with n-s. All three now reject ValueError, probe command exit 0. Their corresponding frozen negative-vector tests reproduce the exact attacks without privileged state.

An initial review invocation referenced nonexistent tests/unit/test_c09_identity_client.py and tests/unit/test_c09_identity_dispatch.py, exited 1 with no tests and receives no credit. Only the corrected commands above support acceptance.

Authenticated reporting capacity, measured 2026-10-27T13:15:11Z via signed-in Codex app usage telemetry: five-hour remaining 32%, reset 2026-10-27T17:36:46Z; weekly remaining 72%, reset 2026-11-02T07:43:08Z. Reserve 15 points preserved. Start 70%/78%, observed consumption 38/6 points through this handoff; final Git/documentation readback follows without another development package.

Worker environment: Python 3.14.2 and pinned cryptography 50.0.1. All commands below use PYTHONPATH=src;tests/unit. No live service or external provider is called.

| Command | Actual result |
| --- | --- |
| `python -m pytest tests/unit/test_f07_contract_resolution.py -q` | Initial 48 passed; corrected 54 passed; exit 0. |
| `python -m pytest tests/unit/test_f07_contract_resolution.py tests/unit/test_ipc_wire_primitives.py tests/unit/test_ipc_envelope.py tests/unit/test_ipc_response.py tests/unit/test_c09_named_pipe.py tests/unit/test_c09_service_host.py -q` | Initial candidate 275 passed, exit 0. |
| `python -m pytest tests/unit/test_orchestrator_kernel.py tests/unit/test_identity_persistence.py tests/unit/test_production_runtime.py tests/unit/test_runtime_activation.py -q` | 88 passed, exit 0; no runtime code changed afterward. |
| `python -m pytest tests/unit/test_documentation_index.py -q` | 18 passed before candidate and after correction, exit 0. |
| `git diff --check` | Exit 0 before both candidate commits. |

Versioned fixture `tests/fixtures/f07-operational-contract-v1.json` is reproduced by the offline helper and equality test. It includes seven positive request/read DTO examples, explicit COMMIT and renewed-PREPARE examples, exact canonical frames/preimages/digests/signatures and 38 hostile vectors. The oversize frame has an exact byte-repeat recipe to avoid a redundant oversized literal. The public scalar 1 is test material only. Stateless examples do not prove durable proof consumption, actual principal authentication, live PENDING comparison, C09 finality or operational acceptance.

Remaining operational prerequisites are deadline/cancellation-aware actual transport, existing Kernel/Identity dispatcher and SCM runtime composition, real-principal authorization/fault/restart tests, independent runtime acceptance and the applicable existing deployment/custody/provider Human Gates. OI-0002/C09/OI-0003, protected case processing, Drive writes, Gemini/CSV, Approval and Submission remain gated. Next executable package after contract acceptance is bounded operational transport/client integration under these same constraints, not automatic activation.

## Continuous mission recovery — 2026-10-27

Overall status: `BLOCKED_SPEC_GAP`. Recovered prior commits e40eff928bb2ed96c7028c6b5a101f723d4fa1f0, 8f4069cefaba3cc017c75dd3a78b842ed3f6c709 and faf32408bfcc06c55a54e641f6639d27350e6414. The previously dirty exchange_validated_identity_read is now preserved and independently PASS at exact `77fd630ffad62e97515c69e384b51387e77262fd` strictly for development-contract composition. Worker verification: 243 client/transport/IPC/SCM tests and 88 Kernel/Identity/F06/F07 regressions. Reviewer verification: 232 focused and 366 expanded, exit 0. These injected/non-operational tests do not establish real Windows service integration.

Independent architecture review identified exact ambiguities in the operational architecture document lines 80, 91, 100, 108 and 110: exact outer fields omit the separately mandatory kernel_proof; prepared_request_digest placement is unspecified; signature preimage is alternately defined as the complete outer request and unsigned-proof bytes; request/response digest exclusion sets and signing order are not frozen; domain reads have no closed result field/schema and unclear subject/date optionality. Required next artifact is clarification of the same approved contract with complete golden vectors, followed by independent review. Neither the development-only validators nor the separate Custodian protocol may silently resolve these choices.

Existing SCM entrypoints remain uncomposed and current native exchange remains synchronous without deadline/cancellation. No real SCM/principal acceptance or protected operation occurred. The read-only SCM inventory returned no Kernel/Identity services and no fixed Kernel configuration file; no installation or privileged change was attempted. Active operational Kernel/Kill Switch state is not recovered. No new Owner decision about Person A/B or Drive architecture is needed; only exact contract clarification and later existing deployment Human Gates remain. The prior unrelated Desktop code was preserved but not invoked or accepted for this mission.

Reproducible worker commands (PYTHONPATH=src): `python -m pytest -q tests/unit/test_c09_identity_boundary.py tests/unit/test_c09_pipe_transport.py tests/unit/test_c09_service_host.py tests/unit/test_c09_named_pipe.py tests/unit/test_ipc_envelope.py tests/unit/test_ipc_response.py tests/unit/test_ipc_wire_primitives.py` (243 passed, exit 0); `python -m pytest -q tests/unit/test_orchestrator_kernel.py tests/unit/test_identity_persistence.py tests/unit/test_runtime_activation.py tests/unit/test_production_runtime.py` (88 passed, exit 0). A large parametrized test ID initially exceeded Windows fixture path limits; explicit short IDs corrected that test setup failure. No security check was relaxed.

Baseline: `f429cad56dad8a7cd1da468cac2da429316b0242`.
Accepted F06: `5f2547a2707a785f34766361ab22148535725086`.

Final preparation status: `INDEPENDENT_PASS` at exact `de0ef2ee1bd612c173774b54902b0070c5d557be`. Operational service-client integration is `PREREQUISITE_BLOCKED / NOT_IMPLEMENTED`, not accepted. Independent verification: 41 F07/runtime/UI tests, adversarial direct-construction/digest probes exit 0, and clean diff verification. Candidate `790abc4` failed F07-R01 MEDIUM on public-constructor validation bypass; final construction and assessment validation reject raw secrets, oversized IDs, duplicate refs and forged/stale digests. No preparation findings remain. Existing service-host/Named-Pipe regression: 22 passed. No privileged deployment or protected activation occurred.

## Existing service boundary

Inspection found no operational Kernel/Identity service client to connect. The fixed-role entry points in `c09_kernel_service.py` and `c09_identity_service.py` delegate to `run_scm_service`; `c09_service_host.py` composes `ServiceHost(role, unavailable_runtime)`. That factory raises `operational component composition is not implemented`. The accepted Named Pipe token/process verification primitives exist in `c09_named_pipe.py`, but do not constitute a client/dispatcher or operational acceptance. `DurableC09TransactionState` is explicitly synthetic and must not be substituted. This is a code-level unmet prerequisite, not a new Owner architecture question.

F07 therefore attaches readiness and exact durable case/run checks to the existing ProductionRuntime, preserving F06's disabled operation boundary. It does not claim a working operational service connection. No service, ACL, credential, cloud setting or protected database was activated or modified.

## Configuration contract

Closed schema: `ai-tax-agent.runtime-activation-preparation/1.0`. Required top-level fields: schema, deployment_id, owner_id, case_id, tax_year, run_id, references. Identity strings are bounded to 128 UTF-8 bytes; tax_year is an integer in the supported date interval. The exact owner/case/year/run must match the existing runtime and a committed Run. No year or case is hardcoded.

References is a closed map with these keys, each null or an immutable sha256 reference. Unknown fields, raw passwords/tokens/key contents, unsupported versions and malformed references are rejected. Null records incomplete configuration rather than inventing defaults.

| Reference | Content required through the existing protected resolver before activation |
| --- | --- |
| identity_binding_ref | Exact deployment, pinned service/principal identity, protocol version, executable and accepted operational Identity binding |
| sqlite_binding_ref | Canonical database/root, protected key custody, least privilege, schema/version and restart/backup evidence |
| drive_credential_ref | Protected credential handle and actor identity; never credential bytes in Git or UI |
| drive_binding_ref | Exact owner/case/year/provider root and accepted provisioning/reconciliation binding |
| provider_authorization_ref | Exact Kernel task/manifest/run/capability and operation-specific Owner authority where required |
| least_privilege_ref | Accepted real-principal effective-access evidence and fixed allowlists |
| privacy_ref | Provider destination, data categories, purpose and accepted privacy controls |
| retention_ref | Accepted evidence/document retention and deletion/recovery policy |
| audit_recovery_ref | Correlated audit heads, generation, accepted recovery/restore and reconciliation evidence |

Canonical configuration digest binds the complete declaration. Hash presence is only a claim; F07 does not resolve it as proof of content, authenticity or acceptance. Caller-supplied authority references cannot make a protected operation READY. Future activation requires the existing authenticated service/Kernel and protected evidence authorities; this preparation checker is not an authorization service.

## Operation gates

All protected operations remain disabled. Identity foundation means the frozen operational C03–C09/C10–C13 requirements, exact Kernel capability/manifest/task/run, custody and recovery. Evidence/Owner gates below supplement that foundation. `docs/oi-0002-final-closure-matrix-20261012.md`, the accepted operational architecture and `contracts/orchestrator/v2/human-gates.json` retain precedence.

| Capability | Required authority and acceptance evidence | Current blocker | Independent activation |
| --- | --- | --- | --- |
| Protected case creation | Kernel plus exact Owner runtime binding; Identity foundation, OI-0003 subject/party evidence and case/provisioning crash-recovery PASS | Operational client/composition absent; protected registration pending | Depends on Identity and storage; does not require Gemini |
| Protected identity registration | Existing Kernel identity_create and Identity authority; declaration/confirmation, exact subject/case binding, operational independent PASS | Operational client/composition absent | Can precede Drive/Gemini/CSV once Identity foundation is accepted |
| Drive provisioning | Kernel plus exact Owner provider binding; scoped credential, root, ACL, privacy/retention, isolation and reconciliation PASS | Runtime/provider binding and independent deployment acceptance missing | Does not require Gemini/CSV; requires accepted case/Identity foundation |
| Document ingestion | Kernel case-document capability; protected storage, immutable duplicate/version/party lineage, privacy/retention and isolation PASS | Protected storage/Identity/provider acceptance missing | Can precede extraction after document/storage controls pass |
| Gemini extraction | Kernel and exact Owner provider binding; scoped document attribution, credential custody, destination/privacy/retention and extraction validation | Provider and protected-document acceptance missing | Separate from CSV; cannot bypass document/Identity foundation |
| CSV ingestion | Kernel case-processing authority; case/run ledger lineage, persistent result and isolation independent PASS | Protected Identity/persistence and processing binding missing | Can be accepted without Drive/Gemini when its own foundation/path is accepted |
| Approval | Human Project Owner; exact immutable artifact content-release approval, classification/purpose/scope/expiry | Exact final artifact and approval absent; disabled by instruction | Separate from submission; creates no transmission authority |
| Submission | Human Project Owner; separately recorded content-release and destination-transmission approvals, exact artifact/destination/channel/scope/expiry | Both exact approvals and submission operational acceptance absent; disabled by instruction | Cannot activate from generic runtime or content approval |

The code's independent_activation flag identifies the explicit Identity and CSV preparation paths that do not depend on the external provider stack; it never waives their listed foundation. The table records the more detailed dependency ordering for other capabilities.

## Deterministic readiness

`ProductionRuntime.assess_readiness` performs only verified reads. The fixed precedence for protected operations is reconciliation, missing configuration, missing authority claim, then security gate blocked. It reports READY only for verified read-only case/run navigation. Even a complete configuration and authority-reference map returns SECURITY_GATE_BLOCKED because no operational service composition or independent operational acceptance exists. `executable` remains false for every protected operation. Credentials/environment variables are never consulted. Unexpected integrity/authorization/I/O failures propagate fail-closed, rather than becoming a favorable readiness result.

RECONCILIATION_REQUIRED means the existing scoped provisioning authority reports an in-progress or uncertain result. F04 still prohibits exposing an uncommitted new case as a committed runtime case; an inconsistent registered-case/provisioning store fails integrity validation before any readiness is returned. No manual reconciliation/override is implemented here. This status is tested with a controlled authority response, not claimed as live reconciliation evidence.

## Continuation and authority split

Codex can implement the already approved bounded authenticated client/dispatcher and service composition, compatibility/error/audit integration, and focused fault tests under a separately admitted implementation package and independent review. Reuse existing Named Pipe and Kernel continuity primitives. First inspect current HG/C09 evidence; do not repeat accepted investigations.

Owner actions remain only at the exact privileged service/deployment/key-custody/IAM/runtime activation gates after reviewable technical evidence exists. No new decision about internal Person A/B IDs, legacy mapping or marriage scope is pending. Unchanged confirmed facts need no reconfirmation. Approval/Submission remain disabled.

Shortest secure next step: complete the missing existing-role service composition/client under the accepted operational contract, independently verify it and the remaining C09/HG controls, then perform exact evidence-bound OI-0003 registration and separately approve the first protected case/provider binding. F07 readiness cannot substitute for that operational campaign.
