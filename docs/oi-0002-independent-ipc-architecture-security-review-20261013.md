# OI-0002 independent IPC architecture/security review — 2026-10-13

Review identity: `/root/oi0002_ipc_independent_review`

Reviewed commit: `dcfb6ab712b74b65b10a2e5206795061dce07c95`

Reviewed artifact: `docs/oi-0002-kernel-identity-ipc-adr-20261013.md`

Decision: **`INDEPENDENT_ARCHITECTURE_FAIL`**

## Independence and scope

This review was performed in the dedicated clean worktree `C:\Users\rezag\ai-agent-lab-oi0002-ipc-review` on branch `codex/oi0002-ipc-independent-review-20261013`. The reviewer did not author or modify the ADR, implementation, protected data, service configuration, ACLs, accounts, tasks, databases, or Windows state. The immutable review target was the branch baseline and HEAD shown above.

The review uses only the frozen C01–C13 closure matrix. It inspected the accepted REMEDIATION-02 custody/four-principal model, Persistence Contract v1, Kernel continuity/restore contracts, current Identity implementation and operations contract, Constitution/Human Gates, and the exact ADR. Prose was treated as a proposed contract, not proof of implementation or operational effectiveness.

## Executive conclusion

The selected local named-pipe direction is compatible with C01–C03, and the ADR correctly requires first-instance creation, local-only message pipes, exact-SID peer checks, impersonation cleanup, a closed operation surface, durable prepare/idempotency records, Kernel coordination, and real-principal fault testing. It is not yet safe to implement because six contract defects leave C04–C09/C11 unenforceable or ambiguous. The defects permit an Identity commit without durable Kernel PENDING, a stale or revoked authorization to commit, Kernel finalization while the external Identity anchor is not durable, cross-case replacement through a case-scoped whole-database restore, undetectable coordinated rollback, and ambiguous canonical bytes/framing at the replay boundary.

## Findings

### F01 — CRITICAL — Identity COMMIT has no proof of durable Kernel PENDING

- Exact ADR sections: **Mutation protocol**, steps 3–4 (lines 121–122); **Crash, restart and reconciliation table**, “After PREPARE, before Kernel PENDING” and “After Kernel PENDING, before Identity COMMIT” (lines 133–134).
- Violated invariant: C05 requires `PENDING → Identity Commit → COMMITTED` with “no unbound commit”; C01 requires the Kernel to remain the sole coordinator.
- Reproducible counterexample: authenticate as the real `AITaxKernel` token, send a valid `PREPARE_MUTATION`, deliberately skip the Kernel continuity reservation, then send `COMMIT_MUTATION` for the prepared transaction. The ADR requires Identity only to find the exact PREPARED row. Identity cannot observe or verify the claimed Kernel PENDING record and therefore commits an unbound mutation. The same path is available after a Kernel DB write failure or to a confused-deputy call site running under the legitimate Kernel service token.
- Minimal correction: define a versioned, non-forgeable continuity-reservation proof bound to transaction ID, request digest, expected/projected epoch/head and deployment, produced only after the Kernel PENDING transaction is durable. Define how Identity verifies it without receiving direct Kernel-DB access and how issuance/revocation/recovery preserve the four-principal custody model. `COMMIT_MUTATION` and `COMMIT_RESTORE` must require and durably bind that proof.
- Required negative/regression test: valid PREPARE followed by COMMIT with no reservation, a fabricated reservation, a reservation for another transaction/head/deployment, and a reservation whose Kernel write was faulted before commit must all leave Identity domain/audit state unchanged. An exact durable reservation must commit once and reconcile across both process restarts.

### F02 — HIGH — Authorization is not revalidated at the commit/use boundary

- Exact ADR sections: **Authorization and transaction identity** (lines 101–113); **Mutation protocol**, steps 1–4 (lines 119–122); **Backup, restore and rollback** (lines 148–155).
- Violated invariant: C03 requires exact authorization scope; C08 requires expired, revoked and consumed restore authorization denial; Constitution Articles 10 and 15 prohibit bypass/reuse of Human Gates.
- Reproducible counterexample: PREPARE while the manifest and authorization are valid, then revoke the manifest/authorization, activate the Kill Switch, or let `expires_at` pass before COMMIT. Step 4 requires only the exact PREPARED transaction, so COMMIT can apply the mutation. For restore, revocation after PREPARE but before file replacement has the same gap; consumption is deferred until after replacement.
- Minimal correction: specify an atomic commit-time authorization decision. Revalidate current Kill Switch, manifest, task/actor/role/capability, immutable evidence status, expiry/revocation and Human Gate immediately before mutation/replace; bind the decision version to the prepared plan. For a one-time restore gate, define reservation and atomic consume semantics that prevent both post-revocation use and duplicate replacement while remaining restart-safe.
- Required negative/regression test: revoke/expire/consume or alter every authorization dimension after PREPARE and before COMMIT, including during restart reconciliation. Every case must deny without mutation or restore; an exact still-valid authorization must remain idempotent.

