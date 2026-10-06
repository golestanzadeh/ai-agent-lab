# Milestone A End-to-End Acceptance

Status: **MA-05 IMPLEMENTED / INDEPENDENTLY ACCEPTED**

This package proves the complete local synthetic journey from registered case creation through intake, processing, specialist and chief review, calculation, form preview, two distinct durable approvals, synthetic submission, placeholder receipt, and restart recovery.

The integration proof creates only synthetic local SQLite state under pytest temporary storage. It verifies the final reopened workflow and coordinator state and proves that exactly one operation, result, and placeholder receipt exist. The existing MA-02 through MA-04 suites provide the failure matrix for stale transitions, crash boundaries, replay, duplicate prevention, revocation, expiry, corruption, registered and unregistered cross-case isolation, and approval reuse.

The dedicated GitHub Actions workflow has read-only repository permission, installs only pytest, and runs the synthetic integration, failure/recovery, governance, and documentation suites. On failure it writes a closed, privacy-safe, integrity-digested STOP diagnostic and uploads that diagnostic as the sole failure artifact for 30 days. This artifact is actionable recovery evidence but is not executable authority. The workflow has no secrets, credentials, provider identifiers, protected material, ERiC invocation, signing, network tax action, ELSTER/Finanzamt contact, or external transmission step.

The reproducible local command is:

```powershell
$env:PYTHONPATH = "src;."
python -m pytest -q tests/integration/test_milestone_a_golden_journey.py tests/unit/test_synthetic_workflow_store.py tests/unit/test_synthetic_workflow_actions.py tests/unit/test_durable_submission_approval.py tests/unit/test_milestone_a_submission.py tests/unit/test_milestone_a_contract.py tests/unit/test_documentation_index.py tests/unit/test_ma05_stop_diagnostic.py
```

Verification: the exact focused command passes with `62 passed`; a clean temporary virtual environment with only pytest installed passes the then-current focused surface with `60 passed`; the complete unit regression passes with `915 passed, 1 warning`; final independent acceptance is `PASS`.
