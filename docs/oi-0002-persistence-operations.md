# OI-0002 protected persistence operations

Status: implementation control for the OI-0002 remediation candidate; independent acceptance pending.

## Deployment requirements

- Keep the live SQLite database and its `.audit-anchor` beside each other on a protected, local, non-synchronized filesystem. Paths containing OneDrive, Google Drive or Dropbox are rejected.
- Provision the HMAC integrity key from a protected secret source at runtime. It must be at least 32 bytes, must not be stored in Git or in the database directory, and must be retained for restore.
- Restrict the database, WAL/SHM files, audit anchor, backups and key to the service account and authorized operators using operating-system ACLs. SQLite encryption is not claimed.
- Route every operation through the existing Kernel permission decision with exact case, tax year and run scope. Do not expose storage primitives directly.

## Backup and restore

Use `IdentityPersistence.backup()` while the store is open. It creates a SQLite online backup and copies the verified audit anchor. Store the database, matching anchor and separately protected key as one recovery set. Restore to a protected non-synchronized directory, then open with the same key; open-time schema, row-integrity and audit-continuity verification must pass before service.

Never copy only the database or only the anchor. A missing, stale or mismatched anchor is a fail-closed integrity event.

## Migration and recovery policy

Schema v2 is the only writable schema. The reviewed v1-to-v2 migration is one `BEGIN IMMEDIATE` transaction: legacy tables are renamed, verified content is copied, v2 indexes are created and legacy tables are dropped before the single commit. Any injected failure before commit rolls back to intact v1; a failure after commit must reopen as fully verified v2 with its matching audit anchor. A v1 store containing subject-fact bindings is rejected without mutation because v1 did not retain enough lineage to construct the frozen envelope safely; migration then requires a separately reviewed evidence-backed procedure and Human Gate. Unknown, unversioned or malformed schemas fail closed.

Case-party role corrections are immutable revisions. Only an authorized, evidence-resolved correction may close an open half-open interval. Preserve both the original and corrected revision, verify both on reopen, and apply the existing role-specific overlap/cardinality rules to every successor binding.

Writes and their audit events share one transaction. Fault-injection coverage verifies rollback before commit and fail-closed reopen after an injected post-commit interruption. After any process, host or storage failure, reopen the store and require the complete integrity verification before further use. Do not repair digests, anchors or rows in place.

## Incident boundary

On HMAC, schema, audit-chain, anchor, payload, date or enum failure: stop access, preserve the database/anchor/key set, record the affected deployment and exact error outside the damaged store, and escalate for independent forensic review. Do not regenerate the anchor from the database as a repair.