### F03 — HIGH — DB commit can become Kernel COMMITTED before the external audit anchor is durable

- Exact ADR sections: **Mutation protocol**, steps 4–6 (lines 122–124); **Crash, restart and reconciliation table**, anchor and response rows (lines 136–137).
- Violated invariant: C05 forbids false COMMITTED state; C06 binds every accepted Identity state to the exact Kernel head; C11 requires reconstructable, immutable audit evidence.
- Reproducible counterexample: let the SQLite mutation commit and the pending anchor receipt persist, then make external-anchor replacement fail. The database transaction is already `COMMITTED`. `GET_TRANSACTION` is specified to return the exact durable committed result, and nothing says the response/finalization is blocked on receipt consumption and verified anchor publication. Kernel can therefore finalize a head whose required external anchor is absent or stale.
- Minimal correction: add an explicit durable `ANCHOR_PENDING`/not-finalizable state, or define `COMMITTED` to mean DB plus verified external anchor publication. `GET_TRANSACTION` must not return a finalizable result until the receipt is consumed and the anchor is reread/verified. Define the terminal behavior for repeated publication failure.
- Required negative/regression test: fault anchor create, flush, replace, directory durability and receipt consumption after DB commit. Kernel must remain PENDING; reads/writes must fail closed as specified; restart may publish exactly once and only then permit Kernel finalization. A stale, missing, substituted or replayed receipt/anchor must never finalize.

### F04 — CRITICAL — Whole-database backup/restore is incorrectly authorized as case/year scoped

- Exact ADR sections: **Frozen wire envelope**, required `case_id`/`tax_year` (lines 68–80); **Backup, restore and rollback** (lines 146–155).
- Violated invariant: C02 independent protection, C03 exact scope, C08 exact authorized restore, and the repository case-isolation rule. Persistence Contract v1 specifies one SQLite database per deployment with case isolation, not one database per case.
- Reproducible counterexample: deployment DB contains cases A and B. Create a consistent SQLite backup while both exist, but authorize/bind `PREPARE_RESTORE` as case A/year only. `COMMIT_RESTORE` atomically replaces the whole live DB, thereby also rolling case B backward or replacing it without case-B authority. The authenticated Kernel becomes a confused deputy even though every envelope field validates.
- Minimal correction: choose and freeze one scope: (a) deployment-wide physical backup/restore with authorization and evidence explicitly binding the complete deployment/store identity and all affected case generations (not a single case/year), or (b) a case-scoped logical export/import that cannot replace unrelated rows. Align backup digest, Human Gate, audit, generation and recovery artifact semantics with that scope.
- Required negative/regression test: populate at least two cases/years, authorize only one, and prove the operation is rejected before replacement or that the unrelated case is byte/lineage invariant under a reviewed logical restore. Add substituted case/year/deployment and partial-scope backup tests.

### F05 — CRITICAL — Coordinated rollback detection is circular and cannot work as specified

- Exact ADR section: **Backup, restore and rollback**, final paragraph (line 155); **Security properties and residual decisions** (line 187).
- Violated invariant: C09 explicitly requires single-store and coordinated rollback to fail closed; C06 requires exact Kernel-bound generation/head.
- Reproducible counterexample: take an internally consistent snapshot of Kernel DB/continuity state and Identity DB/anchor at generation N. Advance normally to N+1. Stop both services and replace both recovery sets with the N snapshots. On startup, the rolled-back Kernel says N and the rolled-back Identity says N, so the claimed “monotonic Kernel generation/head binding” compares equal and detects nothing. The external Identity anchor is part of the same rolled-back set and adds no independent freshness.
- Minimal correction: bind the current generation/head to a separately protected non-rollbackable or independently retained freshness authority outside the coordinated Kernel+Identity recovery set, with explicit custody, backup, recovery and availability behavior. Alternatively narrow C09 only through an Owner-approved matrix change; the reviewer cannot do so.
- Required negative/regression test: snapshot and restore both Kernel and Identity stores/anchors together after advancing a generation. Startup must deterministically detect the old pair without relying on either rolled-back store. Also test Kernel-only, Identity-only and mixed-generation replacement.

### F06 — HIGH — “Canonical JSON” and frame boundaries are not precise enough for security identity

