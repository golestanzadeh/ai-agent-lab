# Owner resolutions: case IDs, backups, document ownership
Date: 2026-10-27
Status: OWNER-APPROVED DESIGN / DOCUMENTATION ONLY / IMPLEMENTATION NOT AUTHORIZED
Parent contract: docs/case-lifecycle-owner-decisions-2026-10-27.md (commit d6741bf)
These later decisions supersede any conflicting open proposals in the parent document.

## 1. Case ID allocation
- A case is EMPTY if it currently has no assigned tax documents, even if it previously had documents that were subsequently removed.
- Once an unfinished empty case is safely deleted, its number is FREE and can be used for a new case in that same tax year. It has no remaining active case dependencies.
- A deleted case with a retained backup reserves its case number for that backup. The number must not be issued to a different case while the backup exists.
- Allocation must check both active cases and backup reservations, never simply max(case number)+1.
- The immutable internal case identity/audit lineage must not confuse an old deleted case with a new case reusing the same visible number. Resolve this contract safely before implementation.
- Restoring a backed-up case must refuse conflicting existing active identities. The policy for deleting backups and releasing their reservations is NOT approved.

## 2. Backup and restoration
- Store case backups in the project Google Drive Backups folder, under a subfolder for the corresponding tax year, outside the active Tax_Years/<year> folder that may later be removed.
- For an unfinished case that has documents, after one owner confirmation, take and verify a restorable backup BEFORE any deletion.
- The backup includes all case-specific Google Drive documents/folder structure, associated SQLite records, relationships and sufficient metadata/manifest/checksums for verification and recovery.
- Restoration must return the documents to the same case's folder under the original tax year, and restore SQLite records and links to their correct logical locations. Google Drive objects recreated by upload may have new Drive IDs; remap them correctly.
- Prefer the simplest safe, deterministic restore workflow. Fail closed on incomplete backup, checksum mismatch, case-ID collision, or partial restore. Never report success until both Drive and SQLite readback checks pass.
- Removing the last active case of a tax year must never remove backups stored under Backups/<year> or their case-ID reservations.
- Use direct Google Drive API. Google Drive Desktop is not part of the architecture.

## 3. Documents: strict exclusive case ownership
- Each document uploaded to a particular tax year and case is a distinct, case-owned object. It is not a shared mutable file between cases or family members.
- If the same source document is needed in another case, it must be uploaded again as a separate independent copy belonging to that other case.
- Deleting a document from an unfinished case must delete its dedicated file from Google Drive, not merely unlink it from the database. Delete the case-specific database association and invalidate dependent analyses, evidence and results.
- A deletion in one case must not delete an independently uploaded copy in another case.
- Verify file ownership, Drive parent scope and canonical SQLite binding before deletion; ambiguous or missing ownership => reject.
- If the ENTIRE tax workflow is finally completed, both case deletion and document deletion are absolutely prohibited. Intermediate analysis completion is not final completion.

## 4. UI and execution boundaries
- Preserve the previously owner-tested same-page new-case confirmation modal, with each existing case ID displayed on its own line, cancel/confirm and server-side stale-state revalidation.
- Year selector lists years and their cases. Explicit active case selection displays e.g. «CASE-2025-0003 انتخاب و فعال است.» and scopes every subsequent operation.
- Unfinished empty case: one warning, deletion without mandatory backup, reusable number. Unfinished case with documents: one warning, verified backup then deletion, reserved number. Final-completed case: deletion denied without exception.
- Removing the final live case of a year requires an additional warning; only delete the active year folder if empty and free of protected dependencies.
- Actual Drive file removal versus provider Trash/permanent purge and provider retention must be accurately disclosed; no promise of irreversibility.
- Preserve deterministic Kernel authorization, audit, lineage, default deny and the two owner approvals for any external tax transmission.
- No live cases, Drive files, SQLite records, source code or runtime state are to be mutated under this documentation-only authorization. CASE-2025-0001/0002/0003 remain untouched.

## 5. Future acceptance
Test independent per-case document ownership, deleting one copy without touching another, removing last document -> empty, empty-case number reuse, backup reservation, backup/restore round trip including Drive ID remapping, final-completion hard deny, last-year cleanup, stale/concurrent requests, and failure/recovery of cross-system writes. Use synthetic fixtures only and independent acceptance.
