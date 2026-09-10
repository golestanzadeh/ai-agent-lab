# Current State

## CURRENT_STAGE

**D-021 — Agent-managed CASE-001 target provisioning and real approval-record preparation.**

D-021 implementation is complete on branch `d021-agent-case-provisioning`. Standard case-storage provisioning is an authorized agent operation inside the existing Case Creation architecture; it is not physical document migration.

The configured system root and existing metadata-read plus `drive.file` credentials supported creation of the standard CASE-001 / 2024 target tree. All six standard subfolders were created. The real 15-document Manifest was validated, target Documents passed empty-target preflight, and D-020 composed the exact D-017 execution context. The D-017 requester-actor correction records the authorized requester as `AGENT`, while `APPROVAL_GRANTED` remains a human action.

Independent human review passed. Human authorization was issued on 2026-09-08 as `HUMAN-AUTH-2026-09-08-CASE-001-PHYSICAL-MIGRATION` by Reza Golestanzadeh. The exact reviewed binding produced an **APPROVED** state in the existing process-local `ApprovalStore` and a private review export. The approval was **not consumed**. Physical migration was **not started**. Source documents remain unchanged.

The approval-preparation implementation checkpoint is commit `8f8b12491e0dab9fd94aa76be99af429896b06cd`. The D-021 end-of-day documentation checkpoint before the 2026-09-10 baseline cleanup is commit `9b316797015026b1c3de74c0226c8752b87fe344`. Private review evidence and Drive references remain under ignored `artifacts/case001/`.

The current `ApprovalStore` is process-local and in-memory. Therefore the APPROVED state is not durable or reloadable after process exit and the private review export is not executable authorization. A separately accepted durable/reloadable approval-record lifecycle remains the architecture/runtime blocker before physical migration execution may be designed or considered.

## LAST_ACCEPTED_STAGE

**D-020 — CASE-001 Approval Context Composition: accepted, integrated, and closed.**

Accepted implementation: `e6f28e89acf45541e4cfaa55c9efd8db35fc7909`.
Integrated main validation completed with **223 passed, 1 skipped**. D-020 composes the generic D-017 execution context from the exact migration Manifest and successful Live Target Preflight artifact identities. It does not grant/consume approval or perform migration.

Canonical main before D-021 branch work: `ee59dadbc2c7f2433e8291f849fef3048b574a9c`.

## BASELINE — 2026-09-10

This section is the canonical starting baseline for Agent Bridge productionization.

- Working branch: `d021-agent-case-provisioning`.
- Pre-baseline branch checkpoint: `9b316797015026b1c3de74c0226c8752b87fe344` (`Record D-021 approval checkpoint`).
- Canonical `main`: `ee59dadbc2c7f2433e8291f849fef3048b574a9c` (D-020 accepted/integrated state).
- D-021 is implementation-complete but has not been declared an accepted/integrated stage on `main`.
- Latest recorded D-021 final verification before this documentation-only cleanup: targeted **84 passed**; full suite **246 passed, 1 skipped**.
- This baseline cleanup changes documentation only; it does not claim a new test execution.
- Approval state produced during the reviewed process: **APPROVED, NOT CONSUMED**.
- Durable/reloadable approval authority: **NOT IMPLEMENTED**.
- Physical Google Drive migration: **NOT STARTED**.
- Source CASE-001 documents: **UNCHANGED**.
- Agent Bridge PoC has been completed in a separate experimental repository. Its architecture/protocol/lessons may inform productionization, but its experimental files and workflows are not part of this repository and must not be copied or merged blindly.
- The approved Agent Bridge production migration plan must be executed sequentially. Step 1 is this baseline/canonical-state cleanup and durable documentation. Production architecture/governance definition is Step 2; no Agent Bridge workflow, secret, permission, branch-protection change, or automation activation is authorized by this baseline.

## NEXT_BOUNDARY

The immediate project-management boundary is completion and acceptance of **Agent Bridge Production Migration Step 1 — Baseline + Durable Documentation + Canonical State Cleanup**. After Step 1 acceptance, work may proceed only to Step 2, production Agent Bridge architecture/governance definition.

