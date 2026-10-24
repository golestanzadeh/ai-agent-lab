# C09/R3 exact Owner Human Gates

Status: `PREPARED / NOT APPROVED / NOT EXECUTED`. Each item is independent. Approval of one does not approve another, R4, operational C09 acceptance or OI-0002 closure.

## HG-C09-R3-01 — Windows service activation

Gate readiness: **`NOT_APPROVAL_READY`** until exact protected executable paths, SHA-256 values and dry-run service definitions are committed and independently reviewed. The wording below is a future exact-form template and cannot currently authorize execution.

Incremental verification found no operational service entry-point implementation, executable artifact or approved reproducible Windows build process in the repository. `config/c09-r3/hg01-windows-services.json` therefore pins the exact names/accounts/SIDs/IPC/startup/recovery intent but deliberately records null executable paths/hashes and `execution_authorized=false`. The read-only verifier matched all accounts/SIDs and found zero installed C09 services. HG-01 cannot become approval-ready until a separately authorized service implementation and reproducible build produce exact artifacts for independent review.

Independent review of exact SHA `7fc27ca51e7123163804ae3041e276ef716cbea4` returned `HG01_PREPARATION_INDEPENDENT_PASS / NOT_APPROVAL_READY`; focused `10` and relevant `298` passed independently. A future ready revision must also make startup wording internally exact and expand rollback into explicit stop/disable/delete steps. No Owner approval statement is issued for this incomplete gate.

1. **Target:** local services `AITaxKernel`, `AITaxIdentity`, `AITaxKeyCustodian` on `DESKTOP-HVRUQB7`, using the existing SIDs pinned in `config/c09-r3/deployment-preparation.json`.
2. **Current state:** four accounts exist and are enabled; no matching service exists; legacy tasks run as `rezag` and are not C09 services.
3. **Change:** install the three disabled-by-default services from exact protected image paths/hashes, then activate only for the bounded synthetic operational campaign.
4. **Permission:** elevated local service installation plus `Log on as a service`; no Administrator membership.
5. **Justification:** real token authentication and store separation cannot be proven in-process.
6. **Cost:** no expected cloud cost; local operational/admin time only.
7. **Rollback:** stop/disable services, remove service definitions, preserve audit/evidence and accounts.
8. **Verification:** retained-handle image/SID checks, first-instance/local-only pipe negatives, four-token access matrix and zero unexpected services/tasks.
9. **Rejection:** R3 remains preparation-only; no operational principal/IPC claim.
10. **Future approval wording (invalid until blockers above are replaced by exact immutable values):** `I approve HG-C09-R3-01 for the exact three services, pinned SIDs and exact reviewed image paths/hashes, synthetic campaign only; no broader privilege or production activation.`

## HG-C09-R3-02 — Protected NTFS ACL application

Gate readiness: **`NOT_APPROVAL_READY`** until exact non-overlapping operational/backup/executable/custody paths, inheritance behavior, complete SDDL descriptors, pre-change readback and dry-run diff are committed and independently reviewed.

Incremental preparation now fixes five exact future store/backup/custody roots and canonical protected SDDL in `config/c09-r3/hg02-acl-proposal.json`. All five roots are absent; no executable target exists because HG-01 has no binary path. Read-only inspection captured the parent owner/inheritance and performed no mutation. Offline descriptor parsing validates every proposed SDDL, but elevated physical file identity/reparse/pre-change descriptor evidence cannot exist until the roots are separately approved and created. The rollback procedure is therefore specified but not currently executable. Independent review remains pending; no Owner approval statement is issued.

Independent review of `74edea4ae36631481aa7d41e2c54de36383a071d` failed because the initial proposal gave Recovery standing read access to stores/backups. The accepted architecture permits Recovery only through governed Kernel transitions. All Recovery ACEs are removed in the remediated proposal and a negative test now requires no Recovery SID in any filesystem DACL. Re-review remains mandatory.

Independent re-review of exact SHA `21aee1b3985b4dfef6d920f524889a2ce0af53fc` returned `HG02_PREPARATION_INDEPENDENT_PASS / NOT_APPROVAL_READY`; focused `12` and relevant `334` passed. The corrected SDDL has no standing Recovery access. No Owner approval statement is issued because roots/executables and mandatory elevated file-identity, SACL/current-state and rollback evidence remain absent.

1. **Target:** the exact Kernel, Identity, backup, executable and key-provider reference roots approved from the template; never the repository or a broad parent.
2. **Current state:** prior `OI0002-TEST2` sealed evidence proves a bounded ACL model, but operational roots do not exist/are not approved.
3. **Change:** create exact roots and apply explicit inheritance-disabled least-privilege ACLs.
4. **Permission:** elevated ACL administration on only the approved roots.
5. **Justification:** prevents cross-store and key access.
6. **Cost:** none expected.
7. **Rollback:** restore a pre-captured ACL descriptor only after services stop; never delete data.
8. **Verification:** effective-access probes under all four actual tokens, plus owner/SYSTEM recovery inspection.
9. **Rejection:** operational services remain disabled.
10. **Future approval wording (invalid until blockers above are supplied):** `I approve HG-C09-R3-02 for the exact reviewed roots and ACL descriptors only, with pre-change readback, rollback capture and four-token verification.`

