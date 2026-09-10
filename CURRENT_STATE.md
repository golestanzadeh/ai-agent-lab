# Current State

## CURRENT_STAGE

**D-021 complete; Agent Bridge productionization in progress.**

D-021 implementation is complete on branch `d021-agent-case-provisioning`. Standard case-storage provisioning is an authorized agent operation inside the existing Case Creation architecture; it is not physical document migration.

Human authorization was issued on 2026-09-08 as `HUMAN-AUTH-2026-09-08-CASE-001-PHYSICAL-MIGRATION`. The exact reviewed binding produced an **APPROVED** state in the existing process-local `ApprovalStore`. The approval was **not consumed**. Physical migration was **not started**. Source documents remain unchanged. Because `ApprovalStore` is process-local/in-memory, that APPROVED state is not durable or reloadable after process exit and the private review export is not executable authorization.

## LAST_ACCEPTED_STAGE

**D-020 — CASE-001 Approval Context Composition: accepted, integrated, and closed.**

Accepted implementation: `e6f28e89acf45541e4cfaa55c9efd8db35fc7909`.
Canonical main before D-021 branch work: `ee59dadbc2c7f2433e8291f849fef3048b574a9c`.

## BASELINE — 2026-09-10

- Working branch: `d021-agent-case-provisioning`.
- Pre-baseline checkpoint: `9b316797015026b1c3de74c0226c8752b87fe344`.
- Step-1 canonical cleanup commit: `df4121b037957dc28658bbc9e51fa38a4b329271`.
- Latest recorded D-021 final verification: targeted **84 passed**; full suite **246 passed, 1 skipped**.
- D-021 is implementation-complete but has not been declared integrated on `main`.
- Approval: **APPROVED / NOT CONSUMED / NON-DURABLE**.
- Durable/reloadable approval authority: **NOT IMPLEMENTED**.
- Physical migration: **NOT STARTED**.
- Source CASE-001 documents: **UNCHANGED**.

## AGENT BRIDGE PRODUCTION MIGRATION

### Step 1 — Baseline + Durable Documentation + Canonical State Cleanup

**Status: ACCEPTED / COMPLETE — 2026-09-10.**

Canonical state was normalized, stale `PENDING` wording removed, branch/commit and test baseline recorded, and the runtime migration boundary preserved.

### Step 2 — Production Architecture and Governance

**Status: HUMAN-ACCEPTED — 2026-09-10.**

The human explicitly approved the following production architecture:

- **ChatGPT Work — Architect / Orchestrator / Reviewer:** designs bounded tasks, evaluates GitHub evidence independently, and decides `PASS`, `BLOCKED`, or `HUMAN_REQUIRED`.
- **Codex — Implementation Engineer:** implements only authorized bounded tasks, runs tests, repairs within scope, and reports evidence. It cannot independently redefine architecture/contracts/governance, accept stages, merge/release, consume runtime approvals, or perform consequential tax-data actions.
- **GitHub — Durable Source of Truth + Event Bridge:** stores task state, commits, diffs, tests, responses, and auditable development history.
- **Human — Final Authority at Human Gates:** retains authority required by D-019 and all consequential runtime gates.
- **Agent Bridge — development control plane only:** it is not runtime tax authority and cannot replace D-017 or any case/run-scoped authorization.
- **Fail closed:** ambiguous authority, malformed protocol, scope violation, security uncertainty, or required human authority results in `BLOCKED` or `HUMAN_REQUIRED`, never guessed continuation.
- **PoC isolation:** the separate Agent Bridge PoC proves feasibility only. Its PAT, workflows, permissions, test artifacts, and lab assumptions are not production authority and must not be copied blindly.

Canonical loop:
`Work → GitHub → Codex → tests/evidence → GitHub → Work → PASS/next bounded task`.
At any Human Gate: `HUMAN_REQUIRED → STOP → Human`.

### Step 3 — Protocol Contract

**Status: DEFINED under the accepted Step-2 architecture; implementation pending.**

Protocol version 1 requires a unique `task_id`, optional `parent_id`, repository/ref binding, `base_commit`, sender, recipient, status, bounded task, acceptance criteria, allowed scope, forbidden actions, and risk class. Responses require the same task lineage plus `result`, response commit when applicable, changed paths, structured test summary, authority used, and `human_required`.

