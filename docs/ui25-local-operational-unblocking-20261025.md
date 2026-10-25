# UI25 local operational unblocking — 2026-10-25

Status: `TECHNICAL_PASS / NON_PRIVILEGED_READ_ONLY / SYNTHETIC_VERIFICATION`

## Decision boundary

`C09_NOT_ACCEPTED != PROJECT_EXECUTION_BLOCKED` remains binding under
`docs/decisions/c09-nonblocking-local-development-20261014.md`.  C09 is not a
prerequisite for UI, localization, navigation, or a read-only case-metadata
projection that does not rely on rollback-resistant finality.  This package
does not accept C09, OI-0002, protected persistence, or real taxpayer data.

Unsigned HG-01 development executables, incomplete GCS witness deployment, and
future cloud/VPS hardening do not block this package.  They remain evidence
gaps for the operational service profile recorded under OI-0002, not a reason
to stop unrelated local product development.

## Implemented slice

`CaseRegistryDashboardReader` connects the existing product Dashboard to the
existing `CaseRegistry` without another registry or persistence authority.  It
requires both an exact owner scope and a non-empty independent case allowlist.
Every allowlisted case must resolve inside that owner scope or the entire read
fails closed.  The projection exports only case ID, calendar tax year, and
canonical lifecycle status; it never exposes owner identity, storage roots,
documents, or facts.

The adapter supports multiple independent cases in the same tax year and cases
across every calendar year already supported by `TaxPeriod` (1900–9999).  The
Dashboard continues to sort by year and case ID.  Approval/Submission remains
inert and `/submit` remains absent.

## Critical path for protected local processing

The smallest currently evidenced blockers are:

1. **Accepted protected case identity and persistence boundary.** OI-0002 and
   OI-0003 remain active in `OPEN_ITEMS.md`.  The frozen C01–C13 matrix requires
   authenticated narrow IPC (C03), deterministic recovery (C07), authorized
   restore (C08), and rollback detection (C09) before protected mutations may
   rely on that operational profile.  OI-0003 separately remains
   `HUMAN_REQUIRED/SCHEMA_BLOCKED`; names may not substitute for authoritative
   identities.  Owner action: decide/accept only the still-open architecture or
   Human Gates identified by those items, followed by independent acceptance.
2. **Case-scoped protected document path and provider boundary.** UI25-04 and
   the UI25 security section require protected storage, exact case isolation,
   duplicate/version lineage, and provider privacy/retention verification
   before real documents may reach Google Drive or Gemini.  The existing Drive
   folders and Gemini code are reusable but are not themselves operational
   acceptance.  Owner action: approve an exact protected runtime binding only
   after its technical and independent evidence is complete; no repeated
   generic Gemini permission is required.
3. **External release and submission approvals.** `contracts/orchestrator/v2/
   human-gates.json` requires separate exact content-release and destination-
   transmission approvals and prohibits combining them.  These gates apply to
   export/ELSTER, not to the present read-only UI package.  Owner action: issue
   the two exact approvals only when a final immutable artifact and destination
   exist.  Approval and Submission stay disabled until then.

No new Owner decision is needed for further synthetic fixtures, bilingual UI,
read-only projections, or other non-privileged integrations that do not touch
protected persistence.  A new external connector, privileged host/cloud
mutation, protected runtime activation, architecture change, or submission
still stops at its exact Human Gate.

## Verification

Focused command:

`PYTHONPATH=src python -m pytest tests/unit/test_ui_case_registry_reader.py tests/unit/test_ui_dashboard.py tests/unit/test_case_registry.py -q`

Result: `33 passed`.  Evidence includes same-year multi-case display,
multi-year display, cross-owner denial, allowlist denial, unknown-case denial,
fail-closed unresolved scope, bilingual Dashboard regression, and absent
submission route.  Only synthetic records were used; no Drive, Gemini, Kernel
execution, network, protected storage, or external action occurred.

## Continuation

The local product launcher now starts `agent_lab.ui_product_app:app`, not the
legacy synthetic application.  Its composition root accepts the existing
`CaseRegistry`, exact owner scope and case allowlist only as one complete unit;
partial configuration stops startup.  With no accepted source it starts a
truthful empty Dashboard and exposes no TEST mutation surface.  Re-composition
after restart preserves exact scope when the same authoritative registry is
injected and fails closed when an authorized case disappears.

