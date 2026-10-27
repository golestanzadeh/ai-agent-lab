# Stage 3: document-bearing case deletion and restore contract
Date: 2026-10-27
Status: OWNER APPROVED DESIGN DIRECTION; BACKUP RETENTION AMENDMENT APPROVED; DESTRUCTIVE IMPLEMENTATION GATED

## Authority and scope
Keep canonical SQLite, Google Drive API, deterministic Kernel, existing Human Gates and default-deny. No Drive Desktop, separate backup service, new database, or real-case deletion without a case-specific Owner confirmation. Stage 2 empty-case behavior stays unchanged. Fully completed cases and their documents are never deletable. Ambiguous finality blocks deletion.

## Identity invariant
Visible case number is reusable only under the approved empty-case rule. Internal immutable identity of a backed-up case is not the visible case number. Backup identity, original identity, original number, source year, version and content hashes remain stable across restores. Restoring must never overwrite an unrelated active case or change historical audit records.

## Document-bearing delete
1. Validate owner, exact case/year, complete workflow status, protected records, SQLite and Drive inventories, document dependencies and any pending operations; fail closed on uncertainty.
2. Show case-specific warning and get one Owner confirmation. Additional warning for the last case of a tax year.
3. Make a restorable backup outside the deletable case/year tree: a consistent SQLite state export, Drive file bytes, manifest of IDs, names, sizes, SHA-256, relations, original identity and audit references. Preserve official originals. Check all hashes and restoration feasibility before any deletion.
4. Record a durable backup receipt, protected backup identity and permanently reserved original visible number while the document-bearing deletion remains unreversed. Reserve outside the deletable year folder.
5. Execute recoverable journaled trash and audited registry cleanup. SQLite and Drive are not atomic: after restart, reconcile pending steps. Do not report success until independent readback confirms both.
6. Keep backup and reservation records independent of the deleted case row. Backup is not consumed by restore.

## Restore and reuse
- A valid backup may be requested repeatedly; each restore attempt is separately authorized and audited.
- If original number is free, a restore may reclaim it only after checking the durable reservation and identity ownership.
- If the original number belongs to another active identity, NEVER overwrite or merge. Require a new available visible number and a deterministic migration of all case-scoped references. If such migration is not independently validated, block restore.
- If original identity is already active, reject duplicate restore; never silently replace its current documents.
- After restore, if all assigned tax documents are removed and no protected dependencies remain, the case qualifies for Stage 2 empty-case deletion: no new backup is required. However its visible number remains reserved while any restorable backup for that original case identity exists. Future restore obeys active-identity and collision guards.
- Any existing restorable backup keeps the original visible number reserved even after the restored case is validly deleted empty. Number reuse is forbidden until the last such backup is explicitly deleted and verified absent, the case is inactive, and protected/audit dependencies permit release.
- Backups must not be located inside case/year paths eligible for deletion. Backup retention and destruction are separately governed; normal case delete never purges backups.

## Mandatory pre-implementation checks
Existing case_record.case_id is PRIMARY KEY and many tables key by case_id. There is no independent immutable case-instance ID. Introducing a restore alias without migration would corrupt audit and references. Implement a backwards-compatible identity/number separation only after architecture and security review. Do not repurpose or rewrite historical case_id or chained case_audit.

Test synthetic scenarios: document-bearing delete/verified backup, backup failure, partial Drive/SQLite failure, restart recovery, repeated restore, occupied number, restored-then-emptied case, empty deletion, number reuse, old backup restore after reuse, and protected/final case rejection. No real user case may be mutated in these tests.

## Current milestone
Design contract documented. No Stage 3 delete/restore endpoint enabled. Owner case CASE-2025-0001 and all three real documents remain untouched.

## Owner amendment: explicit backup deletion and reservation release (2026-10-27)
This section supersedes any contrary number-release rule above and in prior design notes.

- Backups may be deleted only through a separate, explicitly authorized operation. Never delete backups as a side effect of case deletion, restore or document removal.
- Before backup deletion, verify exact backup ID, case identity, owner, year, storage scope, completeness of backup inventory, finality/legal retention holds, audit/lineage dependencies and any active or pending restore. Fail closed on uncertainty.
- Show a specific warning about loss of recovery ability. Require explicit Owner confirmation. If legal/official retention or protected dependencies prohibit deletion, reject regardless of confirmation.
- Delete only the selected backup, with recoverable journal and independent Drive/SQLite readback. Never claim permanent erasure when only moved to Drive Trash. A recoverable trashed copy still counts as an existing backup for reservation purposes until a verified irreversible deletion or an approved non-restorable state under the retention contract.
- After backup deletion, recompute reservation under lock from authoritative active case identity plus *all* surviving restorable backups and protected holds. If any backup survives, keep reservation.
- Release a visible case number only when the corresponding case is inactive, zero restorable backups remain (including recoverable trash copies), and no protected identity/audit/legal dependency forbids reuse. Persist and audit the release before allowing case-number allocation.
- Deleting an empty restored case requires no *new* backup but MUST NOT release its number while any previous restorable backup remains. This overrides the generic Stage 2 empty-case number-reuse rule for identities with surviving backups.
- Restoring a backup must not overwrite an active case. Duplicate identity, stale reservation and number collision fail closed.
- Keep immutable audit events and backup-deletion receipts as appropriate, even after release; do not rewrite history.

Mandatory synthetic tests: delete one of two backups (still reserved); delete final backup while case active (still unavailable); delete empty restored case while backup survives (reserved); delete final backup while case inactive (release only after readback); Drive Trash remains recoverable (still reserved); failed backup delete (still reserved); pending restore (deny); retention hold (deny); concurrent create/delete/release (no duplicate number).
No real backup or case deletion is authorized by this design amendment.
