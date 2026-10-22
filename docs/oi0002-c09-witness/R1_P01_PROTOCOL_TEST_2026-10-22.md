# R1-P01 strict canonical witness decoding - attempt 1

Status: `ENVIRONMENT_FAIL / TEST_NOT_COLLECTED / R1 OPEN`.

Test ID: `R1-P01-A1`.

Command (PowerShell): `$env:PYTHONPATH='src'; python -m pytest tests/unit/test_c09_witness_protocol.py::test_r1_p01_strict_canonical_decode_rejects_reformatted_and_duplicate_json -q`.

Environment: Windows workspace `C:\Users\rezag\ai-agent-lab-c09-continuation`; branch `c09-witness-hardening`; local and freshly fetched remote were both `36c50fe4c1e268efb0bd241c1b755bbed70da094` before the change; default interpreter `C:\Python314\python.exe`.

Evidence: exit code `1`; `C:\Python314\python.exe: No module named pytest`. Pytest did not collect or execute the named test. No PASS is claimed.

Interpretation and caveats: this is an interpreter/tooling selection failure, not evidence for or against canonical protocol behavior. The implementation is unaccepted and R1 remains open. No cloud call, credential use, production mutation, retention-policy change or protected-data operation occurred. Selecting an existing pytest-capable repository interpreter is safe; installing dependencies or weakening the test is not authorized by this result.

Exact continuation after push: discover the existing pytest-capable interpreter without modifying dependencies, then rerun the exact R1-P01 node as a new test transaction. Document and push its result before any later R1 test.

`OPEN_ITEMS.md` assessment: no active row is resolved. OI-0002 remains active; OI-0003 remains blocked.
