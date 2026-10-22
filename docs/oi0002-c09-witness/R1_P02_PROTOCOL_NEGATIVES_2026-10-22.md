# R1-P02 closed schema, exact types and MAC substitution

Status: `PASS / BOUNDED SYNTHETIC PROTOCOL TEST / R1 OPEN`.

Test ID: `R1-P02`.

Command: `$env:PYTHONPATH='.runtime/c09-r1-testdeps;src'; python -m pytest tests/unit/test_c09_witness_protocol.py::test_r1_p02_schema_types_and_mac_substitution_fail_closed -q`.

Environment: Windows, Python 3.14, isolated ignored pytest 9.1.1 target, branch `c09-witness-hardening`, exact predecessor and verified GitHub remote HEAD `4abe8665a67a17e7374a0ca80f1a86448d03934c`.

Evidence: exit code 0; `1 passed, 1 warning in 0.21s`. The bounded test rejected a missing required field, rejected JSON boolean as an epoch despite Python's bool/int relationship, and rejected a substituted HMAC. The warning was the existing pytest cache-path collision and did not affect collection or execution.

Interpretation: the provider-neutral decoder is closed over its required field set, uses exact integer typing for sequence state, and authenticates canonical content. This is not chain, provider, custody, Kernel/Identity or crash-recovery evidence.

Caveats: the test uses a synthetic in-process HMAC key. It proves no durable or independently controlled key custody and changes no production path.

Exact continuation after push: implement and run one bounded ordered-chain verifier test covering contiguous sequence and previous-record linkage. Document and push it before any later test.

`OPEN_ITEMS.md` assessment: no row is resolved. OI-0002/C09 remain open and OI-0003 remains blocked.