- Exact ADR sections: **Frozen wire envelope** (lines 64–81); **Authorization and transaction identity** (line 111); **Required implementation verification** (line 168).
- Violated invariant: C04 requires exactly one logical outcome per transaction and mismatch denial; C03 requires a closed default-deny contract.
- Reproducible counterexample: two conforming implementations choose different plausible canonical forms for Unicode escaping, object-key ordering, negative zero/number handling, timestamp normalization, or length interpretation. They compute different request digests for the same semantic object, or accept different byte strings under one transaction. Message-mode pipes also expose message boundaries while the ADR adds a length prefix but does not define zero length, whether the prefix is included in the 65,536-byte maximum, multi-read `ERROR_MORE_DATA`, or multiple frames per pipe message.
- Minimal correction: normatively select and profile one canonicalization algorithm (for example an explicit RFC 8785-compatible subset), define exact UTF-8 and timestamp normalization, digest input bytes, response-digest input, length bounds, pipe-message/frame relationship, read loop, EOF/`ERROR_MORE_DATA`, and connection disposition after a malformed frame.
- Required negative/regression test: golden byte vectors plus alternate key order, escapes, Unicode normalization, duplicate keys, integer edge cases, zero/oversize lengths, prefix/body split reads, `ERROR_MORE_DATA`, concatenated frames, trailing pipe-message bytes and restart replay. Every implementation must produce the same digest or reject before transaction creation.

## Fifteen-point invariant matrix

| Security-critical point | Exact ADR section | Enforceability / precision | Realistic attack or failure | Required negative evidence | Result |
| --- | --- | --- | --- | --- | --- |
| First-instance / squatting | Transport authentication 1–7 | Enforceable direction; exact Win32 error/fatal lifecycle should be pinned in implementation | Earlier pipe instance blocks service or lures client | Squatter under wrong SID; same-name first instance; client sends no payload before server-token PASS | Adequate for ADR |
| Exact-SID mutual auth using actual tokens | Transport authentication 2, 4–7 | Binary `TokenUser` comparison is explicit; server check is query-only before payload | Wrong account, PID reuse, forwarded handle | Wrong SID, anonymous, inaccessible token, process exit/PID reuse, server-token query failure | Adequate for ADR |
| Impersonation / `RevertToSelf` | Transport authentication 4 | `finally` cleanup is explicit; implementation must prove no parsing/domain work while impersonating | Exception leaves service thread impersonating Kernel | Fault every call after impersonation and assert thread token restored before reuse | Adequate for ADR |
| DACL / remote rejection | Transport authentication 1–2 | Direction is clear; exact descriptor/inheritance verification remains implementation evidence | inherited/extra ACE or remote connection | Effective access under all four principals, unrelated user, Administrator, remote | Adequate for ADR |
| Versioned default deny | Default-deny allowlist; Compatibility | Closed version/type/operation/field model is explicit | downgrade or generic dispatch | unknown/mixed version, field, capability, method and operation/capability pair | Adequate for ADR |
| Canonical framing / replay | Frozen wire envelope; Authorization | Under-specified canonical bytes and pipe framing | digest disagreement or alternate-byte replay | Golden vectors and malformed/split/concatenated frame suite | **F06** |
| Authorization-context integrity | Authorization; Mutation; Restore | Stored context is specified, but commit-time freshness/use is not | revoke/expire after PREPARE, then COMMIT | stale/revoked/Kill-Switch/consumed-after-PREPARE suite | **F02** |
| PREPARE→PENDING→COMMIT→COMMITTED | Mutation protocol | Ordered prose exists, but Identity cannot enforce PENDING prerequisite | authenticated Kernel path skips reservation | COMMIT without exact durable reservation | **F01** |
| Proof of durable Kernel PENDING | Mutation steps 3–4 | No proof field, issuer, verification or custody design | Kernel DB faulted before commit; Identity still commits | fabricated/missing/wrong-head reservation proof | **F01** |
| Crash/idempotency/reconciliation | Crash table | Good boundary inventory, but anchor-finality and stale auth are unresolved | DB committed, anchor absent; retry finalizes early | fault each durable boundary and repeat after both restart orders | **F02/F03** |
| SQLite vs external anchor sync | Mutation step 5; crash table | Receipt idea is sound but finalizable state is ambiguous | permanent anchor replace failure after DB commit | anchor/receipt fault matrix and finalization denial | **F03** |
| Epoch/head coordinated rollback | Restore final paragraph | Single-store comparison is plausible; coordinated rollback claim is impossible with only rolled-back authorities | restore old consistent Kernel+Identity pair | coordinated snapshot rollback after generation advance | **F05** |
| Restore atomicity/generation/one-time gate | Restore steps 1–4 | “atomic replace” across DB+anchor is unspecified; scope and gate freshness unsafe | partial file replace, cross-case replacement, revoked gate | two-case restore, each file/receipt boundary, revoke-after-PREPARE, duplicate COMMIT | **F02/F04** |
| Four-principal operational tests | Required implementation verification | Explicit and aligned with accepted custody evidence | self-client, Recovery direct call, admin/unrelated access | actual-token positive/negative matrix plus store effective access | Adequate for ADR |
| Kernel sole coordinator | Decision; lifecycle; mutation | Topology is explicit, but unproven PENDING allows Identity to accept an uncoordinated commit | legitimate Kernel-token confused deputy | trace every route; reject direct Identity initiation and no-reservation COMMIT | **F01** |

