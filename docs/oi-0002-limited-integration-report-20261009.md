# OI-0002 limited Kernel/evidence integration report

Date: 2026-10-09  
Authorization: OI-0002 Limited Implementation & Synthetic Verification  
Baseline: `a34ba46cc9f81422165467bdb08000b6b92e9258`  
Status: `SYNTHETIC_IMPLEMENTATION_COMPLETE / INDEPENDENT_REVIEW_REQUIRED / NOT_RELEASED`

## Delivered packages

1. `ae3b09dfb43961c7692131def26aec9b7b4686a9`: actual Deterministic Orchestrator Kernel owns versioned identity continuity state. Exact deployment/case/year/task/manifest/run/operation context, PENDING reservation, identity-commit finalization, restart verification, exact pending reconciliation and old epoch/head rejection are enforced.
2. `b3629734fc23fc31820b5296d332a0150f6e3404`: durable metadata-only Owner declaration → confirmation → identity authorization chain with exact scope/revision/provider binding, protected-byte digest verification through an injected case-scoped loader, expiry, revocation, one-time consumption and HMAC row/audit integrity. Identity persistence requires resolver verification for party/fact bind and restart readback. Synthetic custody plans require distinct principals, roots, backups and nonliteral key references.
3. `c0471723ebb9b7139183e5efd3abb8cfb078ffc5`: exact expiring one-time governed restore authorization and concurrent authorization-consumption proof.

No parallel orchestrator/database/scheduler, real taxpayer/identity data, real account/ACL/key/backup mutation, production activation, merge, ELSTER or external protected-data transfer occurred.

## Security evidence

- Old identity epoch/head against newer Kernel state rejects, including after restart.
- Pending state fails closed; only an exact committed identity epoch/head reconciles.
- Wrong case/task/manifest scope denies continuity reservation.
- Protected content bytes must hash to the declared immutable identity; metadata-only hashes fail when bytes differ or are unavailable.
- Cross-case/year/subject/semantic-key/revision mismatch, missing parent, expiry, revocation, consumption, wrong HMAC key and row/audit tampering fail closed.
- Governed restore requires an explicit Owner reference and exact deployment/backup/current-state/generation/operator binding; mismatch and replay deny.
- Two concurrent consumers of one authorization yield one success and one denial.
- Synthetic custody validation rejects shared service/recovery principals, nested custody roots and literal key material.

## Verification

- Package 1 continuity/Kernel: `29 passed`, exit 0.
- Package 2 evidence/custody/persistence: `36 passed`, exit 0.
- Integrated security set: `15 passed`, exit 0.
- Relevant Kernel/identity/registry/approval regression: `115 passed`, exit 0.
- First complete unit run: `1098 passed, 5 skipped, 1 failed`; only the documentation index identified three existing unregistered OI-0002 documents. No product/security test failed.
- Documentation/governance regression after index repair: `15 passed`, exit 0.
- Corrected complete unit regression: `1099 passed, 5 skipped` in 238.83 seconds, exit 0.

## Conditional-gate disposition

This worker does not declare E-03, C-02 or C-06 PASS. Synthetic implementation evidence is ready for a separate independent review, but production custody remains unverified: real service principals, ACLs, key provider/custodians, independent backup roots and recovery rehearsal were intentionally untouched. The Owner must explicitly release every conditional gate after independent evidence review.

OI-0002 remains OPEN. `REMEDIATION-02`, production activation and OI-0003 remain BLOCKED.

## Exact next step

Conduct a separate independent read-only security/acceptance review of the exact final branch SHA, reproducing rollback, crash, evidence substitution, authorization lifecycle, concurrency, tamper and custody-boundary tests. Return defects for bounded correction; only the Owner may subsequently release E-03/C-02/C-06.

## Capacity handoff

- Authenticated ending observation at `2026-10-09T19:52:51Z`: five-hour 58% remaining, reset `2026-10-10T00:35:43Z`; weekly 56% remaining, reset `2026-10-14T16:57:07Z`.
- Source: signed-in Codex rate-limit service. No reset credit was used; the mandatory reserve was preserved.
