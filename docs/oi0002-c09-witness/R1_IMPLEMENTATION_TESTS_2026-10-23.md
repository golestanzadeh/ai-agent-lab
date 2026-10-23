# C09 R1 implementation test ledger

## R1-I01-A1 — initial focused execution

Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py -q`  
Environment: Windows, synthetic temporary Kernel/Identity SQLite stores, injected in-memory Witness; no network, credential or protected data.  
Result: **FAIL**, exit 1; `9 failed` before transaction execution.

Observed cause: adding `identity_backup` and `identity_restore` directly to `contracts/orchestrator/v2/permission-matrix.json` changed the frozen contract-set digest. `OrchestratorKernel` rejected startup with `ContractError` for every test. This is correct fail-closed behavior and no continuity, Identity or witness state was created. Security implication: capability definitions require an explicit governed Contract Set identity/digest update; raw contract mutation cannot silently enter execution.

Exact repair: compute and pin the new accepted Identity contract digest/version through the existing Kernel contract mechanism, add regression proving the old/mutated set is rejected and the exact new set is accepted, then rerun the same focused test as R1-I01-A2. C09/OI-0002 remain open; no active `OPEN_ITEMS.md` row is resolved.
