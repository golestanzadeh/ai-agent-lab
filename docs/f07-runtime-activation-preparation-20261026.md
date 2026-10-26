# F07 governed runtime activation preparation

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
