# Phase O3 — Deterministic Orchestrator Kernel

Status: **IMPLEMENTED; FINAL VERIFICATION PENDING**

## Purpose

The Phase O3 Kernel turns the Human-accepted O2 contracts into a persistent, fail-closed control plane. It records tasks, dependencies, Human Gates, manifests, lifecycle, permissions, budgets, retries, responses, independent acceptance, audit events, checkpoints, recovery state, kill-switch state, and Agent Bridge bindings in one SQLite database.

The Kernel binds to the canonical SHA-256 digest of the exact O2 JSON set accepted at commit `382a140e42496ad9edd92dc2016cfde51d091575`. A same-version content change is rejected until a separately governed contract-version change is accepted.

The Kernel controls state and authority. It does not run an LLM, spawn an Agent, issue a real credential, access private tax data, merge or release code, or transmit externally.

## Components

### Task and Dependency Registry

- Accepts only the exact O2 task field set and version.
- Requires known role and capability identifiers.
- Rejects duplicate task identity, missing parent, missing dependency, self-dependency, and dependency cycles.
- Keeps dependency tasks blocked from activation until all prerequisites are independently accepted and `COMPLETED`.

### Human Gate Registry

Every task registration must explicitly supply a Human Gate trigger list, including an explicit empty list for routine work. The list is stored separately from the accepted O2 task payload so O2 schemas are not silently amended.

- Unknown triggers fail closed.
- A task with one or more triggers enters `HUMAN_REQUIRED`.
- Only `HUMAN_PROJECT_OWNER` may record `APPROVED` or `REJECTED` with an authority reference.
- All registered gates must be approved before the task becomes executable.
- Rejection is terminal for the task.

### Agent Factory Kernel and Manifest Validator

- Requires a registered executable task before accepting a manifest.
- Enforces exact task, role, actor-instance, parent, repository, ref, case, input, output, tool, capability, forbidden-action, budget, timeout, retry, and expiry bindings.
- Rejects unknown or duplicate identity.
- Rejects A6/AX and any tier not assigned to the selected role.
- Requires exact `case_id`, `tax_year`, and `run_id` for A3/A4.
- Preserves Agent Bridge path restrictions when a task originated from the Bridge.
- Validation moves only `PROPOSED -> VALIDATED`; it does not issue a capability or run an Agent.

### Permission Broker

Permission is granted only when:

- the manifest is `ACTIVE`;
- the kill switch is `RUNNING`;
- the capability is known and explicitly present in the validated manifest;
- role and task capability boundaries match;
- exact case/run context matches when required;
- the capability is below A6.

A6 always returns `HUMAN_REQUIRED`; no standing Agent permission can represent external transfer, credential administration, protected-main merge, production release, or destructive action.

### Lifecycle and independent acceptance

- Manifest transitions must exist in the accepted lifecycle graph.
- Terminal manifests cannot restart.
- An Agent `PASS` response moves its task to `AWAITING_ACCEPTANCE`, not `COMPLETED`.
- A `PASS` response cannot contain failed test evidence, and reported token/tool/cost usage must equal the durable budget ledger.
- Only an active `INDEPENDENT_ACCEPTANCE_AGENT` child task with a different actor instance may close the reviewed task.
- Acceptance outcomes are `PASS`, `BLOCKED`, or `HUMAN_REQUIRED` and are durably recorded.

### Budget, retry, and loop control

- Manifest limits may not exceed task or O2 hard limits.
- Consumption is atomically recorded.
- An attempted overspend changes the manifest to `BLOCKED` without recording the overspend.
- Retry requires a terminal `FAILED` manifest, a retryable failure class, remaining retry budget, a running kill switch, and a unique new attempt ID.
- Authority, permission, schema, case, conflict, Human Gate, destructive ambiguity, and uncertain-transfer failures do not retry automatically.

### Kill switch

- A new database starts at `HALTED`.
- Only Human authority may set `RUNNING`.
- Human or Master may pause; Human, Master, or an independent Control Office role may halt.
- `HALTED` blocks dispatch/permission and revokes active or blocked manifests while preserving tasks, evidence, and audit.
- No production RUNNING transition is authorized by Phase O3 implementation or its tests.

### Audit, checkpoint, and recovery

- Material actions append an audit event containing actor, entity, time, payload, previous hash, and deterministic event hash.
- Audit verification recomputes the complete hash chain and fails on modification.
- A checkpoint stores a canonical snapshot and SHA-256 reference bound to the accepted contract-set ID and last event.
- Recovery verifies audit and checkpoint integrity before returning durable state.
- The inspection CLI opens the database in SQLite read-only mode and reports schema, kill-switch state, counts, latest checkpoint, and audit integrity.

### Agent Bridge binding

The existing Agent Bridge validator remains the external envelope boundary. A low-risk `PASSIVE_VALID` request is bound to an exact O2 task only when task identity, repository, ref, objective, acceptance criteria, forbidden actions, base commit, and allowed paths agree.

Bridge requests already classified as `HUMAN_REQUIRED` are not registered for execution. Manifest paths may only narrow the Bridge allowlist.

## Durable schema

The initial SQLite schema version is `1`. It contains:

- `tasks`
- `dependencies`
- `task_human_gates`
- `manifests`
- `budget_usage`
- `retry_attempts`
- `responses`
- `acceptance_records`
- `bridge_bindings`
- `kill_switch`
- `audit_events`
- `checkpoints`

An unknown database or contract version fails closed. Database initialization creates no Agent and starts the kill switch at `HALTED`.

## Read-only inspection

For an explicitly selected existing database:

```powershell
$env:PYTHONPATH = "src"
python scripts/inspect_orchestrator_kernel.py C:\exact\path\kernel.sqlite3
```

The command performs no schema migration or state mutation.

## Acceptance criteria

Phase O3 is technically complete only when tests prove:

1. durable restart and exact contract/schema compatibility;
2. strict task, dependency, and cycle validation;
3. explicit Human Gate classification and Human-only decisions;
4. manifest lineage, role, permission, scope, budget, and expiry validation;
5. A6 prohibition and exact case/run isolation;
6. legal lifecycle transitions and terminal-state behavior;
7. Agent PASS cannot bypass independent acceptance;
8. budget exhaustion, retry identity, and non-retryable failures fail closed;
9. kill-switch authority, revocation, and evidence preservation;
10. audit tampering is detected and checkpoint state survives restart;
11. Agent Bridge binding preserves exact envelope scope and Human Gate results;
12. targeted, relevant, and full regression suites pass.

## Phase boundary

Technical completion does not activate the Kernel in production. Phase O4 controlled pilot remains behind explicit Human acceptance of the exact O3 implementation and verification evidence.
