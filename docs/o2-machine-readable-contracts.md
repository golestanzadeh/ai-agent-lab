# Phase O2 — Machine-Readable Orchestrator Contracts

Status: **DESIGNED AND TECHNICALLY VERIFIED; HUMAN PHASE ACCEPTANCE REQUIRED**

## Purpose

Phase O2 translates the Human-ratified Agent Organization v1 into versioned, machine-readable contracts. These artifacts define what a later deterministic Orchestrator Kernel must validate. They do not implement that Kernel, activate an Agent, issue a permission, or authorize a consequential action.

The contract set is rooted at `contracts/orchestrator/v1/contract-set.json`. Compatibility is exact-version and fail-closed: missing files, unknown versions, or mixed contract versions produce `BLOCKED`.

## Contract map

| Contract | Authority |
|---|---|
| `roles.json` | Exact 20 permanent roles, three inactive domain templates, hierarchy, capabilities, forbidden actions, and review requirements |
| `agent-manifest.schema.json` | Strict temporary-instance identity, task, scope, inputs, outputs, tools, permissions, budget, expiry, and stop contract |
| `permission-matrix.json` | Default-deny access tiers, capability ceiling, role defaults, temporary elevation, case/run scoping, and A6 prohibition |
| `task.schema.json` | Registered Master-to-Agent command and lineage contract |
| `response.schema.json` | Agent-to-Master result, evidence, cost, status, and Human Gate contract |
| `lifecycle.json` | Agent instance states, legal transitions, terminal behavior, expiry, revocation, and retention |
| `human-gates.json` | Mandatory Human Gate triggers, conflicts of interest, authority precedence, and Article 1 transfer approvals |
| `execution-policy.json` | Default and hard budgets, retry classes, loop limits, reporting, and kill-switch behavior |

## Core invariants

### Identity and lineage

- A role definition is stable; an Agent instance is temporary.
- Every instance binds to one manifest and one registered task.
- Every task and response preserves `task_id`, parent lineage, `role_id`, and `actor_instance_id`.
- Unknown roles, fields, schema versions, transitions, permissions, or authority fail closed.

### Scope and permission

- Permission is Default Deny.
- A manifest may request only A0–A5. A6 and AX cannot appear in an Agent manifest.
- A2 and A5 are bounded capabilities. A3 and A4 require exact `case_id`, `tax_year`, and `run_id`.
- A6 actions are never standing Agent permissions. They require their applicable Human Gate and deterministic broker or gateway.
- Domain specialist templates remain `INACTIVE` until their workflow, authoritative sources, tests, and permissions are separately accepted.

### Communication

- An Agent cannot execute without a registered task.
- Peer work becomes a registered child task; lateral messages cannot expand authority.
- `PASS` means the task contract produced completion evidence. It does not mean Human acceptance, production readiness, merge authority, or transmission authority.
- `HUMAN_REQUIRED` responses must set `human_required=true`.

### Lifecycle and recovery

- Legal instance flow begins at `PROPOSED`; activation requires a registered task, validated role and manifest, permission and conflict checks, available budget, running kill switch, and unexpired scope.
- Terminal instances cannot restart. Retry creates a new attempt identity and audit event.
- Expiry and revocation withdraw temporary tools and permissions.
- Termination preserves manifests, tasks, responses, artifacts, test and failure evidence, costs, and audit events.

### Human Gates and external transfer

- Human Gates cover constitutional, governance, architecture, credential, permission, connector, protected-main, release, destructive, evidence, tax-submission, ELSTER/Finanzamt, transfer, and authority-ambiguity boundaries.
- External transfer is Default Deny.
- Stage One approves one exact artifact for release.
- Stage Two separately approves that unchanged artifact for one exact recipient, channel, purpose, time window, and retry rule.
- Stage Two binds to Stage One. Combined approval is prohibited.
- Any artifact, destination, channel, purpose, validity, or audit mismatch blocks transfer.

### Budget, retry, and kill switch

- Every instance has positive token, tool-call, cost, time, retry, child-task, and concurrency bounds.
- Hard limits cannot be lower than defaults.
- Authority, permission, case-scope, schema, conflict, Human Gate, destructive ambiguity, and uncertain-transfer failures are not automatically retryable.
- Duplicate task execution and same-attempt replay are prohibited.
- `HALTED` blocks dispatch and continuation, revokes temporary permissions, and preserves evidence.
- The initial runtime kill-switch state is `HALTED`; Phase O3 cannot claim operation until an authorized deterministic state transition exists.

## Validation boundary

`scripts/validate_o2_contracts.py` performs offline structural and cross-contract checks using the Python standard library. It verifies the exact contract set, role counts and stable identifiers, reporting references, permission coverage, A6 controls, strict schema boundaries, lifecycle reachability and terminal behavior, Human Gate completeness, two-stage transfer separation, conflicts of interest, budget bounds, and kill-switch safety.

The validator does not grant permission, activate roles, dispatch tasks, create approvals, access private case data, or transmit externally.

## Acceptance criteria

Phase O2 is technically complete when:

1. all registered artifacts exist and parse;
2. the role catalog preserves the ratified organization;
3. manifest, task, and response schemas reject unknown top-level fields;
4. permissions are complete, default-deny, case-aware, and never give standing A6 access;
5. lifecycle transitions fail closed and terminal instances cannot restart;
6. conflicts of interest and independent acceptance remain enforceable inputs to O3;
7. Article 1 approvals remain separate, ordered, exact, expiring, revocable, and audit-bound;
8. budget, retry, loop, and kill-switch policies are bounded;
9. positive and negative validation tests pass;
10. canonical state, roadmap, decision log, documentation index, and checkpoint record the verified result and exact next gate.

## Phase boundary

Successful O2 validation proves contract consistency only. Phase O3 deterministic Orchestrator Kernel implementation remains unauthorized until the Human explicitly accepts the O2 phase result.

O2 performs no Agent activation, permission issuance, credential operation, private case-data access, protected-main action, production release, destructive action, ELSTER/Finanzamt contact, or external transfer.
