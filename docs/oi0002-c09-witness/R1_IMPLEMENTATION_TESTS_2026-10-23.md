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
