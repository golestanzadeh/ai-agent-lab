# Documentation Index

Start with the repository-root `PROJECT_CHECKPOINT.md`. This directory contains focused contracts and implementation references, not current project status.

## System and governance

- `../CONSTITUTION.md` — ratified supreme Project Constitution v2 governing all Agents, permissions, transfers, and Orchestrator work.
- `architecture.md` — system components and boundaries.
- `requirements.md` — supported requirements.
- `use-cases.md` — workflow use cases.
- `codex-agent-workflow.md` — controlled Codex workflow.
- `d-019-controlled-agent-assisted-development-workflow.md` — accepted development governance.
- `agent-bridge-production.md` — Work/GitHub/Codex control plane.
- `local-sync-agent.md` — safe GitHub/Windows synchronization.
- `windows-relay.md` — bounded GitHub-to-Windows relay.

## Case, identity, storage, and evidence

- `case-management.md`
- `case-party-model.md`
- `case-registry.md`
- `person-entity-registry.md`
- `case-creation-workflow.md`
- `case-scoped-drive-resolver.md`
- `state-and-memory.md`
- `audit-observability.md`
- `google-drive-storage-adapter.md`
- `document-inventory.md`
- `document-processing.md`
- `document-identity.md`
- `document-identity-persistence.md`
- `case-isolation-tests.md`

## Approval and controlled migration

- `approval-gate.md`
- `artifact-identity.md`
- `case001-approval-context.md`
- `case001-live-target-preflight.md`
- `case001-migration-compatibility.md`
- `case001-migration-preflight.md`
- `durable-approval-lifecycle.md`
- `physical-migration-executor.md`
- `agent-case-storage-provisioning.md`

These contracts remain reusable even though the CASE-001 migration stage completed.

## Tax runtime

- `d025-tax-calculation-contract.md` — canonical evidence, source, and calculation policy.
- `d027-tax-agent-runtime.md` — six-role specialist runtime.
- `d028-chief-tax-auditor.md` — Chief supervision and historical first-run verification.
- `d023-tax-category-organization.md` — retained evidence of real category organization.

Historical D-024/D-025 progress snapshots were removed after their durable rules were consolidated. Current CASE status must be taken only from `PROJECT_CHECKPOINT.md`.

## Documentation rules

- Do not place private case documents, credentials, tokens, or provider object IDs here.
- Do not use a focused technical document as current-state authority.
- Update current state and the checkpoint in the same governed change set.
- Preserve reusable contracts, tests, verified lessons, and recovery evidence.
- Remove temporary probes and superseded progress snapshots when they no longer provide unique value.
