# Owner acceptance: document-bearing case deletion lifecycle (2026-10-28)

Status: **OWNER_ACCEPTED / CLOSED** for the bounded case lifecycle feature only.
Authority: explicit Owner reports and final acceptance in the 2026-10-28 conversation.
Evidence type: Owner-observed real Dashboard and Google Drive API operations; not a new independent security audit.

## Owner-observed PASS sequence

1. CASE-2025-0001 with real tax documents: deletion readiness required a verified backup before the final delete action became available.
2. Owner confirmed backup, then deleted the document-bearing case; it disappeared from the real Dashboard and Google Drive; verified backup remained in Drive.
3. Creating another 2025 case while 001 remained backup-reserved created CASE-2025-0005 (not 001); Owner confirmed.
4. The newly created empty CASE-2025-0005 was deleted without requiring a backup; Owner confirmed.
5. Verified backup of CASE-2025-0001 was restored successfully; Owner confirmed.
6. Owner individually deleted the real tax documents from restored CASE-2025-0001; PASS.
7. Owner deleted now-empty CASE-2025-0001; PASS.
8. Owner permanently deleted the verified 001 backup; PASS.
9. Backup number reservation was released, and a new CASE-2025-0001 for tax year 2025 was successfully created; PASS.
10. Owner inspected Google Drive and confirmed the new case structure and correctness; PASS.

The Owner explicitly accepted and closed the **document-bearing case deletion feature** after these practical tests. The new CASE-2025-0001 is a fresh case, not a claim that old tax documents still exist.

## Deferred mandatory final-tax-case protection

**Not accepted or tested:** protection of a finalized tax case. At the later tax-workflow finalization milestone, design and enforce an absolute deletion prohibition for a finalized tax case, **even if a verified backup exists**. This must be a server-side invariant at every deletion entrypoint and must be independently tested against UI and direct API attempts, including backup-present scenarios. The Owner deferred further deletion design and acceptance to the actual finalized tax case test. Do not claim that the current feature already enforces this future invariant.

## Boundaries and governance

- This acceptance is limited to real-case backup, restore, document deletion, empty/document-bearing case deletion, backup deletion, reservation release and number reuse, as observed by the Owner.
- No ELSTER submission, final declaration, protected taxpayer processing, operational identity/C09, DR-01..DR-04, independent product security acceptance or release gate is closed by this decision.
- No external tax transmission is authorized. Two distinct Owner approvals remain mandatory for submission.
- Direct Google Drive API and canonical SQLite remain the approved storage boundaries; Google Drive Desktop is not part of this workflow.
- Historical CASE-2025-0002 execution evidence remains in docs/case-2025-0002-final-lifecycle-test.md and is not rewritten.
- This record contains no raw financial documents, personal tax facts, credentials or sensitive database content.
- No new case creation, deletion, restore or backup operation is authorized by this documentation-only acceptance record.
