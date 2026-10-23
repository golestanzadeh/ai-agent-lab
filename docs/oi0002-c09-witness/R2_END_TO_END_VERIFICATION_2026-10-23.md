# C09 R2 governed end-to-end verification

Status: `MATRIX_FROZEN / EXECUTION_PENDING / SYNTHETIC_ONLY`.

Baseline: R1 independently accepted at `bd656b7c03a8d20e6c12062b7a599a95fd471aed`; checkpoint baseline `9f6849265ace459b79dbdf4b0edd1fb5f6845c10`; architecture `2c664800d8a3ace7cf0995c838a46d46c6a57191`.

R2 does not reopen the accepted architecture, grant a capability, activate IPC, change IAM/key custody/retention, or use protected data. Each row is an isolated synthetic transaction package. PASS requires the stated deterministic outcome and durable evidence; provider or authority uncertainty fails closed.

| ID | Initial state | Injected failure/adversarial action | Required deterministic outcome and recovery evidence | Security contract |
| --- | --- | --- | --- | --- |
| R2-T01 | Initialized Kernel/Identity continuity, active exact-scope manifest | Execute full transaction and request acknowledgment before/after finality; attempt invalid transition | Kernel PENDING precedes Identity mutation; receipt is durable before Witness I/O; verified Witness precedes Kernel COMMITTED and acknowledgment; early acknowledgment denied | C03, C04, C06, C10 |
| R2-T02 | One new transaction per boundary | Terminate after PREPARED, PENDING, IDENTITY_COMMITTED, WITNESS_STAGED, WITNESSED and COMMITTED | Restart deterministically reaches one COMMITTED result; no duplicate Identity/Witness effect; no unverified acknowledgment | C06, C07, C08, C10 |
| R2-T03 | Two authorized requests share one predecessor; committed request available for replay | Concurrent start, exact replay, conflicting transaction/operation/payload and delayed replay | Exactly one successor wins; conflict/replay cannot produce a second successor; exact replay is idempotent | C03, C04, C07, C10 |
| R2-T04 | Staged or committed synthetic transaction | Provider unavailable before append, ambiguous post-create timeout, Reader outage, partial/multi-page listing, conflicting generation/token/version | No early acknowledgment; exact staged bytes reconcile once; complete enumeration required; service recovery is deterministic when provider returns | C06, C07, C09, C10 |
| R2-T05 | Committed chain and local snapshots | Alter receipt, Witness bytes/sequence/previous/head/generation; truncate/fork chain; restore both local stores behind external head | Every unauthorized mutation, gap, fork and coordinated rollback is rejected at startup/recovery; last verified state is preserved | C05, C06, C08, C09, C10, C13 |
| R2-T06 | Active exact-scope manifest with ordinary Identity capability | Cross-scope/forged capability; backup/restore request; inactive/expired/revoked authority | Default Deny; no protected mutation; backup/restore remain A4 Human-Gate/no-standing-permission and ungranted | C01, C02, C03, C11, C12 |

Live synthetic GCS is optional only when the already-approved resource and effective separated Reader/Writer identities can be verified without IAM/resource mutation. Mocked or same-principal evidence never proves Windows four-principal isolation. Any unavailable live dependency is recorded as a limitation and does not authorize infrastructure changes.

## R2-T03-A1 — concurrency harness FAIL

Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py -q`.
Result: **FAIL**, exit 1; `1 failed, 24 passed in 14.65s`.

Both threads returned COMMITTED because thread scheduling let the second read epoch 1 after the first committed; the test therefore created two valid sequential successors rather than two contenders for one predecessor. No Kernel concurrency failure or PASS is claimed. The bounded correction is a test-only barrier after both predecessor reads and before PREPARED insertion. Durable receipt-tamper and exact Witness-semantic tests in this run passed.

## Harness correction and R2-T01 — PASS

- Corrected complete transaction-state suite: `25 passed in 11.58s`, exit 0.
- `pytest --count=5` repeat attempt: exit 4 because the optional repeat plugin is absent; no tests ran and no PASS is claimed.
- Explicit loop of the same-predecessor concurrency node: five consecutive PASS executions (`2.25s`, `0.85s`, `0.80s`, `0.72s`, `0.78s`).
- R2-T01 command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py -q -k "happy_path_is_durable or reader_failure_and_missing_credentials"`.
- R2-T01 result: **PASS**, exit 0; `2 passed, 23 deselected in 0.96s`.

Evidence proves the bounded happy path cannot acknowledge before verified Kernel finality and the pre-finality reader-failure path remains unacknowledgeable. R2-T02 is next.

