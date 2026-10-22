# R1-G01 generation-pinned GCS chain read

## Attempt 1

Status: `ENVIRONMENT_FAIL / TEST_NOT_COLLECTED / R1 OPEN`.

Test ID: `R1-G01-A1`.

Command: `$env:PYTHONPATH='.runtime/c09-r1-testdeps;src'; python -m pytest tests/unit/test_c09_gcs_witness_adapter.py::test_r1_g01_chain_read_pins_generations_and_rejects_version_ambiguity -q`.

Environment: Windows, Python 3.14, isolated pytest 9.1.1 target, predecessor/verified remote HEAD `1f244ad3d5088d246d17726b5c84fa6f0b9fd4f4`.

Evidence: exit 1; collection error `ModuleNotFoundError: No module named 'requests'`; zero tests collected. Two pytest-cache warnings were also emitted.

Interpretation: the isolated runner lacks the project's pinned runtime dependency `requests==2.34.2`. This is no evidence for or against the GCS chain reader. No network request, cloud write or protected operation occurred.

Caveats: candidate code is unaccepted. R1 remains open.

Exact continuation after push: install the repository-pinned requests dependency into the same isolated ignored target, preserve normal-user read access, and rerun only R1-G01 as attempt 2.

`OPEN_ITEMS.md` assessment: no active row is resolved; OI-0002/C09 remain open and OI-0003 remains blocked.

## Attempt 2

Status: `FAIL / TEST ASSERTION DEFECT / R1 OPEN`.

Environment preparation: installed repository-pinned `requests==2.34.2` and its dependencies into the ignored target, then applied read/execute ACL to the current sandbox SID; 1289 files processed with zero ACL failures.

Observed evidence: exit 1; `1 failed, 2 warnings in 2.02s`. The chain reader returned records whose printed fields and MACs matched, but the test compared the operational `c09_witness_protocol.WitnessRecord` dataclass to the separate legacy simulator dataclass. Dataclass equality correctly returned false across different classes. The version-ambiguity branch was not reached after the first assertion failed.

Interpretation: this is a fixture/assertion boundary defect, not a demonstrated chain-reader correctness failure. No provider call occurred; the session was mocked. No PASS is claimed.

Exact continuation after push: compare returned and fixture records by exact canonical bytes instead of cross-class dataclass equality, then rerun only R1-G01 as attempt 3.
