# C09 witness local acceptance evidence

Status: `LOCAL_SIMULATION_PASS / NOT_C09_OPERATIONAL_PASS`

Command: `python -m pytest tests/unit/test_c09_witness_simulation.py -q`

Evidence: `src/agent_lab/c09_witness_simulation.py` and `tests/unit/test_c09_witness_simulation.py`.

| ID | Initial state | Injected event/attack | Expected and actual outcome | Result |
|---|---|---|---|---|
| AT-C09-01 | Two finalized records | Restore both locals to record 1 | Stale local state rejected; observed rejection | PASS |
| AT-C09-02 | One finalized record | Roll back Kernel head only | Head mismatch rejected; observed rejection | PASS |
| AT-C09-03 | One finalized record | Roll back Identity head only | Head mismatch rejected; observed rejection | PASS |
| AT-C09-04 | Empty | Crash after PENDING, before Identity | Deterministic abort; observed `ABORTED_BEFORE_IDENTITY` | PASS |
| AT-C09-05 | Empty | Crash after Identity, before witness | Fail closed; observed `FAIL_CLOSED_IDENTITY_AHEAD` | PASS |
| AT-C09-06 | Empty | Crash after witness, before Kernel finalization | Exact witness completes pending; observed `FINALIZED_FROM_WITNESS` | PASS |
| AT-C09-07 | Finalized OP-1 | Replay OP-1 | Duplicate rejected | PASS |
| AT-C09-08 | Same pending sequence | Two conflicting successors | First conditional create wins; second rejected | PASS |
| AT-C09-09 | Empty | Witness unavailable | Protected operation rejected | PASS |
| AT-C09-10 | Sequence 1 | Inject authenticated sequence 3 | Gap/high sequence rejected | PASS |
| AT-C09-11 | Epoch 1 | Inject unauthorized epoch 2 | Epoch fork rejected | PASS |
| AT-C09-12 | Current exact witness | Valid exact Owner restore authority | Authorization consumed once; authenticated RESTORE record starts epoch 2/sequence 1 and local state matches | PASS |
| AT-C09-13 | Current exact witness | Reuse, expiry and source mismatch | All rejected | PASS |
| AT-C09-14 | Current exact witness | Cloud writer inserts invalid-MAC successor | Authentication rejected; availability can still be denied | PASS |
| AT-C09-15 | Locked-version model | Delete marker plus replacement version | Version/delete-marker ambiguity rejected | PASS |

All 15 tests passed locally. These tests prove deterministic simulator behavior, not provider enforcement, credential custody, operational IPC or C09 acceptance.
