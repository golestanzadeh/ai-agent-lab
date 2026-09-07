# CASE-001 Live Target-Scope Preflight

## Status

Implemented as a **read-only live validation boundary**. No physical migration is performed.

## Purpose

The migration manifest proves that the live CASE-001 source inventory can be reconciled with stable Document Identity records. Structural preflight additionally proves that the intended target must be an actual, empty storage scope.

This stage connects those two facts to one explicitly supplied Google Drive target folder.

## Security boundary

The live target preflight does **not** perform Drive-wide discovery. The target folder is supplied explicitly by `CASE_001_TARGET_ROOT_ID`.

The source remains protected by the existing `CaseScopedDriveResolver` and `GoogleDriveMetadataAdapter`. The target validator performs only explicit metadata access to the supplied target object and an immediate-child listing for that object.

If the target object is unavailable, trashed, or not a folder, the operation fails closed.

## Checks

The live preflight requires all of the following:

1. CASE-001 and tax year 2024 are present in the validated manifest.
2. The migration manifest contains at least one document.
3. Source and target scopes are different.
4. Every source object is unique in the manifest.
5. Every logical document identity is unique.
6. Manifest document count matches its mappings.
7. The explicitly supplied target object exists.
8. The target object is an active Google Drive folder.
9. The target folder contains zero non-trashed immediate children.
10. The structural migration preflight passes.

A non-empty target fails closed. The executor must never silently merge into an existing target.

## Local live harness

Required environment variables:

```powershell
$env:CASE_001_DOCUMENTS_ROOT_ID="<CASE-001 Documents folder ID>"
$env:CASE_001_TARGET_ROOT_ID="<actual empty target folder ID>"
```

Optional identity snapshot:

```powershell
$env:CASE_001_IDENTITY_SNAPSHOT="artifacts/case001/document_identity.json"
```

Run:

```powershell
cd C:\Users\rezag\ai-agent-lab
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe scripts\case001_live_target_preflight.py
```

The output intentionally reports only safe target metadata and validation facts. Provider object IDs must not be committed to GitHub or written into project documentation.

## D-020 manifest provenance

The live result now records `manifest_identity`, the exact existing Manifest
`ArtifactIdentity` used during preflight. The optional default is `None` for
legacy callers; D-020 composition rejects missing or mismatched provenance.
The nested `structural_preflight` remains the version-1 D-018 preflight artifact
with an unchanged hashed payload. This binding distinguishes different manifest
contents without introducing run/attempt provenance or approval lifecycle logic.
See `case001-approval-context.md` for composition validation and test evidence.

## Mutation policy

This stage performs no:

- create
- copy
- move
- rename
- delete
- overwrite

A successful live preflight is **not** authorization to migrate documents.

## Required next gate

After a successful live target preflight, the next boundary is an explicit **Human Approval Record** bound to:

- `case_id`
- tax period
- migration manifest identity/version
- preflight result
- intended operation
- approver/actor
- timestamp
- authorization reference

Only after that approval boundary should a future physical executor be designed. The executor must include partial-failure handling, rollback semantics, and post-migration verification before the legacy alias can be retired.

## Verification evidence

The unit suite for this stage is deterministic and covers empty-folder success, missing target, non-folder target, trashed target, non-empty target, and invalid manifest handling.

The unit suite must be run locally before its result is recorded as verified. A skipped test, created test file, or expected result is not evidence of a pass.