Controlled statuses are `REQUEST`, `RESPONSE`, `BLOCKED`, and `HUMAN_REQUIRED`. Results are `PASS`, `BLOCKED`, or `HUMAN_REQUIRED`. A response must bind to the expected task, repository, branch/ref, and base lineage. Unknown/missing/mismatched fields fail closed.

Idempotency is mandatory: a `task_id` may not be executed or continued twice. Replay/stale-response detection must reject duplicate or unexpected lineage. Work must verify GitHub commit/diff/test evidence rather than trust response prose alone.

### Step 4 — Production Security Model

**Status: DEFINED under the accepted Step-2 architecture; implementation pending.**

- Least privilege; no `write-all`.
- Default workflow permissions read-only/empty; write permissions only on the exact bounded job that requires them.
- Codex write execution only on dedicated non-main task branches.
- `main` is not an autonomous-agent write target; production branch protection/ruleset is a prerequisite before autonomous continuation is considered production-ready.
- Secrets remain GitHub secrets/environment secrets only; never repository files, prompts, comments, artifacts, or logs.
- The PoC `AGENT_BRIDGE_USER_TOKEN` is not approved for production reuse. Identity/wake-up design must be re-evaluated; PAT is fallback only if unavoidable and then must be repository-scoped and least-privilege.
- Third-party actions should be pinned to immutable commit SHA for production.
- Checkout credentials should not persist where unnecessary.
- No untrusted fork code may receive secrets; avoid unsafe `pull_request_target` patterns.
- Concurrency, timeout, task replay protection, expected base/branch validation, allowed-path restrictions, sanitized logs/artifacts, and a fail-closed kill switch are required before controlled continuation.
- Bridge payloads must not contain private Drive IDs, OAuth material, tax-document content/names, credentials, or private evidence. Use non-sensitive identifiers/references.
- Any change to this security model, secrets, permissions, Human-Gate rules, or consequential authority is `HUMAN_REQUIRED`.

## NEXT_BOUNDARY

Proceed sequentially with Agent Bridge productionization. The next implementation boundary is **Step 5 — Passive / Observe-only Bridge**. Before new production Bridge files are created, their paths must be registered in `ROADMAP.md` according to the future-file registry rule. Step 5 must not invoke Codex with write authority, create autonomous continuation, change secrets/permissions, or authorize runtime tax actions.

The underlying AI-Tax-Agent runtime boundary remains unchanged: durable/reloadable approval lifecycle architecture must be separately accepted and implemented/tested before physical migration execution can be designed or considered.

## VERIFIED_RUNTIME_STATE

- GitHub is the durable source of truth; local Python/Docker is the execution environment; Google Drive holds private case data.
- Multi-case architecture requires mandatory `case_id`, persistent `person_id`/`entity_id`, and explicit `tax_period`.
- Real CASE-001 source inventory: **15 PDFs, 0 folders**.
- Real CASE-001 / 2024 target tree: all six standard subfolders provisioned; target Documents verified empty.
- Real run: `RUN-00000001`; approval identifier: `APP-00000001`.
- Reviewed process produced **APPROVED**, not consumed; state is not durable/reloadable after process exit.
- D-019 controlled agent-assisted development governance remains in force.
- No physical Google Drive migration has occurred.

## ACTIVE_CONSTRAINTS

- Source documents are immutable.
- No broad/unscoped Drive search for case data.
- Every case-data operation requires validated case scope and must fail closed on ambiguity.
- Private Drive IDs, OAuth tokens, credentials, client secrets, and private document information must never be committed.
- Provisioning authority does not authorize source-document mutation, permission changes, approval consumption, physical migration, destructive operations, or architecture/contract changes.
- Human authority remains required wherever D-019 or an accepted consequential-action contract requires it.
- Agent Bridge productionization must not weaken human authority, case isolation, security, audit, approval, or migration boundaries.

## AUTHORITATIVE_REFERENCES

- `AGENTS.md` — agent rules and documentation hierarchy.
- `CONSTITUTION.md` — stable project principles.
- `DECISIONS.md` — accepted architectural/governance decisions and history.
- `ROADMAP.md` — authoritative plan and future-file registry.
- `docs/codex-agent-workflow.md` — Agent Execution Protocol.
- `docs/d-019-controlled-agent-assisted-development-workflow.md` — human/agent authority boundary.
- `docs/approval-gate.md` — D-017 approval contract.

Historical stage details belong in Git history, `DECISIONS.md`, and dedicated documentation rather than being reconstructed from chat memory.
