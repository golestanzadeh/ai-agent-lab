# Owner Broker rollback-finality gap: bounded implementation decision (2026-11-23)

Status: READ_ONLY_CODE_REVIEW_COMPLETE / DESIGN_ONLY / INACTIVE. Reviewed exact HEAD 5a8d3ff7d54e029dfaea807206d47e623f5b292b. This is not an operational C09 acceptance or permission to deploy.

## Verified paths
- owner_identity_broker.py _save -> orchestrator_kernel.py _store_identity_payload writes owner-broker:v1:<deployment> in existing identity_kernel_state and appends IDENTITY_PROTOCOL_RECORDED. No external Witness checkpoint is required for this write.
- orchestrator_kernel.py _verify_identity_protocol_state verifies locally consistent rows and audit events, not independent freshness of a fully rolled-back Kernel database.
- orchestrator_kernel.py _require_durable_owner_binding fails closed for a present enrolled Owner profile without a bound verifier; the owner-absent path retains legacy behavior. The deletion/substitution tests do not cover a coherent rollback of owner profile AND audit history.
- orchestrator_kernel.py witness_identity_checkpoint consumes an Identity checkpoint receipt, binds the current Identity logical/audit cut and a Kernel PENDING event, and uses concrete Custodian/GCS verification before RELEASED. verify_identity_witness_state compares the external chain to the persisted Identity deployment last_cut and predecessor. It does not explicitly bind Owner Broker enrollment/revocation state to an externally finalized security cut.
- Existing witness record schema, epoch/sequence, restore transition, and crash rules are frozen; do not change them casually.

## Minimal required contract before code
1. Define a versioned canonical *security-control cut* commitment covering the Owner Broker deployment/profile identifier, enrolled credential reference, revocation generation/status, and the exact Kernel audit prefix/event identity. No personal values, private keys, or raw assertions in GCS.
2. Persist the intended cut and pending/finalized state atomically with each security-sensitive Owner transition in the existing Kernel SQLite transaction. An event alone is not external finality. Do not call provider I/O while holding SQLite writer lock.
3. Reuse the existing single global Witness reservation/conditional-create, Custodian verification, readback, and recovery state machine, with an independently reviewed mapping of this cut into the *existing* authenticated witness commitment fields. Prove that it does not conflict with the frozen Identity composite and audit checkpoint semantics. If it cannot fit without changing the witness schema, stop for contract review rather than inventing a new protocol.
4. Before a new protected Owner authorization or Family request, require a current externally verified security-control cut. On pending, outage, missing evidence, rollback or divergent cut: fail closed. An already committed transaction's GET/FINALIZE recovery must remain available under its original receipt and independent finality.
5. Startup/restart must compare the independently verified latest security cut with the durable local Owner profile and audit history; absence of an Owner row must not silently re-enable legacy mode for a deployment known externally to be enrolled. Owner-authorized RESTORE must advance the existing witness epoch and reconcile this cut explicitly, never silently reset enrollment or revocation.
6. The current Owner Broker has no reviewed operational revoke/rotate entrypoint. Do not fabricate one as part of this fix. Define coverage for enrollment and any existing real revocation path; defer hypothetical rotation until authorized.

## Focused negative acceptance, synthetic only
- Enroll -> externally finalize cut -> restart raw Kernel -> remove/rollback entire Kernel SQLite (including audit) -> verify denial before new issuance, even when local Owner row is absent.
- Revocation cut finalized -> restore an earlier locally consistent enrolled snapshot -> deny, including across restart.
- Crash before external append, after append before local finalization, and after finalization: exact idempotent recovery; no early success.
- Provider unavailable, invalid/forked/gapped chain, wrong Custodian proof: deny.
- Identity committed recovery GET/FINALIZE remains possible without minting fresh Owner authority.
- Legacy deployment with no external enrolled cut keeps its explicit legacy behavior; no fabricated enrollment.
- Independently review exact SHA and run bounded tests. Do not activate Family or generate operational credentials before existing Human Gates and C09 acceptance.

## Decision
A one-line hook from Owner Broker _save to witness_identity_checkpoint is NOT valid: that API requires an Identity checkpoint receipt and assumes Identity audit-cut semantics. Next work is a small contract mapping and one failing synthetic rollback test, then minimal implementation only if existing protocol accommodates it. No new orchestrator, database, service, or trust root. No Codex.

## Source-to-contract reconciliation — 2026-11-23 (no runtime change)

Read-only inspection of the current repository confirms the precise mismatch:
- `owner_identity_broker.begin_enrollment` and `_finish_enrollment` call `_save`, which stores the Owner row in Kernel SQLite. Neither stages nor finalizes an external Witness record. No accepted operational revoke/rotate entrypoint was found in this Broker.
- `OrchestratorKernel._require_durable_owner_binding` checks the Owner row only when present. A coherent rollback of the entire Kernel SQLite and its local audit can therefore remove the evidence that Option B was enrolled; the existing two tamper tests are narrower.
- `verify_identity_witness_state` authenticates the entire external chain and compares its final `identity_head` with `H(state['last_cut'])`. `last_cut` is the Identity logical/audit composite, not an Owner Broker control cut.
- `stage_identity_audit_checkpoint` derives its Witness `identity_head` from the Identity response and its `kernel_head` from the `IDENTITY_AUDIT_CHECKPOINT_PENDING` event. `witness_identity_checkpoint` requires an Identity checkpoint receipt and release authority; it is not a generic Owner-control finalizer.
- `c09_witness_protocol.WitnessRecord.validate_public_schema` permits only `COMMIT` and `RESTORE`; `owner_authorization_digest` is mandatory only for `RESTORE`. Reusing that field for enrollment or revocation would violate the frozen contract. A new record type or reinterpretation of `identity_head` cannot be assumed accepted.

Decision: `EXISTING_R1_R2_PASS_PRESERVED / OWNER_CONTROL_CUT_UNMAPPED / NO_IMPLEMENTATION_AUTHORIZED`. Do not repeat R1/R2, change Witness schema, add a second authority, or claim a fix from local audit integrity. The smallest next engineering deliverable is an explicit mapping of Owner-control finality to the existing global reservation and authenticated Witness fields, with preservation of the Identity composite and restore semantics; if no non-conflicting mapping exists, obtain a narrowly scoped contract amendment before implementation. Only then add one synthetic coherent-rollback negative test and its minimal code remedy. Operational Family remains inactive.
