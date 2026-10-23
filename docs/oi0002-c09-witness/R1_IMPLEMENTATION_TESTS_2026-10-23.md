# C09 R1 implementation test ledger

## R1-I01-A1 — initial focused execution

Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py -q`
Environment: Windows, synthetic temporary Kernel/Identity SQLite stores, injected in-memory Witness; no network, credential or protected data.  
Result: **FAIL**, exit 1; `9 failed` before transaction execution.

Observed cause: adding `identity_backup` and `identity_restore` directly to `contracts/orchestrator/v2/permission-matrix.json` changed the frozen contract-set digest. `OrchestratorKernel` rejected startup with `ContractError` for every test. This is correct fail-closed behavior and no continuity, Identity or witness state was created. Security implication: capability definitions require an explicit governed Contract Set identity/digest update; raw contract mutation cannot silently enter execution.

Exact repair: compute and pin the new accepted Identity contract digest/version through the existing Kernel contract mechanism, add regression proving the old/mutated set is rejected and the exact new set is accepted, then rerun the same focused test as R1-I01-A2. C09/OI-0002 remain open; no active `OPEN_ITEMS.md` row is resolved.

## R1-I01-A2 — governed Contract Set and focused PASS

Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py -q`.
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

## R1 remediation focused verification

Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py -q`.
Result: **PASS**, exit 0; `18 passed in 8.25s`.

The remediation adds a non-mutating local `PREPARED` state, exact transaction/request binding in the durable Kernel reservation, authorization plus pending-reservation revalidation before every pre-finality side effect, canonical pre-provider `WITNESS_STAGED` bytes, and fail-closed committed-Witness/Kernel verification at restart and acknowledgment. Tests now cover six crash boundaries; failed reservation with no Identity or Witness effect; ambiguous provider completion; missing, rewritten and wrong-generation Witness objects; reader outage; truncated local chain; and durable bytes before provider append. This is still synthetic-only candidate evidence pending relevant/full regression and independent exact-SHA re-review.

## R1 remediation relevant regression

Command: focused C09 transaction/protocol/simulator/GCS adapter, Identity continuity/custody/evidence/persistence, IPC wire/envelope/response and Orchestrator Kernel suites.
Result: **PASS**, exit 0; `346 passed in 27.91s`.

The exact remediation remains synthetic/component evidence. It activates no IPC, cloud mutation, credential, protected data, role grant or operational acknowledgment. Full unit regression and independent exact-SHA security re-review remain mandatory.

## R1 remediation complete unit regression

Command: `PYTHONPATH=src python -m pytest tests/unit -q`.
Result: **PASS**, exit 0; `1469 passed, 5 skipped in 285.38s`.

The full unit suite is green after F01-F03 remediation. Independent implementation re-review of the exact frozen commit remains required before any R1 acceptance claim.

## R1 independent implementation re-review 02 — FAIL

Reviewed exact SHA: `f7d973a82c35d82aadd8a6436957f10a447d0852`.
Decision: **`INDEPENDENT_IMPLEMENTATION_FAIL`**.

The reviewer confirmed F01-F03 materially corrected and reproduced `18 passed in 7.38s` focused plus `81 passed in 19.86s` relevant tests. Independent fault injection found **F04 CRITICAL**: after two committed transactions, restoring both local Kernel and Identity databases to the valid TX-1 snapshot while retaining both external Witness records allowed startup and TX-1 readback. Local rows incorrectly defined the verification set, so the external TX-2 successor was invisible.

Required repair: the Witness reader must independently enumerate a complete, current chain/head and startup/recovery must compare it against local durable rows and Kernel/Identity continuity, rejecting extra successors, gaps, forks, deleted generations and stale/partial listings. Required evidence includes the exact coordinated-rollback probe, one/multiple unseen tails and stale/partial enumeration. No active open-item row is resolved.

## R1-F04-A1 — initial complete-chain remediation test

Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py -q`.
Result: **FAIL**, exit 1; `6 failed, 15 passed in 10.17s`.

