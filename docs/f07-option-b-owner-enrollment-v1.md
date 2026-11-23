# Option B Owner enrollment v1

Status: PROPOSED / OWNER_ENROLLMENT_APPROVAL_REQUIRED. Not operational acceptance.
Baseline: 902c9db699e36c2bf90f101ec4c81344adeccc1d. This is one bounded
deployment/security amendment to the existing F07 architecture, not a replacement
Identity protocol. No enrollment or real-data mutation was performed.

## One recommended decision

Approve application-specific Windows Hello enrollment for the existing local
Owner Broker, separate per-user DPAPI-protected runtime signing material, and
Identity-owned immutable Owner declarations in the canonical Identity SQLite.
Do not use the browser session, Windows SID alone, UI03 grants, the existing
case-integrity HMAC key, or interactive Drive OAuth as this authority.

The Owner must explicitly authorize initial creation/enrollment of these
credentials and the corresponding public-key/reference pins. Existing permission
to implement Family is not permission to manufacture those pins. Enrollment
approves no personal facts, imports no existing taxpayer records, and grants no
external submission authority. Previously confirmed facts remain confirmed.

## Observed host and existing authority

Read-only native query on 2026-11-23: WebAuthN API version9; platform user-verifying
authenticator available, HRESULT0. No prompt/key creation occurred. This establishes
availability only, not credential enrollment, device attestation or successful
ceremony. The platform credential must be verified during enrollment; failure
stops enrollment without choosing an alternative authenticator implicitly.

Actual application Cases directory has cases.sqlite, orchestrator-kernel.sqlite
and case-integrity.dpapi; identity.sqlite is absent there. No key was decrypted.
The old ProgramData service configuration is absent and is not an Option B
prerequisite. Existing canonical Identity persistence and
identity_evidence_authority.py provide storage/lineage mechanisms, not an already
accepted live Owner root. Their synthetic authorization cannot become real
authority by flag/configuration alone.

## Exact interaction and trust bootstrap

1. A local native enrollment action presents this scope and the actual canonical
   paths to the Owner. Explicit Owner authorization is recorded through the
   existing governed enrollment/Human Gate mechanism. No HTTP form can self-enroll
   its own authority. Native Windows Hello creates an application-specific P-256
   credential with required user verification; independently verify the returned
   registration and credential/public-key binding before pinning it. Never accept
   a caller-provided public key as an enrolled pin. Enrollment cancellation or
   partial initialization leaves Family disabled; use the existing recovery path.
2. The existing Broker displays the operation/case/year/person and proposed values
   in its trusted local confirmation surface. Values are not written to logs.
   Kernel allocates a cryptographically random nonce and exact execution scope,
   persisted before asking Windows Hello. Native Broker owns client-data creation;
   no additional HTTP origin/localhost alias or browser authorization is implied.
3. Proposed assertion profile: owner_identity_assertion.py CONTRACT v1, P-256
   ES256, RP localhost, client-data origin http://localhost:8766, get assertion,
   UP+UV and device-bound/non-backup profile, maximum300-second challenge lease.
   This native ceremony profile requires enrollment/interoperability verification;
   the HTTP dashboard remains on127.0.0.1:8766 with its existing CSRF policy.
   Challenge commits canonical operation, Owner, case, tax year, subject, input
   digest, deployment, store, task, manifest, run, nonce and issue/expiry times.
4. Broker verifies the actual signature against the accepted pin, exact scope,
   lease, RP and UV. The existing Kernel transaction must consume the outstanding
   nonce, advance the enrolled counter when supported, record proof commitment and
   issue the exact approval atomically. A unique consumed nonce rejects replay
   after restart/concurrent requests. A lost response resolves the original issued
   approval; it never authorizes another operation. The pure verifier implemented
   here deliberately cannot issue an approval or consume a nonce by itself.
5. Use the existing scoped Identity authorization/evidence envelopes and accepted
   PREPARE/COMMIT/FINALIZE/GET_TRANSACTION/ABORT path. Domain write, authorization
   consumption, logical head, audit and receipt remain one Identity transaction.
   Browser input is a proposal until the authenticated Broker approves that digest.

## Protected source and custody amendment

