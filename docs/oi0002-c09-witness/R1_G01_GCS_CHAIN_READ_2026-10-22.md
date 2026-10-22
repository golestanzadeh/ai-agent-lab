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
