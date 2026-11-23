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

## Independent review correction

Candidate b4997f3f13982ff892c08a36d32968b62a47b8f2: INDEPENDENT_FAIL,
ECDSA high-S twin accepted with a different proof_digest. Corrected by strict DER
and P-256 scalar bounds plus canonical low-S encoding before proof commitment.
Both valid native S representations now yield one verified proof identity; no
native high-S output is rejected merely for its S representation. Added twin
canonical-equivalence and four invalid scalar-boundary tests. Final focused
command includes assertion and documentation tests:54passed,0failed,0skipped,
exit0. Exact successor independent review pending; no live authentication or
operational acceptance implied.

## Exact successor independent acceptance

Separate read-only reviewer /root/c09_architecture_independent_review returned
INDEPENDENT_PASS / INACTIVE at858b8b3a17cb26e88affd2fdca28ecfe1dee5cce.
Initial b4997f3 finding severityMEDIUM, with no signed-scope bypass. Exact-archive
commands: assertion pytest36passed,exit0,0.61s; documentation pytest18passed,
exit0,0.99s; independent ECDSA twin probe accepted both forms with equal proof
digest,exit0; git diff --check b4997f3..858b8b3 exit0. No residual bounded defect.
This accepts only the verifier/proposal, not enrollment or the operational runtime.
Kernel nonce issuer/atomic consumer, native enrollment interoperability, reviewed
source-kind implementation, accepted custody/Witness binding and actual composition
remain technical/operational acceptance work after the specified Owner decision.

## Approved implementation increment — 2026-11-23

Owner approval APPROVE_OPTION_B_OWNER_ENROLLMENT_V1 is now recorded in the canonical
checkpoint; the proposal's earlier approval-required status is historical. Native
Windows Hello registration/assertion ABI v1 and closed P-256 registration parsing
are implemented in owner_identity_native.py. A second required-UV assertion verifies
possession of the extracted registration key. No hardware attestation is claimed.
The actual ceremony has NOT been run. Native cancellation/denial propagates without
creating a public pin. The bootstrap entry point accepts no HTTP identity/key input.

owner_identity_broker.py uses only existing Kernel identity_kernel_state, atomic
execution and audit verification. Nonces/approvals are committed together, exact
manifest/task/case/year/run permissions and externally verified deployment are
rechecked, same-proof recovery returns the original approval and changed-proof
replay fails. This is not live Identity genesis or a Witness acceptance artifact.
owner_identity_keys.py provisions separate Kernel/Identity DPAPI keys only through
explicit enrollment; load never regenerates missing keys. Production keys have
not been generated. Isolated real DPAPI tests verified role separation/readback
and denied wrong Owner/role or missing keys.

54 focused tests passed (18 Broker/native/custody plus36 existing proof tests),
0failed,0skipped,exit0; includes actual canonical Kernel/isolated native IPC fixture,
concurrent approvals, rollback, replay, restart, lost response, audit deletion,
registration substitutions and DPAPI. Initial canonical-state digest and DPAPI
argument-order failures were corrected and rerun. These are technical tests, not
actual Windows Hello or live Family acceptance. Accepted27/269 suites not repeated.

