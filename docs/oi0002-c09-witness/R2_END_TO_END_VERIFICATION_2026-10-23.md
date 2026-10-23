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

## R2-T02 — PASS

Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py::test_r1_i04_process_termination_at_every_boundary_recovers_exactly_once -q`.
Result: **PASS**, exit 0; `6 passed in 3.19s`.

Every durable boundary—PREPARED, PENDING, IDENTITY_COMMITTED, WITNESS_STAGED, WITNESSED and COMMITTED—survived close/reopen and deterministically reached exactly one committed Witness before acknowledgment. R2-T03 is next.

## R2-T03 — PASS

Command: concurrency, replay/conflict and failed-reservation nodes from `test_c09_transaction_state.py`.
Result: **PASS**, exit 0; `3 passed in 2.29s`.

The deterministic same-predecessor race produced one COMMITTED successor and one denied contender. Exact replay was idempotent; conflicting transaction, operation or payload identity was rejected; and reservation failure left epoch zero with no Witness. R2-T04 is next.

## R2-T04 — PASS / live dependency unavailable

Command: timeout, Reader outage, pre-append staging, incomplete enumeration nodes plus complete `test_c09_gcs_witness_adapter.py`.
Result: **PASS**, exit 0; `15 passed in 4.48s`.

Ambiguous conditional-create completion reconciled the exact staged bytes once; Writer/Reader outage and incomplete enumeration denied acknowledgment; pagination, repeated/invalid token, duplicate generation and deletion ambiguity remained fail closed. A read-only host check returned `GCLOUD_UNAVAILABLE`; therefore no live GCS test ran and no actual cloud or Windows-principal isolation claim is made. No cloud resource, IAM, key, service or evidence changed. R2-T05 is next.

## R2-T05 — PASS

Command: selected receipt/Witness tamper, truncation, coordinated rollback and protocol-chain nodes.
Result: **PASS**, exit 0; `11 passed, 17 deselected in 4.56s`.

Startup rejected altered canonical receipt JSON/digest, missing/rewritten/wrong-generation Witness, a validly signed but transaction-inconsistent backup generation, local chain truncation and rollback behind one or two external successors. Gap, fork and ordering protocol checks remained fail closed. R2-T06 is next.

## R2-T06 — PASS

Command: selected default-deny, exact continuity scope, unauthorized initialization, governed-restore gate, declared-capability, case-scope and Kill Switch nodes.
Result: **PASS**, exit 0; `7 passed in 2.72s`.

Exact case/task/manifest/run scope and active Kernel authority remain mandatory. Forged or undeclared capabilities and unauthorized initialization fail closed. `identity_backup` and `identity_restore` remain A4 Human-Gate/no-standing-permission and are hard-denied by the bounded transaction implementation. R2-T01–T06 are technically green; regression and independent acceptance remain mandatory.

## R2 regression and candidate freeze

- Focused transaction/GCS suite: **PASS**, `36 passed in 11.25s`, exit 0.
- Relevant C09 transaction/protocol/simulator/GCS, Identity continuity/custody/evidence/persistence, IPC wire/envelope/response and Kernel suite: **PASS**, `358 passed in 30.66s`, exit 0.
- Complete unit suite with skip reasons: **PASS**, `1481 passed, 5 skipped in 314.15s`, exit 0.

The five skips are existing DR03 protected-source/registration exclusions at `test_case_declaration_dr03.py` lines 45, 60, 68, 76 and 86; none concerns R2, C09, Kernel, Identity, Witness, GCS, IPC or permissions. Local status is `R2_TECHNICAL_PASS / SYNTHETIC_ONLY / INDEPENDENT_ACCEPTANCE_PENDING`. Live GCS and real Windows-principal separation remain explicitly unproven.

## Independent R2 review 01 — FAIL

Reviewed SHA: `a2d28ff3be93ac7db8193e0f00177388b064ed66`.
Reviewer: `/root/c09_r1_implementation_independent_review`, separate read-only context.
Decision: **`INDEPENDENT_R2_FAIL`**.

Independent focused verification passed `36 passed in 12.79s`; relevant verification passed `363 passed in 38.06s`. The reviewer then reproduced **R2-F01 HIGH**: modifying local `payload_digest` and regenerating internally consistent receipt JSON/digest was accepted after restart while the original `next_head`, Witness and Kernel finality remained unchanged. Receipt validation reconstructed expectations from the same mutable row but did not verify the defining head derivation.

Required correction is an independent invariant check that stored `next_head` exactly equals `_next_head(expected_head, transaction_id, payload_digest)`, plus payload-digest, transaction-id and combined row/receipt substitution tests. Full regression and a new exact-SHA independent review are mandatory. Live GCS and four-principal coverage remain unavailable/unproven.

## R2-F01 remediation candidate

The startup validator now independently derives the expected successor head from `expected_head`, `transaction_id` and `payload_digest` before validating receipt bytes/digest. It therefore does not accept a self-consistent receipt rebuilt from a substituted mutable row. New adversarial tests cover payload-only, transaction-only and combined row substitutions with regenerated canonical receipt JSON and digest; every case fails closed during restart.

- Focused transaction suite: **PASS**, `28 passed in 23.67s`, exit 0.
- Relevant C09/Identity/IPC/Kernel regression: **PASS**, `361 passed in 34.37s`, exit 0.
- Complete unit suite: **PASS**, `1484 passed, 5 skipped in 308.45s`, exit 0.
- Documentation suite: **PASS**, `18 passed in 0.77s`, exit 0. An earlier command naming nonexistent `tests/unit/test_documentation_consistency.py` exited 4 and received no credit.

The five skips are the unchanged DR03 protected-source/registration exclusions and do not cover R2. Current status is **`R2_F01_REMEDIATED / SYNTHETIC_ONLY / INDEPENDENT_RE_REVIEW_PENDING`**. Live GCS and real four-principal isolation remain unproven. C09/OI-0002 remain open; no privileged grant is made and R3/R4 are not started.

## Independent R2 re-review — PASS

Reviewed SHA: `a159373c768c52197e2c1647259e855a82e38f91`.
Reviewer: `/root/c09_r1_implementation_independent_review`, separate read-only context.
Decision: **`INDEPENDENT_R2_PASS / SYNTHETIC_ONLY`**.

The reviewer independently regenerated canonical receipt JSON/digest after payload-only, transaction-only and combined transaction-row substitutions. All three probes were rejected with `C09TransactionError: durable transaction head derivation is invalid`. Independent focused transaction/GCS verification passed `39 passed in 12.28s`, and relevant C09/GCS/Identity/IPC/Kernel regression passed `366 passed in 34.45s`, both exit 0. Inspection found no residual in-scope T01–T06 defect. The reviewer relied on the exact-candidate full-suite evidence (`1484 passed, 5 skipped`) rather than repeating the five-minute suite; the five skips are unrelated DR03 protected-source/registration exclusions.

Ending authenticated telemetry measured `2026-10-23T19:10:33.3680770Z`: five-hour 25% remaining, reset `2026-10-23T23:15:20Z`; weekly 88% remaining, reset `2026-10-30T18:15:20Z`. The mandatory 15-point reserve remains intact.

R2 is complete within its bounded synthetic/component scope. Live GCS, actual Reader/Writer custody and real four-Windows-principal isolation remain unavailable/unproven. This is not operational C09 acceptance, OI-0002 closure, protected persistence approval or authority for R3/R4. Privileged IAM, key-custody and retention changes remain explicit Owner Human Gates.

The initial post-acceptance documentation check failed `1 failed, 17 passed` because only one canonical continuation marker had been advanced. That run receives no PASS credit. The correction synchronizes the marker across the existing checkpoint, current state, roadmap and their existing contract test without granting R3/R4 authority or changing product behavior.

