# UI25-05 synthetic Kernel execution — 2026-10-16

## Result

Status: **TECHNICAL_PASS / SYNTHETIC_ONLY / INDEPENDENT_ACCEPTANCE_PENDING**.

The functional UI now exposes one explicit POST action that executes one bounded deterministic task through the existing `OrchestratorKernel`. The path is restricted to a registered `TEST-*` case for tax year 2025, an exact bounded run identity and one integer input from 0 through 1,000,000. The fixed `UI25-SYNTHETIC-WORKER-V1` actor uses the existing `IMPLEMENTATION_AGENT` role and the existing `report_evidence` capability at A1. It performs no file, network, subprocess, provider, document, protected-persistence or external operation.

The deterministic worker doubles the synthetic integer and records its response and SHA-256 evidence in the existing Kernel response/audit structures. The task ends at `AWAITING_ACCEPTANCE`; the worker cannot approve itself. The UI displays the genuine Kernel task identity, role, lifecycle and deterministic response. The Kill Switch is explicitly set to `RUNNING` only for the Owner-initiated action and is returned to `HALTED` in a `finally` boundary.

## Authorization basis

- Current explicit Owner execution order: UI25-05 Synthetic Kernel Execution.
- Existing `docs/ui25-owner-internal-development-testing-authorization-20261009.md` authorizes internal synthetic integration/testing while preserving security and Human Gates.
- Existing O2 permission matrix authorizes `IMPLEMENTATION_AGENT/report_evidence` at A1.
- Existing O3 Kernel remains the sole task, manifest, permission, budget, lifecycle and audit authority.
- No OI-0002, C09, operational IPC or protected-persistence acceptance is used or implied.

## Fail-closed controls

- Production Dashboard construction rejects the execution adapter.
- Only an existing functional-test Case Registry entry is accepted by the UI.
- Only `TEST-*` / tax year 2025 / exact run scope is accepted by the executor.
- One run identity cannot be rebound to another case or year.
- Deterministic task identity prevents duplicate execution and response creation.
- Missing, malformed, non-test and out-of-range inputs are rejected before execution.
- Permission and budget are checked by the Kernel immediately before the fixed worker runs.
- A halted Kill Switch denies direct worker invocation.
- The complete audit chain is verified before and after execution.
- Response content is SHA-256-bound into `RESPONSE_RECORDED`; altered result content fails readback even when it remains valid JSON.
- Restart reads the same task/response from the existing Kernel database; no scheduler, dispatcher database or second task registry was introduced.

## Verification

Focused Kernel/UI/runtime/security suite: `93 passed`.

The suite executes the actual fixed worker and proves UI result `SYNTHETIC_RESULT=42`, exact actor identity, `AWAITING_ACCEPTANCE`, duplicate denial, non-test/year/run denial, cross-case run denial, halted-Kill-Switch denial, restart readback, audit-chain verification and response-rewrite detection.

Relevant UI/Kernel/runtime/case/documentation regression: `148 passed`.

Complete unit regression: `1371 passed, 5 skipped`.

Authenticated ending Codex telemetry at `2026-10-16T20:09:33.406411+00:00`: five-hour `24%` remaining (reset `2026-10-17T00:02:24+00:00`), weekly `86%` remaining (reset `2026-10-23T13:57:50+00:00`). The mandatory 15-point five-hour reserve remains intact.

## Remaining boundary

This is one user-initiated synthetic task, not UI25-05 operational acceptance and not automatic intake dispatch. It cannot process taxpayer data and grants no permission for real documents, protected persistence, external providers, ELSTER or generic automation.

The shortest next step toward the 2025 end-to-end test is separate independent review of this exact commit and Owner hands-on UI confirmation. After that, real-case execution remains blocked until an accepted durable live case/run resolver and protected persistence boundary exist.
