# R1 focused witness regression

Status: `PASS / LOCAL_AND_MOCKED_ONLY / R1 NOT ACCEPTED`.

Test ID: `R1-REG-01`.

Command: `$env:PYTHONPATH='.runtime/c09-r1-testdeps;src'; python -m pytest tests/unit/test_c09_witness_protocol.py tests/unit/test_c09_gcs_witness_adapter.py tests/unit/test_c09_witness_simulation.py -q`.

Environment: Windows, Python 3.14, pytest 9.1.1 and repository-pinned requests 2.34.2 in ignored workspace test target; predecessor and verified remote HEAD `a286f4394a9d1e47e7ff0fa5de0022387eee0080`.

Evidence: exit 0; `28 passed, 1 warning in 1.00s`. The warning was the known pytest-cache path collision. Executed scope: 3 shared-protocol tests, 6 mocked GCS-adapter tests, and 19 local simulator tests.

Interpretation: the new shared canonical protocol and mocked generation-pinned chain reader preserve the prior simulator behavior. This does not prove live multi-record listing/version semantics, durable staged receipts, Kernel/Identity service separation, process-kill recovery, custody, restore or operational C09 acceptance.

Exact continuation is governed by the consolidated blocked report. No later test or phase was started.

`OPEN_ITEMS.md` assessment: no row is resolved; OI-0002/C09 remain open and OI-0003 remains blocked.
