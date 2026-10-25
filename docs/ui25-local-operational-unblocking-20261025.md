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

Next safe package: inject this reader into the existing local product launcher
through an explicit, non-secret, read-only authorization configuration and test
restart/configuration failure behavior with synthetic registries.  Do not bind
real records until blockers 1 and 2 above are independently accepted.
