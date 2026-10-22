# T07 signer/Owner key separation - 2026-10-22

Verdict: LOCAL PASS / REAL KEY CUSTODY NOT PROVEN / C09 OPEN.

Gate: T06 documented and pushed at `e48edfa` before T07 execution.
Command: `PYTHONPATH=src python -m pytest tests/unit/test_c09_witness_simulation.py -q -k "owner_key or restore_authorization or cloud_credential"`.
Observed: `3 passed, 16 deselected in 0.25s`, exit 0. Tests verify that identical Owner/witness keys are rejected, changing Owner key invalidates prior restore authorization, restore replay/expiry/source mismatch are rejected, and cloud writer cannot forge witness MAC. The selected three tests do not prove physical or administrative separation.

GCS check: `gcloud iam service-accounts keys list --iam-account=c09-witness-reader@ai-tax-agent-507813.iam.gserviceaccount.com --managed-by=user --format=value(name)` produced no user-managed keys, exit 0. Reader uses short-lived impersonation. Writer key inventory and independent KMS/HSM custody NOT verified in this execution.

Critical gaps: signer secret and Owner restore secret remain synthetic in simulator; no independent real custody, distinct administrators, deployed signer or verifier, or secret-rotation/incident test. Project Owner can impersonate reader. No new secret was created. No operational security PASS. Proceed to T08 as a rejection/conditional independent review, not an acceptance declaration.
