# HG01 independent Codex review handoff (prepared 2026-10-24)

State: READY_FOR_READ_ONLY_REVIEW / REVIEW_NOT_RUN. This is a reviewer handoff, not independent acceptance.

## Immutable baseline and scope
Branch c09-witness-hardening; preparation HEAD bd349181e05b514aa6d31ece8bcf34d9684459d0. Technical executable candidate source f1af82fd1a7c858074db868d412604dba9589833. At this source, two clean A/B Windows onedir builds had 75 identical manifest entries each (zero differences), and full unit regression yielded 1558 passed, 6 skipped in 288.64s. The two different SHAs MUST be distinguished: bd34918 is documentation handoff, f1af82f is build source. Reviewer must independently check no intervening implementation changes before applying source-based evidence.

## Review inputs
- docs/oi0002-c09-witness/HG01_IMPLEMENTATION_2026-10-24.md
- docs/oi0002-c09-witness/HG01_SERVICE_IMPLEMENTATION_PREREQUISITES_2026-10-24.md
- docs/oi0002-c09-witness/KERNEL_IDENTITY_OPERATIONAL_ARCHITECTURE.md (locate if path differs)
- config/c09-r3/hg01-build-profile.json
- config/c09-r3/hg01-build-evidence.json
- config/c09-r3/hg01-signing-profile.json
- config/c09-r3/hg01-windows-services.json
- src/agent_lab/c09_service_host.py
- src/agent_lab/c09_kernel_service.py
- src/agent_lab/c09_identity_service.py
- src/agent_lab/c09_custodian_service.py
- src/agent_lab/c09_named_pipe.py
- PROJECT_CHECKPOINT.md, OPEN_ITEMS.md, CURRENT_STATE.md
- Ignored local evidence .runtime/hg01-build/f1af82fd1a7c858074db868d412604dba9589833/{A,B}/artifact-tree.json and .runtime/hg01-full-regression-f1af82f.log, if accessible.

## Independent review protocol
1. Run in a separate Codex context from the implementer, using a separate read-only checkout/worktree and no write authority to production or source. If no true isolation is possible, report INDEPENDENCE_NOT_ESTABLISHED rather than PASS.
2. Verify git source SHA, test log provenance, manifest completeness/uniqueness, SHA256 parity, locked dependencies, unsigned state, and no deployment.
3. Independently audit Windows SCM lifecycle, actual-token SID and fail-closed startup, Named Pipe DACL/first-instance/local-only and PID/image/hash binding, IPC canonicality, replay/timeout, synthetic-only Custodian key boundary, and operation denial.
4. Re-run relevant focused tests and construct adversarial tests (wrong SID, image replacement, PID turnover, pipe squatting, remote connection, noncanonical frames, replay, interrupted lifecycle); no real services, credentials, GCS mutations, ACL/IAM or signing keys.
5. Explicitly distinguish implemented and not wired runtime composition. An executable that fails closed is not an operational three-service acceptance.
6. Return independent PASS / FAIL / HUMAN_REQUIRED with finding IDs, severity, exact source SHA, commands, exit codes, evidence, coverage gaps, reproducibility limits and next steps. PASS must be scoped to actual proven synthetic/build properties; do not certify HG-01 operational approval.
7. Reviewer must not modify source, docs, checkpoint or OPEN_ITEMS. Return report to Supervisor; Supervisor/Development Worker handles remediation and committed evidence. On FAIL repair in a separate implementer context, then re-review new SHA.

## Security and authority
Owner authorizes bounded synthetic technical stages 1-5A and repair/retest, not real activation, key provisioning, privileged IAM/ACL, retention lock or external filing. Preserve 15 percentage points of Codex usage reserve. Read authenticated capacity/reset before starting; if insufficient, defer without consuming reserve. No taxpayer facts or secrets in review output.

## Reviewer output contract
Exact SHA; independence proof; summary decision; findings table; commands/results; explicit scope exclusions; next actionable repair package. Independent acceptance is NEVER inferred from a passing regression alone.