## HG-C09-R3-03 — GCS least-privilege bindings

Gate readiness: **`NOT_APPROVAL_READY`** until a fresh policy version/etag readback, exact custom-role resource names, exact prefix condition and approved local keyless credential-delivery mechanism are committed and independently reviewed. `gcloud.cmd` is unavailable here, so current IAM cannot be asserted.

1. **Target:** project `ai-tax-agent-507813`, bucket `ai-tax-agent-c09-witness-test-507813`, exact deployment prefix and the two existing service accounts in `config/c09-r3/gcs-iam-proposal.json`.
2. **Current state:** historical isolated writer/reader probes passed; current IAM cannot be read because `gcloud.cmd` is unavailable in this process.
3. **Change:** apply/reconcile custom prefix-scoped Writer=create-only and Reader=get/list-only bindings; no user-managed keys.
4. **Permission:** narrow bucket IAM administration for the exact bindings.
5. **Justification:** separates append authority from verification.
6. **Cost:** normal test-object/storage/API charges within the existing test bucket; no new service.
7. **Rollback:** remove only the exact added bindings after preserving evidence; objects remain protected.
8. **Verification:** policy readback plus create/get/list/delete/update/admin positive/negative probes under both identities.
9. **Rejection:** mocked/local tests remain valid; live R3 remains blocked.
10. **Future approval wording (invalid until blockers above are supplied):** `I approve HG-C09-R3-03 for the exact existing test bucket, deployment prefix, policy version/etag, custom roles, condition and two service accounts; no new keys, bucket, retention or project-wide role.`

## HG-C09-R3-04 — Operational Witness signing custody

1. **Target:** one non-exportable HMAC-SHA-256 key and manifest-pinned key ID for deployment `C09-R3-OPERATIONAL-PENDING`, accessible only through `AITaxKeyCustodian`.
2. **Current state:** no durable operational signing key/provider reference is approved or verified.
3. **Change:** provision the key in an Owner-selected provider and bind only use/verify, never read/export, to the Custodian.
4. **Permission:** provider key creation and narrowly scoped use grant.
5. **Justification:** Writer compromise must not permit a valid record forgery.
6. **Cost:** provider-dependent and must be presented before approval if non-zero.
7. **Rollback:** disable new signing; retain historical verification capability; never delete/rotate within deployment v1.
8. **Verification:** Custodian success, every other principal read/export/use/replace denial, restart and historical verification.
9. **Rejection:** no operational authenticated Witness chain.
10. **Approval wording:** `I approve HG-C09-R3-04 only after the exact provider, key ID, custody ACL and cost are supplied; the key must be non-exportable and usable solely by AITaxKeyCustodian.`

## HG-C09-R3-05 — Owner restore authority

1. **Target:** offline Owner ECDSA P-256 restore key and public-key manifest for the accepted owner-restore contract.
2. **Current state:** no approved operational Owner restore key or custody procedure exists; restore capabilities are ungranted.
3. **Change:** provision offline private custody and publish only the reviewed public key/key ID; do not grant standing restore capability.
4. **Permission:** Owner-controlled offline key ceremony and public manifest update.
5. **Justification:** restore authorization must be independent of rollbackable local/cloud runtime state.
6. **Cost:** depends on Owner-selected offline custody method.
7. **Rollback:** revoke future use through the governed control chain while retaining historical public verification.
8. **Verification:** signature vectors; wrong/expired/revoked/reused authorization and every runtime-principal private-key access denied.
9. **Rejection:** operational restore stays unavailable and fail closed.
10. **Approval wording:** `I approve HG-C09-R3-05 only for the exact reviewed offline custody method, key ID and public manifest; no standing restore grant or private-key exposure to runtime principals.`

## HG-C09-R3-06 — Retention policy change

1. **Target:** exact existing test bucket and deployment prefix.
2. **Current state:** seven-day retention is historically recorded as `UNLOCKED`; current policy readback is unavailable here.
3. **Change:** first approve a reversible retention configuration and verify it. **Retention Lock is explicitly excluded.**
4. **Permission:** narrow bucket retention administration.
5. **Justification:** records must resist deletion/version substitution through the evidence lifetime.
6. **Cost:** storage/early-deletion exposure requires a fresh estimate.
7. **Rollback:** only while unlocked, restore the captured prior policy.
8. **Verification:** policy readback, delete/overwrite/version tests and complete enumeration.
9. **Rejection:** operational rollback-resistance acceptance remains blocked.
10. **Approval wording:** `I approve only the exact reversible unlocked retention proposal and stated cost for the existing test bucket; I do not approve Retention Lock.`

## HG-C09-R3-07 — Irreversible Retention Lock

This is deliberately **not approval-ready**. It requires a separate future Owner decision after reversible operational verification, exact duration/cost/legal-retention analysis and independent security review. Consequence of rejection: the deployment cannot claim locked-WORM operational evidence, but local development remains nonblocking.