## Targeted adversarial probes required after correction

- TOCTOU: change token/process state before first sensitive byte; change manifest, Kill Switch, task, evidence and restore gate between PREPARE and COMMIT.
- Unauthorized commit/confused deputy: valid Kernel SID but no durable reservation; wrong transaction/head proof; case-A authority attempting whole-store replacement containing case B.
- Restart replay: each crash boundary under both restart orders, changed request with reused transaction ID, exact retry before/after expiry, anchor receipt replay and restore COMMIT replay.
- Stale/revoked authorization: revoke or expire every permission/Human Gate dimension after PREPARE and while either service is down.
- Coordinated rollback: restore a previously valid matching pair of both stores and anchors after a later committed generation.
- Incomplete recovery: unavailable freshness authority, missing/stale anchor, partial restore replace, preserved pre-restore artifact unavailable, or ambiguous receipt must fail closed without silent reinitialization.

## C01–C13 disposition

| Criterion | Architecture-review disposition |
| --- | --- |
| C01 | FAIL pending F01; topology says Kernel-only but COMMIT prerequisite is not enforceable |
| C02 | PASS at ADR topology level; operational preservation remains future evidence |
| C03 | FAIL pending F02/F06; transport design is acceptable, authorization/use and byte contract are incomplete |
| C04 | FAIL pending F06 |
| C05 | FAIL pending F01/F03 |
| C06 | FAIL pending F03/F05 |
| C07 | FAIL pending F02/F03; table is comprehensive but cannot safely converge in these states |
| C08 | FAIL pending F02/F04 and precise multi-file restore recovery semantics |
| C09 | FAIL pending F05 |
| C10 | No architecture regression identified; implementation routing remains unproven |
| C11 | FAIL pending F03; final audit-anchor durability is not a prerequisite to Kernel finalization |
| C12 | FAIL pending F06; version closure is good but canonical public bytes are not frozen |
| C13 | BLOCKED by this architecture FAIL; no implementation or operational campaign is authorized |

## Verification record

The following read-only checks were run against the exact reviewed SHA before this report was written:

- `git status --short --branch` — exit 0; clean dedicated review branch.
- `git rev-parse HEAD` — exit 0; `dcfb6ab712b74b65b10a2e5206795061dce07c95`.
- targeted repository/document/contract inspection with `Get-Content` and `rg` — exit 0 except one PowerShell wildcard invocation rejected by Windows path parsing; it changed no state and was replaced by explicit paths.

Final verification:

- `python -m pytest tests/unit/test_documentation_index.py -q` — exit 0; `10 passed in 0.30s`.
- PowerShell static count of frozen closure-matrix rows matching `^\| C\d{2} \|` — exit 0; `13`.
- PowerShell static count of requested security-point rows in this report — exit 0; `15`.
- First `git diff --check` — exit 2, reporting one added blank line at EOF in `CURRENT_STATE.md`; the review record was moved to the top and the whitespace defect corrected.
- Final `git diff --check` — exit 0.

Starting authenticated telemetry supplied by the supervisor was measured `2026-10-13T08:40:58.723653Z`: five-hour 86% remaining, reset `2026-10-13T13:19:11Z`; weekly 98% remaining, reset `2026-10-20T08:19:11Z`; existing Limit Guard `BOUNDED(15/5)` returned `RUN_OPERATION_FITS`.

The ending authenticated read used the existing reader with explicit executable `C:\Users\rezag\AppData\Roaming\npm\codex.cmd`: `PYTHONPATH=src; python -c "...read_codex_usage(executable=...); write_snapshot(...)..."` — exit 0. Readback from `.runtime/usage/CODEX_USAGE.json` matched exactly: measured `2026-10-13T08:44:40.278638Z`, five-hour 79% remaining (21% used), reset `2026-10-13T13:19:11Z`; weekly 97% remaining (3% used), reset `2026-10-20T08:19:11Z`; `ordinary_usage_allowed=true`, source `codex_app_server`. The local runtime snapshot is ignored operational state and is not part of this review commit.

## Decision and next authorized action

**`INDEPENDENT_ARCHITECTURE_FAIL`**

Do not implement or activate the IPC. The next authorized action is a bounded ADR-only correction of F01–F06 on the ADR-author branch, followed by a new independent architecture/security review of the exact corrected commit. The correction may not change the frozen C01–C13 matrix, weaken the four-principal custody model, create a shared database/broker/second coordinator, or begin implementation.
