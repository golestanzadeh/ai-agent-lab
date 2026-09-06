# Case-Scoped Drive Resolver and Access Boundary

## Status

Foundational contract and deterministic runtime boundary.

## Purpose

The Case-Scoped Drive Resolver converts a validated `case_id` into the exact storage scope recorded in the Case Registry. It is the mandatory boundary between case identity and Google Drive access.

The resolver does not discover cases by scanning Drive, does not infer ownership from filenames, and does not authorize access to unrelated cases.

## Security invariant

> No case-data access is permitted without a validated `case_id` resolved through the Case Registry.

A storage reference is routing information, not case identity. `case_id` remains authoritative.

## Resolution flow

```text
request
  ↓
validated case_id
  ↓
Case Registry
  ↓
CaseRecord
  ↓
exact StorageScopeReference
  ↓
case-scoped Drive access
```

The resolver must fail closed when:

- `case_id` is empty or malformed;
- the case does not exist;
- the registry lookup is unresolved;
- the storage scope is missing or invalid;
- a requested object is outside the case scope.

## Allowed operations

The future Drive adapter may expose only case-scoped operations, conceptually:

```text
list_documents(case_id)
get_document(case_id, document_id)
get_case_child(case_id, child_id)
```

The resolver may internally use the exact root reference from the Case Registry. It must never replace that reference with a broad Drive search.

## Prohibited operations

The case-scoped boundary must not expose generic case-data access such as:

```text
list_all_tax_documents()
search_drive_for_taxpayer_name()
list_documents_without_case_id()
resolve_case_by_drive_scan()
```

Prompts, Agent instructions, and naming conventions are not security controls. Enforcement belongs in deterministic application/connector code.

## Descendant containment

For Drive-backed implementations, a resolved case root defines the permitted descendant scope. A requested Drive object must be demonstrably within that scope before content or metadata is returned.

Parent traversal, sibling access, unrelated case roots, and arbitrary Drive IDs must be rejected unless a separate explicitly authorized operation exists.

## Storage provider abstraction

The resolver depends on the provider-neutral `StorageScopeReference` already held by the Case Registry. The Google Drive adapter is a later implementation detail.

This keeps case identity independent from Google Drive and permits future storage migration without changing `case_id`.

## CASE-001

The resolver must not migrate, rename, or restructure the existing CASE-001 layout. CASE-001 becomes accessible through this boundary only after its exact storage scope is registered or a separate migration/compatibility workflow establishes that mapping.

## Audit

Every resolved case access should be attributable to at least:

- `case_id`;
- operation;
- resolved storage scope;
- run/request identity when available;
- outcome.

The resolver must not log unnecessary document contents or credentials.

## Acceptance criteria

The deterministic runtime is accepted when tests demonstrate:

- valid `case_id` resolves only to its registered storage scope;
- unknown cases fail closed;
- empty/invalid scope references fail closed;
- storage scope cannot be selected independently of the Case Registry;
- two cases cannot resolve to the same registered storage root under current registry invariants;
- changing a case's storage reference does not change `case_id`;
- no broad Drive search is required for resolution;
- access to a different case is rejected;
- the resolver contains no document-content processing logic;
- CASE-001 remains untouched.
