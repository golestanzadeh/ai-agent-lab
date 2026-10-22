# C09 synthetic GCS pilot evidence (2026-10-22)

Status: T01-T04 LIMITED LIVE PASS; T05 LOCAL PASS / OPERATIONAL PENDING; C09 OPEN / NOT ACCEPTED.

Environment: project `ai-tax-agent-507813`, Frankfurt bucket `ai-tax-agent-c09-witness-test-507813`. Synthetic data only. No production Kernel/Identity mutation. Source commit `1826356`.

| Test | Observed evidence | Verdict and limitation |
|---|---|---|
| T01 conditional create | Existing synthetic object rejected on `ifGenerationMatch=0` with HTTP 412 | PASS for GCS create-if-absent, not operational adapter |
| T02 writer least privilege | `c09-witness-test@ai-tax-agent-507813.iam.gserviceaccount.com` bucket `roles/storage.objectCreator`; GET/DELETE HTTP 403; LIST denied | PASS for tested identity |
| T03 retention | Bucket retention `604800` seconds, effective `2026-10-22T19:38:44.500Z`, NOT LOCKED. Owner DELETE HTTP 403; object remained, generation `1792696997556544` | LIMITED PASS; HTTP 403 response body not preserved, precise denial cause unproven; privileged policy change remains possible |
| T04 reader | `c09-witness-reader@ai-tax-agent-507813.iam.gserviceaccount.com` bucket `roles/storage.objectViewer`, keyless impersonation. Metadata read generation `1792696997556544`, size 41, CRC32C `lHI6GA==`, retention expiration `2026-10-29T19:23:17Z`. Content equality true; SHA256 `B90BB1CC9DD986E439470F6EA64C62081F45684FA21C8640FED4D504F1D5DFC0`; DELETE HTTP 403; CREATE HTTP 403 | PASS for isolated read/negative permissions; not an independent cryptographic chain validator; impersonator remains project Owner |
| T05 coordinated rollback | `AT-C09-01` restores both simulated local heads to earlier record and `recover()` rejects stale state. `AT-C09-02/03` separately reject single-head rollback. `PYTHONPATH=src python -m pytest tests/unit/test_c09_witness_simulation.py -q` returned `19 passed in 0.40s` on 2026-10-22 | LOCAL PASS only; no actual signed multi-record GCS chain or production fail-closed enforcement |

T04 initial token impersonation attempt returned IAM `getAccessToken` PERMISSION_DENIED despite correct binding; retry later succeeded without further IAM change. This transient failure is retained as evidence.

Documentation debt: original 15-case acceptance table is a scenario catalogue, NOT total test count. Four extra pytest cases cover key separation, Identity-head mismatch, witness outage, and unverifiable recovery base. A previous decision report and crash matrix contain obsolete claims about Identity-ahead recovery; current implementation conditionally reconciles only a verifiable base, otherwise fails closed. Evidence is based on observed console outputs, not a captured immutable cloud audit export.

Next gate: T06 must be documented and committed before T07. T07 likewise before T08. T08 requires independent authority and cannot be self-approved. No C09 operational acceptance until integrated Kernel/Identity, real chain verification, key custody and control-plane separation are proven.
