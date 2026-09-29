# Milestone A Synthetic Actions

Status: **MA-03 IMPLEMENTED / INDEPENDENTLY ACCEPTED**  
Authority: `MILESTONE-A-20260927-001`

`SyntheticWorkflowActionService` is the sole MA-03 action adapter. It accepts six enum-valued local actions from `INTAKE` through `FORM_PREVIEW`, requires the exact assigned enum role and prior transition hash, derives the next artifact identity from canonical lineage, and delegates persistence to the MA-02 composition/store boundary.

Correction evidence is permitted only at specialist or chief review. Invalidated artifact identities are disjoint from active inputs and are cryptographically bound into the new lineage. The adapter does not evaluate free-form text, invoke a shell, call a provider, access real data, execute ERiC, or transmit anything.

Recovery reserves every transition attempt durably before validation. A rejected attempt consumes its identity; an exact accepted replay returns the durable result; changed reuse, stale state, wrong sequence, wrong role, corrupt state, or cross-case scope fails closed. The canonical request journal preserves input and invalidation lineage and is hash-verified on reopen.

Verification: focused MA-02/MA-03 `16 passed`; full unit regression `892 passed, 1 warning`; independent acceptance `PASS`. Kernel checkpoint `sha256:c90bbe7a41bf1ade4e491c4abdec8ac11473da2f782ef7e9b7f759a5434dd2d3` selects `PKG-MA-04-APPROVAL-SUBMISSION-RECEIPT` next.
