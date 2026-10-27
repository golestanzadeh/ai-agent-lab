# Stage 3: document-bearing case deletion and restore contract
Date: 2026-10-27
Status: OWNER APPROVED DESIGN DIRECTION; DESTRUCTIVE IMPLEMENTATION GATED

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
- After restore, if all assigned tax documents are removed and no protected dependencies remain, the case qualifies for Stage 2 empty-case deletion: no new backup, visible number becomes reusable. The old backup remains valid but loses any exclusive claim on that number. Future restore obeys the collision rules above.
- An existing backup may not by itself reserve a visible number forever once the restored case is validly deleted empty. Do not erase the backup to achieve number reuse.
- Backups must not be located inside case/year paths eligible for deletion. Backup retention and destruction are separately governed; normal case delete never purges backups.

## Mandatory pre-implementation checks
Existing case_record.case_id is PRIMARY KEY and many tables key by case_id. There is no independent immutable case-instance ID. Introducing a restore alias without migration would corrupt audit and references. Implement a backwards-compatible identity/number separation only after architecture and security review. Do not repurpose or rewrite historical case_id or chained case_audit.

Test synthetic scenarios: document-bearing delete/verified backup, backup failure, partial Drive/SQLite failure, restart recovery, repeated restore, occupied number, restored-then-emptied case, empty deletion, number reuse, old backup restore after reuse, and protected/final case rejection. No real user case may be mutated in these tests.

## Current milestone
Design contract documented. No Stage 3 delete/restore endpoint enabled. Owner case CASE-2025-0001 and all three real documents remain untouched.
