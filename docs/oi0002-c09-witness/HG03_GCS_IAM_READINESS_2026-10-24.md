# C09/R3 HG-03 GCS IAM readiness

Status: `REVIEW_READY / NOT_APPROVAL_READY / NO CLOUD MUTATION`.

## Authenticated read-only inventory

On 2026-10-24 the installed Cloud SDK `590.0.0` at `C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd` authenticated as the Owner account and read project `ai-tax-agent-507813`. The exact bucket is `ai-tax-agent-c09-witness-test-507813` in `EUROPE-WEST3`; uniform bucket-level access and public-access prevention are enabled. Its seven-day retention policy is present and unlocked. No retention setting was changed.

The bucket IAM policy readback omitted the version field (the IAM v1/default representation), yielding effective version `1`, ETag `CAQ=`. The Writer has unconditioned `roles/storage.objectCreator`; the Reader has unconditioned `roles/storage.objectViewer`. There are no custom project roles and no IAM Conditions. The project policy readback explicitly returned version `1`, ETag `BwZa0Iovf6w=`. Legacy project basic-principal bucket bindings remain and can bypass the proposed two-principal restriction. Both service accounts exist, have zero user-managed keys, and grant the Owner user `roles/iam.serviceAccountTokenCreator`. No Workload Identity pool exists.

These are observed facts, not acceptance. ETags are concurrency preconditions and must be freshly re-read immediately before any separately approved change.

## Exact least-privilege proposal

The machine-readable package is `config/c09-r3/hg03-gcs-iam-readiness.json`; the exact conditional bucket-policy candidate is `config/c09-r3/hg03-proposed-bucket-policy.json`.

- Writer role: `projects/ai-tax-agent-507813/roles/c09WitnessWriter`, only `storage.objects.create`, exact object-prefix condition.
- Reader object role: `projects/ai-tax-agent-507813/roles/c09WitnessObjectReader`, only `storage.objects.get`, exact object-prefix condition.
- Reader listing role: `projects/ai-tax-agent-507813/roles/c09WitnessBucketLister`, only `storage.objects.list`, exact-bucket condition.
- Remove the Writer's unconditioned objectCreator binding and Reader's unconditioned objectViewer binding in the same ETag-protected policy replacement.

The list permission is evaluated on the bucket resource and does not itself filter returned names by object prefix. Therefore the dedicated witness-only bucket, application exact-prefix validation, generation-pinned reads and complete-chain verification are mandatory additional controls. IAM Conditions are not represented as complete object-level isolation.

The legacy project basic-principal bindings are deliberately retained in the candidate because removing them is a project-wide security/governance change whose impact has not been reviewed. Their presence keeps HG-03 not approval-ready.

## Keyless authentication finding

Historical live tests used interactive Owner-authenticated `gcloud` impersonation. That proves neither Windows-service binding nor operational custody. The required operational design is short-lived service-account impersonation, maximum token lifetime 3600 seconds, role-specific Storage scopes, no token persistence, exact local-service-to-cloud-identity binding, audited correlation, and fail-closed refresh/revocation with no shared/user-managed-key fallback.

No approved non-exportable source credential or Windows service binding currently implements those properties. Workload Identity Federation is not configured. The Owner's current Token Creator grants are test access, not accepted operational custody. Choosing/provisioning an operational source credential is a separate architecture/Human Gate; this package does not invent or activate one.

## Proposed deployment and rollback commands — do not execute without a new exact Owner approval

The following commands are documentation only. Immediately before execution, read and compare the live policy and ETag; any mismatch stops the operation. Role creation must use the three exact permission lists above.

```powershell
$gcloud = 'C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd'
& $gcloud iam roles create c09WitnessWriter --project=ai-tax-agent-507813 --title='C09 Witness Writer' --permissions=storage.objects.create --stage=GA
& $gcloud iam roles create c09WitnessObjectReader --project=ai-tax-agent-507813 --title='C09 Witness Object Reader' --permissions=storage.objects.get --stage=GA
& $gcloud iam roles create c09WitnessBucketLister --project=ai-tax-agent-507813 --title='C09 Witness Bucket Lister' --permissions=storage.objects.list --stage=GA
& $gcloud storage buckets set-iam-policy gs://ai-tax-agent-c09-witness-test-507813 config/c09-r3/hg03-proposed-bucket-policy.json
```

Post-change verification must re-read policy/version/ETag and role definitions, then run synthetic positive/negative probes: Writer create only under the prefix; Writer get/list/delete/update/admin denied; Reader intended get/list only; Reader create/delete/update/admin and identity impersonation denied; stale-ETag replacement rejected. No live enforcement probe is authorized now.

Rollback must use a freshly captured post-change ETag, remove only these three conditioned bindings, restore exactly the two pre-change service-account bindings, and delete a custom role only after confirming no binding references it. Witness objects and audit evidence must remain. Legacy-binding remediation requires its own reviewed rollback plan.

## Cost and exact Human Gate

No new service is proposed. Existing Cloud Storage object, operation and audit-log costs apply to a future synthetic campaign; marginal cost depends on test volume.

The future Owner statement is recorded in the JSON package. It is not presently actionable because the keyless delivery architecture, legacy binding remediation, live negative enforcement and a then-current ETag remain unresolved.

## Verification performed

- Authenticated read-only GCS/IAM/service-account/key/WIF inventory: exit `0`.
- Focused offline HG-01/HG-02/HG-03 preparation tests: `21 passed`.
- No IAM, key, role, bucket, retention or credential mutation occurred.

Independent reviews of `df1c939` and `1eb9c94` initially failed and identified enforceability gaps in condition, ETag, full-policy-member and keyless-contract validation. Those findings were corrected. Independent re-review of exact SHA `0f197ef9682ccf79f9df7743748951585cfdcaa8` returned `HG03_PREPARATION_INDEPENDENT_PASS / NOT_APPROVAL_READY`; reviewer tests passed `33` focused and `327` relevant, and all 14 adversarial substitutions were rejected. Even with preparation PASS, the operational blockers above keep the gate not approval-ready.
