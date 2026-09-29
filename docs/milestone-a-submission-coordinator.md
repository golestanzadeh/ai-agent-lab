# Milestone A Durable Submission Coordinator

Status: **MA-04 IMPLEMENTED / INDEPENDENTLY ACCEPTED**
Authority: `MILESTONE-A-20260927-001` plus Owner architecture choice B on 2026-09-28

MA-04 adds coordinator contract version `1` to the existing `DurableApprovalStore`; it does not add a store or authority. The existing workflow store remains a separate SQLite commit domain. The composition service advances only the closed local synthetic stages from form preview through approval stage 1, approval stage 2, synthetic submission, placeholder receipt, and recovery.

The approval-store transaction persists the exact intent and later consumes both typed approvals while recording consumption ownership. It then records ordered markers after exact idempotent workflow transitions. The durable record integrity-binds case ID, tax year, run ID, operation ID, artifact/version, destination, channel, purpose, approval IDs, consumption state, result, and receipt. Case Registry/run resolution and tax-year matching are required before intent or approval persistence.

There is deliberately no atomic transaction across the approval and workflow databases. A crash after a workflow commit but before its coordinator marker is recovered by replaying the same transition identity; the workflow store returns the exact prior transition, after which the marker is written. A crash after a marker simply reloads and continues. Partial or foreign approval consumption, altered payloads, missing or inconsistent workflow state, out-of-order markers, and corruption fail closed.

Result and receipt schemas are closed and synthetic-only. They cannot contain network calls, credential access, or an external-receipt claim. Exact replay returns the single persisted result and receipt; a second operation cannot reuse the approvals.

Verification covers crash/restart/replay after the intent commit, approval-consumption commit, every workflow commit, and every marker commit, plus expiry, revocation, approval reuse, registered and unregistered cross-case isolation, corruption, result/receipt duplicate prevention, and complete replay. Focused verification passes with `32 passed`; the complete unit regression passes with `913 passed, 1 warning`; independent acceptance is `PASS`.