The same composition root can accept the existing read-only Kernel projection.
It calls that projection only with the selected authorized case ID, that
record's exact tax year, and the explicitly entered run ID.  It adds no task
dispatch or mutation capability.

Focused launcher/registry/Dashboard/Kernel verification now passes `69` tests.
A real Uvicorn loopback smoke returned HTTP 200 with
`read-only-dashboard/source=unavailable`, rejected `POST /test/cases` with 404,
and shut down cleanly.

### Exact remaining code prerequisites

1. Implement an accepted durable provider that reconstructs the existing
   `CaseRegistry` and exact UI authorization after restart.  Current
   `CaseRegistry` and `CaseStateStore` are in-memory; the functional-test SQLite
   store and PostgreSQL PoC must not be promoted.
2. Route case creation through the existing `CaseCreationWorkflow` only after
   that provider can commit the case, owner association, audit and storage
   reference atomically/recoverably.  The current workflow is component code,
   not a durable operational transaction.
3. After OI-0002/OI-0003 acceptance, compose the existing
   `GoogleDriveStorageScopeCreator`, case-scoped Drive adapter, document identity
   store, `GeminiDocumentExtractor`, and `ingest_sparkasse_csv` behind that exact
   case/year boundary.  These components already exist; the missing work is the
   accepted protected transaction and result persistence, not another provider
   or UI database.

### Exact Owner/Human Gate actions

1. OI-0002: approve only privileged deployment actions that remain after the
   code/security re-review, then obtain independent C01–C13 PASS.  Unsigned
   development executables do not block the current launcher, but must never be
   installed as operational services.
2. OI-0003: authorize/accept durable Person A/Person B identity resolution,
   CASE-001 role association, and the already-designed subject-bound fact
   envelope.  The historical stop at `f9a4b99` forbids name-based inference.
3. Protected Drive/Gemini activation: approve the exact runtime binding after
   privacy/retention, credential custody and case-isolation evidence; the prior
   generic Gemini authorization need not be repeated.
4. Keep content release and ELSTER destination approval separate until an
   immutable final artifact exists.

Next safe code package is the durable CaseRegistry provider contract and
recovery tests inside the approved persistence architecture.  It must not create
a UI-owned store or bind real records before OI-0002/OI-0003 acceptance.

## Durable case provider implementation candidate

`SQLiteCasePersistence` now implements the frozen one-database local pattern
for case metadata, `CaseState`, and exact UI case authorization.  It uses WAL,
foreign keys, schema versioning, transactional case/state/authorization/audit
registration, a protected runtime HMAC key, canonical row digests and an HMAC
audit chain.  It rejects synchronized-folder placement, unversioned/unsupported
databases, wrong keys, altered rows, deleted state, cross-owner authorization,
incomplete allowlists and reused case identities with changed content.

The provider preserves multiple independent case IDs for one owner/year and
multiple years.  After close/reopen it reconstructs the existing
`CaseRegistry`, returns exact durable `CaseState` values, and supplies the
allowlist consumed by the existing product composition root.  It stores no
document bodies, identity facts, Gemini output or bank data and is not a new
Kernel/Identity authority.

Focused provider/UI/registry/state/launcher verification passes `65`.  This is
an implementation candidate requiring independent persistence/security review;
it is not OI-0002 acceptance or authorization for protected records.

Independent review of `dd831b7` returned FAIL: coordinated deletion and valid-
prefix rollback were accepted, an empty database was not key-bound, and durable
CaseState/run mutation was absent.  The first two findings are remediated with a
separately protected HMAC anchor binding the key verifier, schema, case count and
audit event count/head; focused remediation tests pass `17`.  The third finding
remains outside the accepted read-only scope and prevents operational-persistence
acceptance pending a separate mutation/recovery implementation and re-review.

The remaining code boundary is operational transaction composition: case
creation must commit this provider together with accepted identity association,
audit and Drive scope semantics without partial side effects.  Existing Drive,
Gemini and CSV components should then be injected behind the same exact
case/year authorization.  That composition cannot safely precede OI-0003's
authoritative Person A/Person B mapping and subject-fact decision.
