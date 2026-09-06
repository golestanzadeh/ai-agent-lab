# Google Drive Storage Adapter

## Status

Stage defined and implementation started. The six stages are the controlled rollout for case-scoped Google Drive access. The stages are recorded as one ordered work package; implementation may proceed in parallel where dependencies permit, but no live CASE-001 document inventory is allowed until the scope and adapter gates pass.

## Six-stage rollout

### Stage 1 — Storage Adapter Contract

Define a provider-neutral storage interface between the deterministic Case-Scoped Resolver and any physical storage provider.

Requirements:
- every case-data operation requires `case_id`;
- storage scope is resolved from the Case Registry, never from the caller's free-form path;
- document identity is opaque to higher layers;
- no unscoped list/search API exists;
- metadata operations are separated from content operations;
- out-of-scope access fails closed.

Deliverable:
- provider-neutral adapter protocol and stable metadata model.

### Stage 2 — Case-Scoped Resolver Integration

Bind the adapter to `CaseScopedDriveResolver` so a physical storage root can only be obtained from a validated `case_id`.

Required chain:

```text
case_id
  -> Case Registry
  -> ResolvedCaseScope
  -> Storage Adapter
  -> exact root
```

The adapter must not resolve a case independently and must not scan Drive to find one.

### Stage 3 — Google Drive Metadata Adapter

Implement the Google Drive provider using the existing metadata-only OAuth capability.

Initial scope:
- list immediate children of the case root;
- retrieve metadata for an explicitly requested object;
- verify object containment inside the case root;
- return normalized metadata;
- do not read PDF/file contents.

The implementation must use exact Drive file IDs supplied by the resolved scope or a case-scoped request. Generic Drive-wide search is prohibited.

### Stage 4 — Deterministic Scope Enforcement

Enforce containment before returning any case object.

Rules:
- root object is valid for its own case;
- direct and nested descendants are valid only when their parent chain terminates at that case root;
- sibling, parent, unrelated, deleted/trashed, or unknown objects are rejected;
- a document ID alone never overrides the resolved case scope;
- ambiguous or incomplete ancestry fails closed.

### Stage 5 — Adapter and Scope Tests

Build deterministic unit tests plus a live integration harness.

Minimum test matrix:
- CASE-A lists only A's root children;
- CASE-B lists only B's root children;
- A cannot retrieve B's document;
- B cannot retrieve A's document;
- nested descendant is accepted only under its own root;
- sibling/parent/unrelated object is rejected;
- unknown case is rejected;
- invalid root is rejected;
- unscoped listing/search is impossible through the adapter API.

A passing unit suite is not a claim of live Drive isolation. Live verification must be separately recorded.

#### Stage 5 verification procedure

Run from the repository root in the project's Python environment:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m pytest -q tests\unit\test_storage.py tests\unit\test_google_drive_storage.py
```

Expected result: all tests pass.

Then prepare two unrelated, manually created **test-only** Google Drive folders. They must not be CASE-001 folders and must contain no real tax documents. Put at least one harmless marker file in each folder so that each root has a visible child.

Set their Drive folder IDs locally without committing them:

```powershell
$env:TEST_DRIVE_ROOT_A="<test-folder-A-id>"
$env:TEST_DRIVE_ROOT_B="<test-folder-B-id>"
```

If the OAuth credential file is not at the harness default, set it locally:

```powershell
$env:GOOGLE_DRIVE_CREDENTIALS="<local-credentials-path>"
```

Run:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m pytest -q tests\integration\test_google_drive_scope_live.py
```

The live harness is read-only. It does not create, move, rename, delete, or modify Drive data. It verifies both directions of cross-case access and rejects using one test root as an object for the other case.

Do not substitute CASE-001 for either test root.

#### Stage 5 evidence rule

Only the exact locally executed output may be recorded as verification evidence. A test file existing in GitHub is not verification. A skipped integration test is not a passing integration test. Unit-test success does not establish live Drive isolation.

### Stage 6 — Documentation, Verification and Gate

Record implementation status, test results, decisions, limitations, and the exact conditions for opening CASE-001 to inventory.

Required records:
- adapter contract;
- implementation files;
- unit tests;
- integration test results;
- `DECISIONS.md` decision entry;
- `CURRENT_STATE.md` status update.

Stage 6 is complete only when the evidence is recorded without upgrading unexecuted or skipped tests into verified status.

## CASE-001 gate

The existing CASE-001 files must remain untouched during adapter development.

The first permitted live case-data operation is a metadata-only inventory of:

```text
CASE-001 -> exact registered Documents scope
```

only after:
1. Stages 1–4 are implemented;
2. Stage 5 unit tests pass;
3. live scope verification passes against isolated test folders or an equivalent faithful integration environment;
4. Stage 6 records the evidence.

## Security invariant

> No case-data access is permitted without a validated `case_id` resolved through the Case Registry to an exact storage scope.

## Explicit non-goals of this stage

- CASE-001 migration;
- PDF/content extraction;
- OCR;
- tax-rule research;
- final tax calculations;
- electronic filing;
- production multi-user authorization;
- durable storage migration.
