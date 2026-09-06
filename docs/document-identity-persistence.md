# Document Identity Persistence Boundary

**Status:** Implemented local persistence baseline; production durable storage is still future work.
**Last updated:** 2026-09-06

## Why this boundary exists

`DocumentIdentityRegistry` originally lived only in memory. That is sufficient for unit tests, but it is not sufficient for a real CASE-001 migration manifest: a new process would otherwise generate new logical document IDs and could not prove continuity with a previous run.

Before generating the real CASE-001 migration manifest, the project therefore establishes a restart-safe local snapshot boundary for Document Identity.

## Contract

The identity snapshot is:

- scoped to exactly one `case_id`;
- versioned with `schema_version`;
- complete for that case's document records and source observations;
- validated before import;
- deterministic with respect to stored logical IDs and sequence counters;
- stored locally, outside GitHub;
- allowed to contain private provider object IDs locally;
- never a substitute for the Case Registry or case-scoped storage resolver.

A snapshot from another case must fail closed.

## Local persistence

The runtime now provides:

- `export_snapshot(case_id)`;
- `save_snapshot(case_id, path)`;
- `load_snapshot(case_id, path)`;
- `import_snapshot(case_id, payload)`.

The intended CASE-001 local path is under `artifacts/`, which is ignored by Git. The snapshot must never be committed because it can contain private Google Drive object IDs.

## Live bootstrap sequence

`scripts/case001_identity_bootstrap.py` is a read-only live harness:

```text
Case Registry
    ↓
Case-Scoped Drive Resolver
    ↓
Google Drive Metadata Adapter
    ↓
Live CASE-001 Inventory
    ↓
Load prior local identity snapshot (if present)
    ↓
Resolve current inventory against logical identities
    ↓
Persist updated local identity snapshot
```

It does not create, move, rename, delete, overwrite, or copy Drive objects.

Required environment:

```powershell
$env:CASE_001_DOCUMENTS_ROOT_ID="<CASE-001 Documents folder ID>"
```

Optional snapshot path:

```powershell
$env:CASE_001_IDENTITY_SNAPSHOT="artifacts/case001/document_identity.json"
```

Run from the repository root with:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe scripts\case001_identity_bootstrap.py
```

The output is local verification evidence. Do not paste private Drive object IDs into GitHub issues, documentation, or commits.

## What this does and does not prove

A successful bootstrap proves that the current live inventory can be resolved against the local identity snapshot without creating a second logical identity for an already-known source object.

It does **not** prove:

- production-grade database durability;
- concurrent multi-process writes;
- tamper-proof persistence;
- backup/restore guarantees;
- physical Drive migration safety;
- content-level document equivalence.

Those are later architecture layers.

## Gate for the real manifest

The real CASE-001 manifest should not be generated until the bootstrap has been executed against the live 15-document inventory and the local snapshot contains a stable logical identity for every non-folder source object.

The manifest generation run must then load that snapshot rather than constructing a fresh identity registry from scratch.