The underlying AI-Tax-Agent runtime boundary remains unchanged: before any physical migration execution may be designed or considered, a durable/reloadable approval-record lifecycle architecture must be explicitly accepted and then implemented/tested. Agent Bridge productionization does not itself authorize physical migration or approval consumption.

## VERIFIED_RUNTIME_STATE

- Local execution environment: Windows + project-local Python virtual environment; pytest is operational.
- GitHub is the durable source of truth; local Python/Docker is the execution environment; Google Drive holds private source/working case data.
- Multi-case architecture uses mandatory `case_id`, persistent `person_id`/`entity_id`, and explicit `tax_period`.
- Case Registry, Person/Entity Registry, Case↔Identity Association, Case Creation, Case-Scoped Drive Resolver, Case State/Run ID, Audit, and isolation boundaries are implemented and tested.
- Google Drive metadata adapter and case-scope isolation were live-verified read-only.
- Real CASE-001 source inventory contains **15 PDFs and 0 folders** within the selected source Documents scope.
- All 15 source PDFs have stable logical Document Identity records in the local private snapshot `artifacts\\case001\\document_identity.json`.
- CASE-001 migration compatibility, deterministic Manifest generation, Live Target Preflight, D-017 approval gate, D-018 artifact identity, and D-020 approval-context composition are implemented.
- D-019 controlled agent-assisted development governance is accepted.
- Real CASE-001 / 2024 target tree was provisioned with all six standard subfolders; target Documents was verified empty. Exact provider references are privately journaled.
- Real run identifier: `RUN-00000001`.
- Approval identifier: `APP-00000001` (process-local identifier). The reviewed process produced **APPROVED**, not consumed; this state is not durable/reloadable after process exit.
- No D-017 approval has been consumed.
- No physical Google Drive migration has occurred.

## ACTIVE_CONSTRAINTS

- Source documents are immutable.
- No broad/unscoped Drive search for case data.
- Every case-data operation requires validated case scope and must fail closed on ambiguity.
- Private Drive IDs, OAuth tokens, credentials, client secrets, and private document information must never be committed.
- Standard case provisioning may create the approved case root/subfolders and persist exact returned references without per-folder human approval.
- Provisioning authority does **not** authorize source-document copy/move/rename/delete/overwrite, permission changes, approval fabrication/consumption, physical migration, destructive operations, or architecture/contract changes.
- Human authority remains required for architecture/contracts, stage acceptance, consequential migration authorization, destructive operations, and other governance decisions defined by D-019.
- OAuth scope should follow least privilege; do not request unrestricted Drive access unless the approved design demonstrably requires it.
- The Agent Execution Protocol in `docs/codex-agent-workflow.md` governs development execution: progressive context loading, targeted-first testing, bounded changes, and compact routine reports.
- Agent Bridge productionization must not weaken any existing human-authority, case-isolation, security, audit, approval, or migration boundary.

## AUTHORITATIVE_REFERENCES

Read these only as required by the current task and expand context progressively:

- `AGENTS.md` — agent rules and documentation hierarchy.
- `CONSTITUTION.md` — stable project principles.
- `DECISIONS.md` — accepted architectural/governance decisions and history.
- `ROADMAP.md` — authoritative plan and future-file registry.
- `docs/codex-agent-workflow.md` — Agent Execution Protocol.
- `docs/d-019-controlled-agent-assisted-development-workflow.md` — human/agent authority boundary.
- `docs/agent-case-storage-provisioning.md` — D-021 provisioning clarification.
- `docs/case-creation-workflow.md` — case creation/storage-scope contract.
- `docs/google-drive-storage-adapter.md` — Drive adapter boundary.
- `docs/case001-migration-compatibility.md` — CASE-001 migration compatibility contract.
- `docs/case001-live-target-preflight.md` — live target preflight contract.
- `docs/case001-approval-context.md` — D-020 composition contract.
- `docs/approval-gate.md` — D-017 approval contract.

Historical stage details and earlier test evidence belong in Git history, `DECISIONS.md`, and their dedicated documentation rather than being repeated here.
