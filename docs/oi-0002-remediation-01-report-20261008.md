# OI-0002-REMEDIATION-01 implementation handoff

Instruction: `OI-0002-REMEDIATION-01`  
Starting implementation SHA: `90d44a8b0a40ad5a29ffa6d5d7d63db7c3caa10a`  
Preserved independent-review evidence commit: `afbb6be` (content from review commit `a3e2f5a12fc021eb524c361077a867d4132283e8`)  
Implementation code SHA: `ad30cee664b2ca002014adb0c9b3c46daca7ca82`  
Status: `REVIEW_READY`, never `ACCEPTED`

## Finding remediation

| Finding | Correction | Reproducible evidence |
|---|---|---|
| F01 | Permission decisions re-evaluate manifest expiry and terminate expired authority. | `test_kernel_adapter_expiry_denies_read_and_write`; revocation/Kill Switch test |
| F02 | Removed public raw save/load/restore APIs; identity lifecycle is case-scoped, Kernel-authorized and audited. | `test_raw_identity_bypass_api_removed`; default-deny lifecycle test |
| F03 | Versioned envelope persists and re-verifies subject, semantic key, full fact payload, declaration, confirmation, authorization, validity, revision and audit lineage. | T06, T07 |
| F04 | ACTIVE is required at identity, party and fact read/write boundaries and survives restart. | T05 |
| F05 | Exclusive family roles reject overlapping intervals across subjects; evidence references are canonical immutable hashes. | T02, T04 |
| F06 | HMAC protects rows; a chained HMAC audit log is bound to an independently protected sidecar anchor and checked on open/operation. | T10 deletion, reorder, rewrite, payload-plus-digest substitution probes |
| F07 | Schema v2 policy, transactional empty-v1 migration, fail-closed legacy-lineage boundary, crash injection, online backup/restore and synchronized-path rejection are implemented and documented. | T08, T10 backup, migration and deployment tests; operations guide |

## T01-T12 implementation evidence

| ID | Expected / observed evidence | Result | Remaining risk |
|---|---|---|---|
| T01 | Stable identities and digests survive idempotent replay/restart. | PASS | Independent reproduction pending. |
| T02 | Owner association remains strict; spouse follows an explicit role. | PASS | Real identities remain gated. |
| T03 | Half-open effective history and open-ended intervals survive restart. | PASS | Independent reproduction pending. |
| T04 | Same-case exclusive-role overlap across subjects rejects; adjacent intervals pass. | PASS | Policy expansion needs frozen-contract authority. |
| T05 | Unresolved, inactive and archived identities fail at all applicable boundaries, including restart. | PASS | Independent reproduction pending. |
| T06 | Confirmed fact binds with the complete reconstructable frozen envelope and unchanged original digest. | PASS | Protected repository integration remains downstream. |
| T07 | Wrong scope, subject, state, digest, confirmation, lineage and changed replay fail closed. | PASS | Independent reproduction pending. |
| T08 | Replay is idempotent; injected pre-commit failures roll back and post-commit interruption reopens consistently. | PASS | Platform-specific power-loss validation remains operational. |
| T09 | Exact case/year/run authorization and distinct storage roots isolate subjects. | PASS | Production ACL evidence remains a deployment gate. |
| T10 | Schema/corruption/lineage and audit tampering fail closed; backup plus anchor restores and verifies. | PASS | Key custody is an operational Human Gate. |
| T11 | Relevant and complete unit regressions pass without changing accepted real identities. | PASS | Final counts recorded below. |
| T12 | No real CASE-001 Person A/B bootstrap or private values were created. | PASS | Real bootstrap remains HUMAN_REQUIRED. |

These are implementation-worker results, not independent acceptance.

## Verification

- Syntax compilation: PASS, exit 0.
- Focused persistence and Kernel suite: `python -m pytest tests/unit/test_identity_persistence.py tests/unit/test_orchestrator_kernel.py -q` — 50 passed, exit 0.
- Relevant persistence/Kernel/registry/fact regression: `python -m pytest tests/unit/test_identity_persistence.py tests/unit/test_orchestrator_kernel.py tests/unit/test_person_entity_registry.py tests/unit/test_case_identity_association.py tests/unit/test_human_declared_fact.py tests/unit/test_durable_approval.py tests/unit/test_case_registry.py -q` — 102 passed, exit 0.
- Original adversarial classes (expiry, raw API bypass, overlapping spouse, non-active read, audit tamper): 9 passed, exit 0.
- T01-T10 and T12 were each invoked separately by exact test selector: 18 parameterized checks passed, exit 0. T11 is the complete regression below.
- Complete unit regression: `$env:PYTHONPATH='src'; python -m pytest tests/unit -q` — 1084 passed, 5 skipped in 238.32 seconds, exit 0.
- Documentation/governance regression: `$env:PYTHONPATH='src'; python -m pytest tests/unit/test_documentation_index.py tests/unit/test_orchestrator_pilot.py -q` — 15 passed, exit 0.
- One preliminary full-suite command without `PYTHONPATH=src` failed collection with 82 import errors and exit 1; no tests executed. The corrected project-contract command above is the authoritative full regression.

## Residual risks and Human Gates

- A separate independent reviewer must inspect the exact final branch SHA; this worker does not approve its own implementation.
- Runtime operators must provision a protected HMAC key, local non-synchronized storage and verified ACLs. Those production controls are not secrets or fixtures in Git.
- Nonempty v1 fact stores lack the lineage needed for safe automatic migration and deliberately require a reviewed evidence-backed migration/Human Gate.
- Real CASE-001 identity resolution/bootstrap remains `HUMAN_REQUIRED`; OI-0003 and later stages remain blocked.
- No frozen contract changed. Any role-policy expansion, production activation, merge or release requires its existing authority and gates.

## Required next action

Conduct a new independent, read-only security and T01-T12 acceptance review of the exact published remediation head. Keep OI-0002 OPEN unless that review passes; do not begin OI-0003.
