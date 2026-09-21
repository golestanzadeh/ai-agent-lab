# Documentation Index

Start with the repository-root `PROJECT_CHECKPOINT.md`. This directory contains focused contracts and implementation references, not current project status.

## System and governance

- `../CONSTITUTION.md` — ratified supreme Project Constitution v2 governing all Agents, permissions, transfers, and Orchestrator work.
- `agent-organization-v1-proposal.md` — Human-ratified active organizational contract defining the 20 permanent Agent roles, three inactive domain templates, hierarchy, access levels, communication rules, Agent lifecycle, separation of duties, and O0–P4 path.
- `o2-machine-readable-contracts.md` — Phase O2 contract map, invariants, technical verification, and current Human acceptance boundary; machine-readable artifacts live under `../contracts/orchestrator/v1/`.
- `o3-deterministic-orchestrator-kernel.md` — persistent Kernel architecture, controls, failure behavior, inspection path, verification, and activation boundary.
- `o4-controlled-autonomous-development-pilot.md` — bounded autonomous-development pilot and recovery boundary.
- `o5-production-control-plane-readiness.md` — deterministic production-control-plane readiness evidence and activation boundary.
- `agent-runtime-activation-layer.md` — local synthetic Planning/Implementation/QE/Independent Acceptance runtime layer.
- `agent-runtime-recovery-inspector.md` — read-only runtime recovery classification and automatic-replay boundary.
- `plan-limit-continuation-controller.md` — live plan-limit inspection, pause thresholds, and guarded continuation.
- `development-setup.md` — supported local development setup.
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

## Controlled ERiC path

- `p1-controlled-elster-path.md`
- `p1-eric-adapter-contract.md`
- `p1-eric-material-process.md`
- `p1-eric-e10-2024-mapping.md`
- `p1-eric-e10-2024-declaration.md`
- `p1-eric-e10-2024-plausibility.md`
- `p1-eric-e10-2024-readiness.md`
- `p1-synthetic-preview.md`
- `p1-synthetic-submission-lifecycle.md`
- `p1-synthetic-submission-audit.md`
- `p1-synthetic-readiness-dossier.md`

## Local user interface

- `ui-phase-foundation.md`
- `ui-state-contract.md`
- `ui-interactive-prototype.md`
- `ui-synthetic-workflow.md`
- `ui-synthetic-document-intake.md`
- `ui-synthetic-review-preview.md`
- `ui-synthetic-decision-queue.md`
- `ui-synthetic-submission-readiness.md`
- `ui-synthetic-support.md`
- `ui-windows-launcher.md`
- `ui-phone-accessibility.md`
- `ui-local-security-headers.md`

## Documentation rules

- Do not place private case documents, credentials, tokens, or provider object IDs here.
- Do not use a focused technical document as current-state authority.
- Update current state and the checkpoint in the same governed change set.
- Preserve reusable contracts, tests, verified lessons, and recovery evidence.
- Remove temporary probes and superseded progress snapshots when they no longer provide unique value.
