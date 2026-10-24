# C09/R3 HG-01 Windows service implementation prerequisites

Status: `PROPOSAL_READY / IMPLEMENTATION_NOT_AUTHORIZED / HG01_NOT_APPROVAL_READY`.

This is a repository-derived implementation proposal only. No service source, executable, install definition, account right, ACL, task or host state was created or changed.

## Approved architecture versus missing implementation

The independently accepted C09 architecture requires three Windows SCM services under the existing separate principals: Kernel, Identity and Key Custodian. Identity and Custodian each own a fixed message-mode local Named Pipe; Kernel is their sole authorized client and remains the sole transaction coordinator. Each endpoint requires first-instance ownership, remote rejection, exact DACL, actual token/SID verification, retained server-process-handle image/path/hash verification and fail-closed service lifecycle behavior.

That security architecture is approved. The repository does **not** contain operational service entry points, a Windows service host/lifecycle adapter, Named Pipe transport, operational Identity dispatcher, Custodian service, build metadata, a frozen dependency lock, a reproducible executable build, signing policy or executable artifacts. `requirements.txt` pins runtime package versions but is not a complete reproducible Windows build definition. No PyInstaller, WinSW, NSSM, MSI, wheel/console-entry-point or service-wrapper contract is present or approved.

## Reusable components

- Kernel authority/state: `orchestrator_kernel.py`, `identity_continuity_authority.py`, `c09_transaction_state.py`.
- Identity semantics/storage: `identity_persistence.py`, `identity_evidence_authority.py`, `identity_custody.py`, accepted REMEDIATION-02 contracts.
- Closed protocol primitives: `ipc_wire_primitives.py`, `ipc_envelope.py`, `ipc_response.py`.
- External witness behavior: `c09_gcs_witness_adapter.py`, `c09_witness_protocol.py`.
- Frozen operational contract and matrices: `KERNEL_IDENTITY_OPERATIONAL_ARCHITECTURE.md`.

These are libraries/component evidence, not SCM service executables. The development-only IPC validators have no transport or peer authentication and must not be represented as an operational endpoint.

## Required bounded implementation

1. **Kernel service entry point:** SCM start/stop handling; exclusive Kernel-store ownership; construction of the existing Kernel/continuity/transaction components; Identity and Custodian pipe clients; bounded reconciliation on restart; halt/kill-switch propagation; no direct Identity/key-store access.
2. **Identity service entry point:** exclusive Identity-store/audit ownership; fixed Named Pipe server; exact Windows-token and retained-client-process verification; closed operation dispatcher into existing accepted identity APIs; deterministic shutdown and recovery; no Kernel/GCS/key-store access.
3. **Custodian service entry point:** fixed independent Named Pipe server; exact peer verification; only the closed authenticate/verify operations; provider-reference-only key use; no key export, transaction decision, Kernel/Identity-store or GCS authority.
4. **Shared service-host boundary:** minimal SCM adapter, structured privacy-minimized event logging, bounded timeouts/message sizes/instances, explicit startup dependency checks, stop-without-partial-commit semantics and zero interactive-user fallback.

The implementation must remain three separately built entry points. A single multi-role executable, command-line role switch, shared writable runtime directory or generic command dispatcher is prohibited because it weakens image/role binding.

## Reproducible build and artifact requirements

Before HG-01 can be approval-ready, a separately authorized implementation package must select and freeze one Windows packaging toolchain, exact Python/tool versions, dependency hashes, deterministic build commands and clean-build environment. It must produce three immutable executables plus dependency/SBOM manifests. Two clean builds must either be byte-identical or document and independently verify every nondeterministic field with normalized reproducible content digests.

Each candidate requires SHA-256, Authenticode status, publisher/thumbprint when signing is used, protected absolute install path, file size/version, source commit, build-manifest digest and malware-scanning result. Signing is a separate custody decision: no certificate/private key exists in this package, and implementation may not create or export one. An unsigned synthetic test build may support development tests but can never satisfy the operational Human Gate.

Exact future paths remain unset until the packaging choice is independently accepted. `config/c09-r3/hg01-windows-services.json` must continue to contain null executable paths/hashes and `execution_authorized=false` meanwhile.

## Required tests and acceptance evidence

- Unit/contract: SCM start/stop/timeout/failure; default-deny dispatch; exact frame/operation/outcome matrices; no interactive fallback.
- Four-principal host matrix: correct token succeeds; wrong principal, same-SID wrong image, PID turnover, pipe squatting, remote client, Administrators/Recovery and cross-store access fail.
- Fault/restart: termination before/after every PREPARE/PENDING/Identity commit/Witness/finalize boundary; repeated restart converges or halts; no false acknowledgment.
- Custody: Kernel/Identity/Recovery cannot read/export/use the Witness key; Custodian cannot access domain stores or choose transactions.
- Artifact: clean rebuild, hashes, dependency/SBOM verification, signature/path tamper, downgrade and manifest mismatch negatives.
- Regression: focused service/IPC/security suites, relevant C09/Identity/Kernel regression, full unit regression because the service boundary is cross-cutting, then exact-SHA independent implementation/security review.
- Owner operational verification only after HG-01/02/03/04 prerequisites are separately approval-ready and approved; no implementation PASS activates a service.

Acceptance outcome before installation is `HG01_IMPLEMENTATION_INDEPENDENT_PASS / ARTIFACTS_REVIEWED / NOT_ACTIVATED`. Activation remains the separate exact Owner Human Gate.

## Estimate and next authority boundary

Conservative estimate for implementation, Windows-host fault/security tests, reproducible builds, full regression, at least one repair cycle, independent exact-SHA review and checkpointing: **35–50 five-hour percentage points**. Operational four-principal activation/evidence is excluded and separately gated.

Exact next action: Owner authorization for this bounded service-host implementation and selection/approval of the Windows packaging/reproducible-build profile. Until then, do not add service code merely to fill the gap. HG-01 remains `NOT_APPROVAL_READY`; R3 operational security, C09 and OI-0002 remain open.
