# C09 R1 implementation test ledger

## R1-I01-A1 — initial focused execution

Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py -q`
Environment: Windows, synthetic temporary Kernel/Identity SQLite stores, injected in-memory Witness; no network, credential or protected data.  
Result: **FAIL**, exit 1; `9 failed` before transaction execution.

Observed cause: adding `identity_backup` and `identity_restore` directly to `contracts/orchestrator/v2/permission-matrix.json` changed the frozen contract-set digest. `OrchestratorKernel` rejected startup with `ContractError` for every test. This is correct fail-closed behavior and no continuity, Identity or witness state was created. Security implication: capability definitions require an explicit governed Contract Set identity/digest update; raw contract mutation cannot silently enter execution.

Exact repair: compute and pin the new accepted Identity contract digest/version through the existing Kernel contract mechanism, add regression proving the old/mutated set is rejected and the exact new set is accepted, then rerun the same focused test as R1-I01-A2. C09/OI-0002 remain open; no active `OPEN_ITEMS.md` row is resolved.

## R1-I01-A2 — governed Contract Set and focused PASS

Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py -q`  
Result: **PASS**, exit 0; `9 passed in 4.00s`.

The Identity Contract Set now has distinct ID `ORCHESTRATOR_CONTRACT_SET_V2_IDENTITY_ADMINISTRATION_C09_R1` and exact pinned digest `sha256:fe140ebca6f207dd8f3aa46158328f3fa7f63b00f74851aa0af77c9c12ce9f77`. Tests cover durable PENDING/Identity commit/staged receipt/witness/Kernel COMMITTED/acknowledgment, process termination at four boundaries, ambiguous timeout after provider create, independent Reader denial, unavailable witness, exact replay, conflicting transaction/operation identity, ungranted backup/restore and forged capability. No external I/O or protected data was used. No active open-item row is resolved; implementation remains pending broader regression and independent review.

## R1-REG-A1 — invalid test-path selection

The first relevant-regression command included nonexistent `tests/unit/test_identity_permission_adapter.py`. Pytest exited 4 with `file or directory not found`; **no tests ran** and no PASS is claimed. No product state changed. Exact continuation is to derive the existing test paths from the repository and rerun the intended relevant set as R1-REG-A2.

## R1-REG-A2 — transient path inventory conflict

A repository-path inventory briefly exposed an untracked synthetic receipt-store test from another concurrent workspace action; it disappeared before collection. The attempted command exited 4 with `file or directory not found`; **no tests ran**. No candidate code was retained from that transient file and the worktree returned clean. Exact continuation is to use only `git ls-files` tracked test paths for R1-REG-A3.

## R1-REG-A3 — tracked relevant regression PASS

Command: tracked C09 transaction/protocol/adapter/simulator, Identity continuity/persistence/evidence/custody, IPC wire/envelope/response and Orchestrator Kernel unit suites.
Result: **PASS**, exit 0; `337 passed in 26.50s`.

This proves compatibility across the relevant bounded components, including the governed C09-R1 Contract Set. It does not establish real Named Pipe authentication, real principal separation, live GCS custody or operational C09 acceptance. Exact continuation is complete unit regression, candidate diff/security review and independent implementation review.

## R1-FULL-01 — complete unit regression PASS

Command: `PYTHONPATH=src python -m pytest tests/unit -q`
Result: **PASS**, exit 0; `1460 passed, 5 skipped in 280.95s`.

The full unit suite preserves existing behavior with the R1 synthetic durable transaction state machine and governed capability Contract Set. No real service, credential, cloud mutation, protected data, capability grant or external acknowledgment was activated. Exact continuation is candidate diff/security inspection and independent exact-SHA implementation review.

## R1 independent implementation review 01 — FAIL

Reviewed exact SHA: `8a6b655a9e6e1e1786055fd254b826d52fd6960f`.
Reviewer: `/root/c09_r1_implementation_independent_review`, separate read-only context.
Decision: **`INDEPENDENT_IMPLEMENTATION_FAIL`**.

Reviewer verification reproduced `9 passed` focused and `72 passed` relevant tests. Independent adversarial probes found:

- **F01 CRITICAL:** after injected Kernel reservation failure, local recovery could commit Identity and append Witness without an exact durable Kernel PENDING reservation; final Kernel transition alone rejected the ghost transaction too late.
- **F02 CRITICAL:** after a completed transaction, process restart and deletion of the external Witness, `acknowledge()` trusted local `COMMITTED` and returned success.
- **F03 HIGH:** canonical Witness bytes were stored only after provider append/readback rather than durably and atomically staged before provider interaction.

Required remediation is bounded to enforcing exact Kernel PENDING before every pre-finality mutation, fail-closed startup/recovery/acknowledgment Witness verification, and durable pre-append canonical staging. Required negative evidence includes every transition boundary plus missing, rewritten, wrong-generation, truncated-chain and reader-outage conditions. C09/OI-0002 remain open and no active open-item row is resolved.

Documentation verification initially named absent `tests/unit/test_documentation_consistency.py`; pytest exited 4 and no test ran, so no PASS is claimed for that command. Repository-derived correction is `tests/unit/test_documentation_index.py`.

Corrected documentation verification: `python -m pytest tests/unit/test_documentation_index.py -q` — **PASS**, exit 0; `18 passed in 0.83s`.
