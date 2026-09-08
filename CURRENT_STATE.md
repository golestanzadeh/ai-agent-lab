# Current State

## CURRENT_STAGE

**D-021 — Agent-managed CASE-001 target provisioning and real approval-record preparation.**

Work is on branch `d021-agent-case-provisioning`. The branch contains the accepted clarification that standard case-storage provisioning is an authorized agent operation inside the existing Case Creation architecture; it is not physical document migration.

D-021 is currently blocked at the Google OAuth credential boundary: the existing local token/loader uses `drive.metadata.readonly`, which cannot create the authorized standard case folders. The next execution step is a least-privilege credential upgrade/reauthorization, preferring `drive.file` while retaining required metadata-read capability.

## LAST_ACCEPTED_STAGE

**D-020 — CASE-001 Approval Context Composition: accepted, integrated, and closed.**

Accepted implementation: `e6f28e89acf45541e4cfaa55c9efd8db35fc7909`.
Integrated main validation completed with **223 passed, 1 skipped**. D-020 composes the generic D-017 execution context from the exact migration Manifest and successful Live Target Preflight artifact identities. It does not grant/consume approval or perform migration.

Canonical main before D-021 branch work: `ee59dadbc2c7f2433e8291f849fef3048b574a9c`.

## NEXT_BOUNDARY

Resume D-021 from the credential blocker:

1. update the OAuth loader/configuration for the minimum sufficient Drive scopes;
2. perform local OAuth reauthorization if required;
3. implement and test the real Google Drive `StorageScopeCreator`/case provisioner using existing Case Creation contracts;
4. create only the standard empty CASE-001 / tax-year-2024 target structure;
5. privately retain exact provider-returned storage references;
6. generate the exact real CASE-001 migration Manifest;
7. execute read-only Live Target Preflight;
8. compose the D-020 `ApprovalExecutionContext`;
9. prepare D-017 reviewable approval evidence/record up to the genuine human approver/authorization boundary.

Physical source-document migration remains outside this boundary.

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
- No physical Google Drive migration has occurred.
- No real CASE-001 target tree has yet been provisioned.
- No D-017 approval has been consumed.

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

## AUTHORITATIVE_REFERENCES

Read these only as required by the current task and expand context progressively:

- `AGENTS.md` — agent rules and documentation hierarchy.
- `CONSTITUTION.md` — stable project principles.
- `DECISIONS.md` — accepted architectural/governance decisions and history.
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
