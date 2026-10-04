# Official knowledge index

Status: **implementation proof v1**

`contracts/official-knowledge-index-v1.json` is the canonical, versioned index of
bounded official semantics that have already been reviewed. It is not a copy of
the protected official material and it does not replace
`OfficialSourceResolver`. Normal consumers can resolve an exact verified entry
without opening the protected source.

Every consumable entry has a stable ID, `VERIFIED_ACCEPTED` status, an exact ERiC release and tax year,
the logical source identity and SHA-256 inherited from the index, a precise source
locator, and a canonical entry identity. Callers supply the required tax year,
release and source hash. The default index is always checked against the separate
trusted manifest pin. A custom path is rejected unless its trusted canonical hash
is explicitly supplied. Missing, wrong-scope, malformed, invalid-lifecycle and
canonical-drift states fail closed. `EXTRACTED_UNRESOLVED` entries such as DR-03 and DR-04
remain visible to comparison but cannot be resolved.

Failures expose a versioned `OfficialKnowledgeReopenAuditRecord` with the exact
semantic ID, year, release, source hash, locator, observed condition and smallest
required review scope. This is a diagnostic request only. Any actual exception-driven
inspection must produce `OfficialKnowledgeReopenCompletion` with the exact section
inspected, whether canonical knowledge was added/changed/unchanged, and a closed
PASS/FAIL acceptance result.

The comparison API classifies stable IDs as `UNCHANGED`, `CHANGED`, `NEW` or
`REMOVED` by canonical entry identity. Both indexes must first pass trust-pin and
structural validation.

The initial seed is intentionally limited to DR-01 through DR-04 E10/2024 extracts.
Only DR-01 and DR-02 are consumable; DR-03 and DR-04 remain unresolved. Adding or changing an entry requires a new bounded
official-source review, a version/identity update, focused tests and acceptance.
The index contains no taxpayer data and authorizes no ERiC execution or external
transmission. The Git-reviewed manifest plus committed checkpoint is the trust root;
the manifest alone is not an independent external authority.