Independent enumeration made missing, rewritten, wrong-generation and truncated evidence fail closed, but three older tests asserted the former provider exception type rather than the coordinator integrity denial. More importantly, the two-record rollback test exposed that `WitnessRecord.epoch` remained fixed at 1 while sequence advanced. No PASS is claimed. The bounded correction is to bind both epoch and sequence to `expected_epoch + 1`, retain fail-closed integrity errors at the coordinator boundary, and rerun the exact suite.

## R1-F04-A2 — complete-chain remediation focused PASS

Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py -q`.
Result: **PASS**, exit 0; `21 passed in 8.72s`.

Both Witness epoch and sequence now equal the committed successor epoch. The injected reader independently returns the complete current chain; local durable rows no longer define the external verification set. One and two unseen external successors, missing/tampered/wrong-generation evidence, local truncation, partial listing and unavailable complete enumeration all fail closed. Regression and independent re-review remain required.

## R1-F04 regression

- Relevant C09/Identity/IPC/Kernel command: **PASS**, exit 0; `349 passed in 29.82s`.
- Complete unit command `PYTHONPATH=src python -m pytest tests/unit -q`: **PASS**, exit 0; `1472 passed, 5 skipped in 288.44s`.

This freezes synthetic/component candidate evidence only. Another independent exact-SHA implementation re-review remains mandatory.

## R1 independent implementation re-review 03 — FAIL

Reviewed exact SHA: `9be09e7cb84e04663eaf896f1a482a1b9be4d23b`.
Decision: **`INDEPENDENT_IMPLEMENTATION_FAIL`**.

The reviewer confirmed F01-F03 and direct F04 complete-chain rollback corrections, reproducing `21 passed` focused and `84 passed` relevant. **F05 CRITICAL** remains: a valid-looking partial listing equal to the rolled-back local prefix is accepted, and `GCSWitnessAdapter.read_chain()` issues one list request without consuming `nextPageToken`. The adversarial probe retained two external objects, restored both local stores to the first transaction, returned only the first external item, and startup accepted it.

Required repair is exhaustive pagination until `nextPageToken` is absent, rejection of malformed/repeated tokens, duplicate objects across pages, deletion/version ambiguity and incomplete synthetic enumeration. Required tests cover first-page-only rollback denial, valid multi-page chains, repeated/invalid tokens, page-order variation, cross-page duplicates and deletion metadata. No active open-item row is resolved.

## R1-F05-A1 — initial pagination remediation test

Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py tests/unit/test_c09_gcs_witness_adapter.py -q`.
Result: **FAIL**, exit 1; `2 failed, 30 passed in 10.39s`.

The new partial-enumeration path raised fail-closed `WitnessError` while an older assertion expected `C09TransactionError`; the valid multi-page reader returned the contract tuple while its new assertion compared against a list. These are bounded test-expectation defects, not permission or external-state changes. No PASS is claimed.

## R1-F05-A2 — pagination remediation focused PASS

Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_transaction_state.py tests/unit/test_c09_gcs_witness_adapter.py -q`.
Result: **PASS**, exit 0; `32 passed in 9.70s`.

The reader consumes all pages through terminal absence of `nextPageToken`; it rejects repeated or malformed tokens, duplicate objects across pages, deletion/version ambiguity and incomplete synthetic enumeration. A complete two-page chain with reversed page order is sorted and verified deterministically. Regression and independent review remain mandatory.

## Capacity stop after R1-F05-A2

Authenticated measurement at `2026-10-23T14:07:03.7832886Z`: five-hour remaining 21%, reset `2026-10-23T18:24:15Z`; weekly remaining 76%, reset `2026-10-29T20:33:11Z`. With the mandatory 15-point five-hour reserve, only 6 points are admissible, which is insufficient for the remaining relevant/full regression, independent review and governed result cycle.

Status: **`BLOCKED_CAPACITY / R1_REVIEW_NOT_COMPLETE`**. Clean synchronized recovery commit is `17657f276999cdf815df7ac9e3595b82b85bd7df`. After reset, obtain fresh authenticated admission, run relevant and complete unit regression, publish the exact evidence SHA and request independent re-review. R2 remains prohibited until R1 independent PASS.