Only authenticated Owner-entered declarations may use an Identity-owned source
root in the existing canonical Identity database. Store actual immutable canonical
declaration bytes and revisions with existing declaration/confirmation lineage;
digest-only metadata is insufficient. Reference registration must verify the
Broker proof, exact scope, immutable revision, content digest, expiry and revocation.
Only this source kind may be independent of the case's Drive storage root.
Existing identity_mutation_source.resolve currently requires every artifact's
provider/root to equal case storage: a narrow versioned source-kind exception,
independently reviewed, is required before activation. Document evidence continues
to require the original exact case/provider/root/object/revision binding. Requests
cannot select or replace trust roots. No shared relationship/parent-child authority
is implied by this single-subject amendment.

Use distinct DPAPI-per-user protected application keys for existing Kernel and
Identity roles. Store public pins/enrollment references in their existing canonical
stores; keep private material outside Git in the existing protected application
configuration location. Do not reuse case-integrity.dpapi or create keys now.
This explicitly gives up OS-enforced separation between those same-user roles;
same-user malware can access app keys/stores. Windows Hello proves a user-verified
credential assertion, not immunity from a compromised same-user application.

No interactive Google Drive OAuth token is enrolled as an Identity credential.
The existing GCS Witness architecture and independent finality/custody requirements
remain unchanged. Previously tested bucket/ephemeral test key are not an accepted
operational deployment. Verify current accepted Witness binding during enrollment
readiness; absent independent signing/finality evidence fails closed. Do not
create IAM identities, change retention or substitute local audit for Witness.

## Frozen controls and acceptance

Option B was already Owner approved; C02/C03/C06/C08/C09/C11/C13 must reflect the
documented same-user custody reduction, not claim four-principal guarantees.
Retain Default Deny, Permission Matrix, Kernel sole coordination, exact isolation,
logical/audit heads, single-use mutation authorization, Kill Switch, independent
Witness/rollback checks and two approvals for external submission. HG deployment
history is preserved, not implicitly approved or reinstated as the target.

Before enabling Family: independent exact-SHA contract/implementation review;
actual native registration/assertion/cancellation/denial; atomic nonce issuance
and consumption with replay/concurrency/lost-response/restart tests; immutable
source substitution/revocation tests; accepted custody and Witness startup evidence;
actual isolated dashboard create/correct/read/refresh/restart. No real personal
record is a verification fixture. Missing dependency leaves503 with precise cause.

## Single Owner approval requested

`APPROVE_OPTION_B_OWNER_ENROLLMENT_V1`: authorize the above versioned same-user
Owner-declaration source/custody amendment and subsequent controlled enrollment
of one application-specific Windows Hello Owner credential, distinct DPAPI runtime
keys and canonical Identity source/public pins, subject to independent acceptance
and existing Witness/Human Gates. No real personal-data enrollment, cloud/ACL/service
change or external submission is included.

This is the single concrete Owner decision needed to continue that enrollment
implementation. It does not mean a live runtime is already composed or accepted.
Remaining work after approval is technical integration and independent verification
above; a newly discovered privileged/cloud decision must not be silently authorized.

## Evidence for this bounded change

31 focused assertion tests passed,0failed,0skipped: exact scope substitutions,
wrong key/signature/credential, expiry, missing UV/UP, RP/origin substitution,
duplicate JSON, counter rollback, backup/extension flags and malformed lengths.
They use ephemeral in-memory synthetic keys, not operational credentials. Earlier
test invocation failed31 cases due to a constant typo; corrected and rerun.
Repeated proof verification intentionally returns the same result: it demonstrates
why the Kernel nonce transaction is still required. No live Family operation,
refresh/restart acceptance or credential enrollment is claimed.

Source references: owner_identity_assertion.py; identity_mutation_source.py;
identity_evidence_authority.py; identity_protected_revision.py;
family_identity_gateway.py; orchestrator_kernel.py; local_case_host.py;
case_analysis_kernel_dispatch.py; runtime_activation.py; canonical checkpoint
Option B decision; docs/f07-runtime-activation-preparation-20261026.md.
Native API reference: https://learn.microsoft.com/en-us/windows/win32/api/webauthn/nf-webauthn-webauthnisuserverifyingplatformauthenticatoravailable
