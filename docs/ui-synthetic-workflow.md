# UI package 4 — synthetic workflow and operational status

Package 4 continues the local UI while ELSTER reviews the developer-account
application. It adds an immutable workflow contract and responsive rendering without
accessing the pending account or any external source.

The exact ordered stages cover case scope, document intake, processing, specialist
and Chief review, calculation, form preview, Human approval, submission, and receipt.
Exactly one stage is active or blocked; earlier stages are complete and later stages
are locked. The workflow binds to one synthetic case/run already validated by the
UI state contract.

Diagnostics use a closed allowlist of privacy-safe codes. Private contents,
credentials, prompts, and arbitrary error text cannot enter the view. Operational
controls, submission, real-data classification, and networking remain disabled.

The Persian RTL workspace includes a responsive timeline and collapsible local
technical/recovery panel. Case switching replaces the whole scoped fragment so no
prior-case stage remains visible.

Persistence, authentication, real documents, Drive, protected ERiC access, external
connectivity, production deployment, and submission remain separate gates.

Verification completed with UI targeted `19 passed`, full regression
`524 passed, 1 skipped`, Python compile success, and loopback visual inspection.
The existing upstream Starlette TestClient deprecation warning remains recorded.
