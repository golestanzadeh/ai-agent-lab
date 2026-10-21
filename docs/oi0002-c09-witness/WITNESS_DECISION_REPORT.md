# OI-0002/C09 witness decision report

Date: 2026-10-21  
Status: `DESIGN_AND_LOCAL_PROOF_COMPLETE / C09_OPEN / OWNER_DECISION_REQUIRED`

## Result

The isolated simulator demonstrates coordinated/local rollback detection, crash recovery, replay/fork/gap rejection, one-time restore authorization and object-version/delete-marker rejection across AT-C09-01..15. Result: `LOCAL_SIMULATION_PASS` (`15 passed`). It does not touch the operational Kernel↔Identity path, network, credentials or taxpayer data.

Global-head correctness is **conditionally specified, not operationally established**. A fixed sequence key plus provider conditional-create selects one successor per position under the provider's documented consistency model. The guarantee still depends on retention/policy enforcement, complete version inspection, independent authentication-key custody and provider/account trust. No live cloud behavior or administrative isolation was tested.

## Recommendation

Prefer a bounded GCS Frankfurt live-test profile over S3 for the next architecture review because its generation precondition, global listing consistency and absence of S3 delete markers reduce protocol complexity. Do not deploy yet. The Owner must approve the provider/trust/cost profile, retention horizon, independent key/administrator custody and a limited live adversarial test budget. An independent architecture/security review must then accept the revised ADR before operational code.

## Effort estimate

- revised ADR and independent review: 2–4 engineering days;
- provider sandbox policy/configuration verifier and live negative campaign: 3–6 days;
- operational adapter, durable staged receipt and recovery integration: 5–10 days;
- four-principal regression, restore campaign and independent acceptance: 4–8 days.

Total estimate: 14–28 engineering days, excluding Owner/provider-account lead time and remediation cycles.

## Required Owner decisions

1. Approve or reject GCS Frankfurt as the candidate witness provider (AWS remains alternate).
2. Approve the threat model, especially cloud-admin/provider compromise exclusions and fail-closed availability impact.
3. Select retention horizon and accept irreversible-retention/cost consequences.
4. Select independent signer/Owner restore-key custody and administrator separation.
5. Authorize a capped, synthetic-only live provider test and billing ceiling.

Until those decisions and independent ADR PASS, `C09` and OI-0002 remain OPEN; protected persistence and operational IPC remain blocked.
