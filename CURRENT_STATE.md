# Current State

## CURRENT_STAGE

**D-021 — Agent-managed CASE-001 target provisioning and real approval-record preparation.**

Work is on branch `d021-agent-case-provisioning`. The branch contains the accepted clarification that standard case-storage provisioning is an authorized agent operation inside the existing Case Creation architecture; it is not physical document migration.

D-021 implementation is complete and has reached its end-of-day checkpoint. The configured system root and existing metadata-read plus drive.file credentials supported creation of the standard CASE-001 target tree. All six standard subfolders were created, the 15-document real Manifest was validated, the target Documents folder passed empty-target preflight, and D-020 composed the exact context. The D-017 requester-actor correction records the authorized requester as `AGENT`, while `APPROVAL_GRANTED` remains a human action. Independent human review passed and human authorization was issued on 2026-09-08: `HUMAN-AUTH-2026-09-08-CASE-001-PHYSICAL-MIGRATION` by Reza Golestanzadeh. The exact reviewed binding produced an APPROVED state in the existing process-local ApprovalStore and a private review export. It was not consumed; physical migration was not started; source documents remain unchanged.

### D-021 end-of-day checkpoint — 2026-09-08

Implementation and the D-017 requester-actor correction are complete on `d021-agent-case-provisioning`. The approved review state was produced from the exact CASE-001 / `RUN-00000001` Manifest and Preflight identities, with the human authorization reference `HUMAN-AUTH-2026-09-08-CASE-001-PHYSICAL-MIGRATION`. Verification confirmed `APPROVAL_REQUESTED` was attributed to the authorized agent and `APPROVAL_GRANTED` to Reza Golestanzadeh. The approval is **not consumed**. Physical migration is **not started**, and source documents are unchanged.

The approval-preparation implementation checkpoint is commit `8f8b12491e0dab9fd94aa76be99af429896b06cd` on `d021-agent-case-provisioning`; the private review export and Drive references remain under ignored `artifacts/case001/`. The current ApprovalStore is process-local and in-memory, so this APPROVED review record is not durable or reloadable after process exit. That is the remaining architecture/runtime blocker. The next session must begin with an explicitly accepted durable approval-record lifecycle before any physical migration execution may be designed or considered. No physical operation is authorized by this checkpoint.

## LAST_ACCEPTED_STAGE

**D-020 — CASE-001 Approval Context Composition: accepted, integrated, and closed.**

Accepted implementation: `e6f28e89acf45541e4cfaa55c9efd8db35fc7909`.
Integrated main validation completed with **223 passed, 1 skipped**. D-020 composes the generic D-017 execution context from the exact migration Manifest and successful Live Target Preflight artifact identities. It does not grant/consume approval or perform migration.

Canonical main before D-021 branch work: `ee59dadbc2c7f2433e8291f849fef3048b574a9c`.

## NEXT_BOUNDARY

The next session must not execute physical migration from the review export. `ApprovalStore` remains in-memory, so the approved state has no durable/reloadable lifecycle authority after the preparation process ends. A durable approval-record/persistence architecture and its acceptance are required before any physical execution can be designed or authorized. No new persistence contract was introduced. Main remains unchanged.

Verification: focused provisioner/preparation tests and relevant creation/approval/D-020 regression suites: **103 passed**; full suite: **241 passed, 1 skipped**. The opt-in live isolation test skipped; the authorized create-only provisioning and real read-only preflight were executed separately and passed.

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
- Real CASE-001 / 2024 target tree was provisioned with all six standard subfolders; target Documents was verified empty. Exact provider references are privately journaled. Real run: RUN-00000001; PENDING approval: APP-00000001 (both process-local identifiers).
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
