# UI package 5 — synthetic document intake and provenance

Package 5 adds a metadata-only document inventory to the local prototype while
ELSTER developer access is pending. Every item binds to the selected synthetic
case/run and carries only an immutable document reference, a distinct provenance
reference, a generic synthetic label, allowlisted category/type, and processing
status.

Private filenames and contents cannot enter the contract. Cross-case items,
duplicate or malformed references, real-data classification, uploads, persistence,
source access, and networking fail closed. The Persian UI renders the inventory as
a responsive table and explicitly labels real upload/content viewing as disabled.

Real file intake, Drive access, persistence, authentication, protected ERiC access,
external connectivity, production deployment, and transmission remain separate
governed gates.

Verification completed with UI targeted `24 passed`, full regression
`529 passed, 1 skipped`, Python compile success, and loopback visual inspection.
The known upstream TestClient deprecation warning remains recorded.