After independent exact-SHA review, the Owner's native action is to open PowerShell
in this repository and run:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
& 'C:\Users\rezag\ai-agent-lab\.venv\Scripts\python.exe' -m agent_lab.owner_identity_broker --enroll
```

Confirm only the AI-Tax-Agent Windows Hello dialogs. Do not send PIN/password/key
material to chat. The flow requests two verifications, creates application keys,
and records ENROLLED_LOCAL only after successful proof verification. Cancellation
leaves pending enrollment and Family disabled. No real person data is entered.
Do not run before the new exact-SHA security review. Live source/reference binding,
Option B runtime composition and accepted independent Witness/Custodian evidence
remain required; this increment does not complete them or claim Family persistence.

## Independent findings, source integration and genuine activation prerequisite

Candidate51f43cfdac1232ed3e5724c3e0c86ec0be179c24 was INDEPENDENT_FAIL:
HIGH fabricated deployment/store UUID fallback; HIGH approval recovery failed after
lease expiry. Removed the fallback: native entry requires exactly one canonical
ACTIVE deployment/store and its current independently verified Witness record.
No accepted binding means no prompt/pin/key. Display exact scope and canonical
paths before a permitted ceremony. Committed same-proof readback now verifies
its immutable signature/commitment without a new issuance lease/manifest decision;
it returns only the old receipt. Receipts retain original issue/expiry and deterministic
execution authorization reference. No lifetime extension or new nonce is implied.

The Owner approval already given is valid; no repeated approval is requested.
The earlier CLI directions are now conditional: a fresh standalone CLI cannot
invent an external-verification adapter or mark a head verified. Do NOT run it as
an operational bypass. The existing governed runtime must first supply the accepted
canonical deployment and independently verified Custodian/Witness binding. There
is no automatic new genesis or synthetic trust promotion in this increment.

Read-only actual application storage inspection2026-11-23: identity.sqlite absent;
canonical Kernel identity_kernel_state has0rows/0ACTIVE enrollment artifacts;
new Kernel/Identity DPAPI files absent. Therefore the real application cannot yet
satisfy that existing protected enrollment/finality requirement. Windows Hello
has not been invoked and no production key generated. Existing Kernel/Identity
operational architecture source-boundary/genesis/Witness clauses and this approved
amendment require failure closed. This is an actual operational prerequisite,
not C09 globally blocking ordinary development or a reinstated four-principal target.

Implemented identity_owner_source.py optional versioned source inside canonical
Identity SQLite: actual immutable content, scoped Owner proof and accepted canonical
enrollment key; content substitution denial; case/year/subject/run/operation and
expiry checks; audit/MAC deletion detection; idempotent identical staging; revocation
revalidation inside the existing Identity writer transaction. Document sources keep
their original case/provider/root restriction. Only the concrete pinned Owner source
kind may use its canonical Identity root. No browser request selects a source root.
Staging is evidence/audit only and cannot mutate persons or logical identity head.
The existing PREPARE/COMMIT path remains the only domain writer, consuming its
one-time authorization with domain/head/audit/receipt. New source table is a
versioned optional same-database extension, not another database. Live enrollment
or a request-controlled source configuration is NOT installed by these changes.

A trusted native review dialog now displays exact operation/case/year/subject and
confirmed input before required Windows Hello verification; the dialog alone never
grants authority. The actual Family app remains unbound until its source, accepted
canonical enrollment/Witness and client composition exist. No real dashboard
refresh/restart acceptance may be inferred from isolated synthetic SQLite tests.

## Source review corrections: authenticated delivery, distinct assertion key

Candidate7365841b916302d5a4f82af222f4a9fae1dffc61 was INDEPENDENT_FAIL:
CRITICAL raw-assertion staging bypassed the committed Kernel approval; HIGH
conflation of the new Windows Hello credential with the continuity/restore key;
MEDIUM repeat authorization conflicted with immutable scope reference.

Corrections: source staging no longer accepts raw intent/assertion. It requires
closed ai-tax-agent.owner-approval-delivery/1, signed by Identity's EXISTING pinned
Kernel key under a distinct domain. The Kernel exporter verifies the authoritative
ledger's APPROVED nonce, current exact scope, lease and nonrevoked Owner credential
before signing. Delivery binds the actual approval/reference, exact intent/proof,
original expiry, deployment/store and distinct Windows Hello credential pin. Identity
verifies the Kernel signature and Owner proof independently, then stores that
signed pin/proof/approval digest with the immutable source bytes in canonical SQLite.
No Kernel DB is opened by Identity. A Windows Hello key is NOT required to equal
or replace the continuity/restore key. The earlier equality requirement was a defect,
not an accepted security rule. The distinct pin is authorized by the existing Kernel
boundary; a raw caller-provided key, hash or class is still insufficient authority.

Execution authorization slots are now permanently one-per-exact-scope: repeated
pending issue returns the same nonce; an expired or consumed slot requires an
explicit new Task/Manifest successor, never a new approval silently overwriting the
same immutable reference. This restriction preserves bounded execution and history.
Committed receipt readback remains separate and does not authorize fresh use.
Kernel mutation issuance also rechecks recognized Owner approval scope, expiry and
credential revocation before fresh PREPARE/COMMIT; recovery/finality paths retain
their existing semantics. Public signed proof bytes are durable for source delivery
and lost-response recovery; person values are not stored in the Kernel ledger.
No source revocation/rotation administrative authority is fabricated or activated.

Actual application composition remains unavailable because the canonical deployment/
Identity database/Witness enrollment prerequisites are absent. No actual native
ceremony has occurred; do not execute the old standalone command without an accepted
current governed binding. Owner approval is already granted and needs no repetition.
Final exact-SHA independent re-review follows these corrections. No operational
acceptance, real-person write, service, ACL, credential or cloud change occurred.

## Final controlled handoff — 2026-11-23

Final mission status: BLOCKED_WITH_EXACT_UNRESOLVED_DEPENDENCY.
Stop: OWNER_CONTROLLED_STOP / QUOTA_15_PERCENT. No operational acceptance.
Exact final implementation/review candidate: bf75475d3ba073f0a431fb6fc3f7e6a8b8c79e35.
Separate read-only reviewer /root/c09_architecture_independent_review returned
INDEPENDENT_FAIL. Exact archive87tests passed,0failed,0skipped,exit0,15.06s;
diff-check exit0. Worker same87test selection passed,exit0,13.49s. Earlier atomic
regression selection105passed before the final Kernel hook; it is not claimed as
an exact-final compatibility run. Accepted Family27/269 suites were not repeated.

Remaining F05 HIGH: approved_source_evidence checks current approval/revocation
and signs outside Kernel.atomic_execution. Concurrent revocation can linearize
between the check and signing; Identity could stage stale-authorized bytes before
Kernel's later mutation check rejects them. Repair must load/check/sign in the
existing atomic Kernel boundary and prove ordering with a barrier concurrency test.
Remaining F06 MEDIUM: exact-SHA integration tests must exercise the new Kernel
Owner approval hook at both PREPARE/COMMIT (valid, revoked, expired, substituted),
existing non-Owner authorization and GET/FINALIZE recovery. Current direct Identity
source tests do not supply that evidence. No fix or new test started after the
Limit Guard stop; these are real unresolved findings, not accepted residual risks.

Actual localhost8766 read-only readback: root200; /family/persons503 with
FAMILY_AUTHORIZED_RUNTIME_UNAVAILABLE. No Windows Hello ceremony, production key,
protected enrollment, source activation, real taxpayer mutation or application
restart occurred. Live refresh/restart Family persistence is NOT verified. Isolated
canonical SQLite source/PREPARE/COMMIT/reopen behavior is verified only as synthetic
technical evidence. Source factory and Option B transport/application composition
remain unwired. Do not run the earlier enrollment command at this revision.

Owner approval remains valid; do not request it again. After a fresh admitted
execution, repair F05, supply F06 evidence and obtain independent acceptance on the
new exact SHA before continuing remaining factory/Option B runtime integration.
Operational enrollment additionally requires the existing accepted canonical
Identity deployment/store and independent Custodian/Witness binding. Actual
canonical metadata currently has no such enrollment; no UUID/credential/config flag
may stand in for it. No four-principal target reinstatement or new cloud decision
is made. The native Owner verification action becomes executable only once that
governed binding and technical security acceptance exist, not now.

Capacity source codex_app_server: initial2026-11-23T14:30:38.786256Z58%/48%; final
observed2026-11-23T15:02:58.133527Z15%five-hour/41%weekly, resets18:33:47Z and
2026-11-25T09:13:38Z. Observation15:00:08.371783Z24%/43% returned
CAUTION_CHECKPOINT_ONLY even for CHEAP; development stopped then, existing review
finished, only controlled documentation/publication followed. Platform quota was
not bypassed; observed differences are not exclusive per-task billing. Preserve
all original dirty UI/Drive files. Final recovery documentation commit and remote
readback follow; no active OPEN_ITEMS row closes and no Human Gate is granted.

## F05/F06 bounded security remediation — 2026-11-23

Owner authorized only atomic approval export and exact mutation-hook verification.
Baseline7cade479733a54c9e322c7467024e4839b074b3c recovered and fetched remote aligned;
all pre-existing dirty UI/Drive files preserved. Initial authenticated app-server
observation19:25:44.519003Z100%five-hour/41%weekly, BOUNDED15/5 admitted; reserve15.

F05 production correction is limited to approved_source_evidence: load/check current
Owner approval/credential/scope and sign delivery inside existing Kernel.atomic_execution
(BEGIN IMMEDIATE). Original receipt/reference, immutable scope slot, proof, audit and
lost-response semantics unchanged. Monotonic time spent waiting for the lock counts
against the original approval lease; queued export cannot issue expired evidence.
No new authority, table, protocol, credential or operational binding introduced.

New focused test_f07_owner_authorization_integration.py reuses existing isolated
canonical Kernel/Identity SQLite, actual native Named Pipe client/dispatcher and
existing synthetic Custodian/Witness test fixture. No authorization mock is used:
only fixture dependency injection, signing/transport observation, controlled clock
for pre-dispatch expiry denial, and deterministic concurrency barriers. Native
Owner enrollment and operational acceptance are not simulated or claimed.
F05 barriers prove credential and manifest revocation cannot enter its write
transaction until export signing finishes; subsequent export denies without signing.
Queued-lock lease expiry also denies. F06 actual PREPARE/COMMIT accept valid Owner
authority and reject revoked/expired/substituted subject scope before transport.
Existing non-Owner authorization still commits. Actual committed GET/FINALIZE,
Witness settlement and restart readback remain available after Owner revocation
and real lease expiry, without issuing another grant or domain mutation.

Worker focused three-file command44passed,0failed,0skipped,exit0,34.65s. Final new-test
and documentation verification recorded below after execution. Initial test harness
errors (Identity context-manager assumption and inconsistent simulated IPC clock)
were corrected; actual lease expiry is now used in the recovery test. Independent
exact-SHA review pending, so F05/F06 are not yet closed. Existing27Family/269wire
campaigns not repeated. No real data, native ceremony, key/pin/genesis creation,
source/Family activation, service/ACL/IAM change or external submission occurred.
