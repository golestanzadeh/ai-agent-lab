# C09/R3 governed security deployment preparation

Status: `R3_PREPARATION_TECHNICAL_PASS / INDEPENDENT_REVIEW_PENDING / OPERATIONAL_NOT_ACCEPTED`.

## Recovery and admission

Branch `c09-witness-hardening` recovered clean and synchronized at `8004a665d1af92bc31a69a0273cc21f99128d83d`; R2 reviewed candidate is `a159373c768c52197e2c1647259e855a82e38f91`. Authenticated admission measured 99% five-hour and 88% weekly remaining after reset, preserving the mandatory 15-point reserve. The bounded estimate was 35 percentage points including inventory, implementation, regressions, independent review and reporting.

## Read-only operational inventory

Observed on `DESKTOP-HVRUQB7` without elevation or mutation:

| Boundary | Observed state | Classification |
| --- | --- | --- |
| `AITaxKernel` SID ending 1020 | exists, enabled | configured but inactive |
| `AITaxIdentity` SID ending 1021 | exists, enabled | configured but inactive |
| `AITaxKeyCustodian` SID ending 1022 | exists, enabled | configured but inactive |
| `AITaxRecovery` SID ending 1023 | exists, enabled | configured but inactive |
| C09 Windows services | none found | missing / Human Gate |
| AI-Tax-Agent scheduled tasks | three legacy tasks run as `rezag`; none uses an AITax principal | unrelated; not operational C09 proof |
| Protected ACLs | prior sealed `OI0002-TEST2` evidence retained; not read or changed in this execution | previously evidenced, operational deployment absent |
| GCS Writer/Reader | historical keyless single-record evidence exists | configured historically / current readback unavailable |
| `gcloud.cmd` | unavailable in current process | external verification blocked |
| Witness signing key | no operational provider/key ID approved | missing / Human Gate |
| Owner restore key | no operational offline custody approved | missing / Human Gate |
| Restore capability | ungranted and disabled | correctly fail closed |
| retention | historical seven-day `UNLOCKED`; no current readback | operational acceptance blocked |

The reusable read-only inventory command is `scripts/inspect-c09-r3-readonly.ps1`; it reports account SIDs/status and service/task metadata only. It does not read protected stores, key bytes or taxpayer data.

## Implemented non-privileged preparation

- `c09_r3_deployment.py` validates four distinct enabled pinned Windows identities, distinct fixed local pipe names, separate stores, distinct keyless Writer/Reader identities, closed exact GCS permissions, opaque separate signing/restore references and disabled restore/Retention Lock.
- Authorization is default deny. No role receives `identity_restore`; only Custodian gets the synthetic `use_nonexportable` action.
- Deployment, IPC, ACL and disabled-service template is data-only and contains no credentials or active command.
- GCS IAM proposal is data-only, applies nothing, adds no resource and explicitly denies destructive/admin permissions.
- Owner Human Gates are split by service activation, ACLs, IAM, signing custody, restore authority, reversible retention and irreversible lock.

## R3-T01–T06 evidence classification

| Test | Result | Evidence class | Operational limitation |
| --- | --- | --- | --- |
| R3-T01 principal isolation | PASS | synthetic model + read-only local identity inventory | services/tokens not activated |
| R3-T02 IPC authorization | PASS | synthetic configuration boundary; accepted R1/R2 protocol regressions | no real Named Pipe service |
| R3-T03 signing isolation | PASS | synthetic opaque/non-exportable reference and default-deny checks | no operational key/provider |
| R3-T04 restore authority | PASS | synthetic disabled/no-grant and independent-reference checks | no Owner offline key ceremony |
| R3-T05 Writer/Reader separation | PASS | synthetic exact-permission tests; historical isolated cloud proof | current IAM/live multi-record campaign absent |
| R3-T06 failure recovery | PASS | synthetic inactive/missing/retention activation rejection plus accepted R2 recovery | no operational process/principal campaign |

The first focused test command failed during collection because a Python raw string ended in a backslash; exit 1, no tests, no credit. After correction and template/script assertions, `PYTHONPATH=src python -m pytest tests/unit/test_c09_r3_deployment.py -q` passed `8 passed` in 0.23s. The read-only script returned the expected schema, four accounts, zero C09 services and `gcloud_available=false`. Relevant C09/Identity/IPC/Kernel regression passed `369 passed in 34.38s`; complete unit regression passed `1492 passed, 5 skipped in 294.08s`. The skips are the unchanged DR03 protected-source/registration exclusions and do not cover R3. Independent exact-SHA review remains required.

## Boundaries and continuation

No account, service, task, ACL, IAM binding, key, bucket, retention policy, protected store or data changed. No operational C09/R3 acceptance is claimed. Exact continuation: run relevant/full regression, freeze/push candidate, obtain `INDEPENDENT_R3_PREPARATION_*` on the exact SHA, repair any in-scope finding, and leave operational actions behind the seven documented Owner gates. R4 is not started; C09/OI-0002 remain open.
