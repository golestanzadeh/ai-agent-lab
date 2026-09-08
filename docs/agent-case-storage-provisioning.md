# Agent-Authorized Case Storage Provisioning

## Status

Accepted governance clarification for D-021 implementation.

## Purpose

Case storage provisioning is a normal agent operation when it executes the already accepted Case Creation and Case Model contracts. It is not, by itself, a new architecture decision or a physical document migration.

The system is intended to operate as an agentic multi-case platform. A human is not required to approve the creation of each standard case folder or each required standard subfolder when the operation is fully determined by an already accepted case-creation contract.

## Authorized standard operation

After deterministic validation of case identity, owner, tax period, idempotency, and storage root, an authorized agent may create the standard case storage structure required by the accepted architecture:

```text
AI-Tax-Agent/
└── Tax_Years/
    └── <tax year>/
        └── Cases/
            └── <case_id>/
                ├── Documents/
                ├── Evidence/
                ├── Tax_Categories/
                ├── Calculations/
                ├── Reports/
                └── Audit/
```

This authority includes creating missing standard parent folders when their identity and placement are deterministic under the configured system root and accepted storage contract.

## Required persistence

The agent must capture provider object IDs/references returned by storage creation and persist the authoritative storage references through the project's registry/state/configuration boundary. Later operations must resolve those references from the authoritative stored state rather than rediscovering case folders through broad Drive searches or guessing by folder name.

Private provider object IDs, OAuth credentials, tokens, source-document contents, and other private runtime values must not be committed to GitHub. GitHub records the contract, code, schemas, tests, and non-sensitive verification state; private operational identifiers belong in the approved private/local or durable runtime store.

## Idempotency and recovery

Provisioning must be idempotent. Re-running an identical request must return/reuse the already established exact storage scope and must not create duplicate case trees.

Partial creation must be detectable. The implementation must either safely resume the known partial operation or fail closed with sufficient audit evidence. It must not use a broad Drive search to guess which folder belongs to a case.

## Agent authority

Within this accepted contract, an agent does not require a fresh human approval merely to:

- create the standard case root and required standard subfolders;
- retain their exact returned storage references;
- initialize/update the corresponding authorized Case Registry/state records;
- emit required audit evidence;
- reuse those references in later case-scoped workflows.

These are execution actions inside previously accepted architecture.

## Human-authority boundaries

Fresh human authority remains required for material changes to architecture or contracts and for consequential operations that have their own approval requirements.

In particular, this provisioning authority does not authorize:

- moving, copying, renaming, deleting, overwriting, or otherwise migrating existing source documents;
- consuming a D-017 physical-migration approval;
- destructive cleanup of ambiguous or unrelated Drive objects;
- changing the standard case structure or storage architecture;
- bypassing case isolation, provenance, audit, or approval controls.

## CASE-001 transition

CASE-001 currently has a legacy source Documents scope containing the real source documents, while its target standard case tree has not yet been physically provisioned.

For CASE-001, D-021 may provision the empty target case structure under the accepted 2024 case hierarchy, capture the exact target storage references, and then use the target `Documents` reference for manifest construction and read-only Live Target Preflight.

Provisioning the empty target structure is not the CASE-001 document migration. Existing CASE-001 source documents must remain untouched until the separate D-017 physical-migration approval and execution boundaries are satisfied.

## Expected D-021 flow

```text
validated CASE-001 legacy source
        ↓
provision standard empty CASE-001 target tree
        ↓
persist exact target storage references
        ↓
generate exact real migration manifest
        ↓
read-only Live Target Preflight
        ↓
D-020 approval-context composition
        ↓
prepare reviewed D-017 approval evidence
        ↓
STOP before approval consumption / physical migration
```

## D-021 implementation and live evidence

`GoogleDriveStorageScopeCreator` in `src/agent_lab/google_drive_provisioning.py`
implements the existing `create_case_scope(tax_period, case_id)` contract.
It creates only standard folders under an explicitly configured system root.
Root identity is loaded privately from `AI_TAX_AGENT_DRIVE_ROOT_ID`; it is not
discovered by name. The existing metadata-read and drive.file scopes sufficed
for the authorized live execution; no OAuth changes were made in this work.

One canonical private local reference journal must be used per system root,
with one local execution owner. The CASE-001 execution uses ignored
`artifacts/case001/provisioning.json`. Atomic local replacement records exact
returned IDs, case/year bindings, create intents, completion events and unresolved
operations. An exclusive local lock prevents concurrent use of that journal.
Known completed folders are verified by exact ID, parent, name, MIME type and
trash state on replay. Only missing known steps may resume. An uncertain create,
crash lock, changed root, mismatched year, or unrecorded conflicting folder fails
closed. An exact-name/exact-parent query is only a conflict check; it never adopts
unrecorded folders. No cross-case document listing or broad Drive search exists.

This is private provisioning configuration/recovery evidence, not a replacement
Case Registry, durable AuditStore, or distributed transaction system. Do not use
multiple journals or hosts to provision the same root concurrently. Journal loss
does not authorize guessing or recreating an existing tree. No destructive
compensation or automatic deletion is implemented. Provisioning events are
retained in the private journal and the CASE-001 harness forwards them through
the existing case/run-scoped AuditStore. Generic CaseCreationWorkflow retains its
existing responsibility for validating owner/request identity and registering the
returned case-root reference. The CASE-001 harness validates the existing registry
and source snapshot without replacing the legacy source scope with the target.

`scripts/case001_prepare_approval.py` connects the existing inventory, identity,
Manifest, Live Target Preflight, D-020 composition and D-017 create_pending APIs.
It requires the exact source and system-root configuration, validates the known
15-document source population, and stores exact real artifacts and audit records
in a private review export. It neither grants nor consumes approval. The export
does not add restart support to ApprovalStore and is not executable authorization.

Live execution created the required 10 folders (four hierarchy folders and six
standard subfolders). The target Documents folder was empty; real manifest count
was 15. D-020 composed a successful context and D-017 created PENDING evidence.
No source document or permission was modified; no migration occurred.

Safe exact artifact references:
- Manifest, `CASE001_MIGRATION_MANIFEST`, version `1`:
  `sha256:94b563afc299a1c3da3b5e57ab6deb023952e15ae8e6abb274223f5d72b85587`
- Preflight, `CASE001_MIGRATION_PREFLIGHT`, version `1`:
  `sha256:16d9b1bd5ed8fb08d5cac0aa22a00333fa2d2c783da7fa38899efad747379853`

Tests with project-local Python and `PYTHONPATH=src`:
- `-m pytest -q tests/unit/test_google_drive_provisioning.py tests/unit/test_case001_prepare_approval.py tests/unit/test_case_creation_workflow.py tests/unit/test_approval.py tests/unit/test_case001_approval_context.py`: **103 passed**.
- `-m pytest -q`: **241 passed, 1 skipped**.

The next boundary is human review with explicit approver identity and authorization
reference. Approval grant/consumption and main integration have not been performed.

## Required verification coverage

Implementation must demonstrate with tests and, where explicitly authorized, narrowly scoped live verification that:

- provisioning creates only the accepted standard structure;
- returned IDs/references are captured rather than guessed;
- repeated execution is idempotent;
- partial/ambiguous state fails closed or follows an explicit safe recovery path;
- no broad Drive search is introduced;
- case isolation remains enforced;
- private Drive IDs are not committed;
- CASE-001 source documents are not mutated;
- provisioning does not grant or consume migration approval;
- physical migration does not occur during D-021.
