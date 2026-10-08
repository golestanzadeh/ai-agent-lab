# OI-0002 independent security and acceptance review 02

Review date: 2026-10-08  
Reviewer role: separate independent security and acceptance reviewer  
Repository: `golestanzadeh/ai-agent-lab`  
Branch: `oi0002-identity-persistence`  
Exact reviewed SHA: `ad263284ff211d6d7d75234c03c3005d43b7d2df`  
Implementation commit: `ad30cee664b2ca002014adb0c9b3c46daca7ca82`  
Recommendation: **FAIL**

The remote branch head was fetched and matched the requested SHA. Review ran from a new clean detached worktree. Existing worktrees and uncommitted files were not modified. The first review and remediation evidence were preserved. No implementation, frozen contract, CASE-001 identity, protected evidence, merge, release, external transmission, scheduler, downstream package or OI-0003 action was changed or invoked.

Authenticated starting capacity reported by the supervising session was five-hour 54% remaining and weekly 68% remaining. The review remained above the mandatory 15-point five-hour reserve.

## Executive result

F01 and F04 are corrected at code level. Five mandatory security/integrity findings remain unresolved or only partially corrected:

1. Generic tax-agent derived-artifact capabilities authorize privileged identity lifecycle operations.
2. Declaration, confirmation, authorization and role-evidence references are syntax-checked but never resolved or verified.
3. Open-ended exclusive role records cannot be closed by an immutable evidence-backed correction, so valid family history cannot advance.
4. The database and its same-directory anchor can be rolled back together to an older valid pair without detection.
5. The v1 migration destructively commits table deletion before schema recreation and data insertion, so an interruption can destroy the legacy schema.

The submitted tests pass, but those results do not satisfy the affected frozen invariants. OI-0002 remains OPEN.

## F01-F07 disposition

### F01 — PASS — manifest expiry

- Code: `src/agent_lab/orchestrator_kernel.py:1223-1259`.
- Observed: each permission decision checks `expires_at` before capability/scope authorization, transitions an active expired manifest to `EXPIRED`, and denies at the exact boundary.
- Independent evidence: exact-boundary read returned `False/DENY`; after Kernel reopen, the write decision also returned `False/DENY`. Submitted expiry and Kill Switch tests pass.
- Residual risk: none blocking this finding.

### F02 — FAIL — identity lifecycle is over-authorized by generic capabilities

- Code: `src/agent_lab/identity_permission_adapter.py:24-44`; permission contract `contracts/orchestrator/v1/permission-matrix.json:44-45`; role grants in `contracts/orchestrator/v1/roles.json`.
- Observed: `register_identity`, `update_identity`, `bind_party` and `bind_fact` all map to generic `write_derived_case_artifact`. A synthetic `TAX_LAW_AGENT` manifest holding only ordinary derived-artifact read/write capabilities successfully registered and read an identity. No identity-administration capability or trusted lifecycle-service role exists in the frozen matrix.
- Adjacent boundary: `_load_identity()` and the SQLite connection remain directly callable implementation attributes (`identity_persistence.py:289-302`), so the Python object is not a security sandbox; production confinement is still operational.
- Correction required: obtain authority for least-privilege identity lifecycle capabilities/service entry points and bind them to explicitly permitted roles. Do not silently expand the frozen Permission Matrix.

### F03 — FAIL — immutable fact source and confirmation evidence are not resolvable

- Code: `src/agent_lab/identity_persistence.py:387-414` and `416-430`.
- Observed: the full fact payload is HMAC-bound, but `declaration_artifact_ref`, `confirmation_ref`, authorization and audit references are accepted solely when they match the `sha256:` text pattern. Readback reconstructs the embedded fact and checks its self-contained confirmation enum; it never resolves the declaration or confirmation artifacts or verifies that those artifacts exist and bind the same fact/subject/scope.
- Reproduction: fresh arbitrary 64-hex declaration, confirmation and audit references with no backing artifacts were accepted and survived binding (`UNRESOLVED_FAKE_LINEAGE_ACCEPTED True`).
- Correction required: integrate an authorized immutable evidence resolver/repository, bind exact content identities and confirmation records, and fail closed after restart when any required lineage object is absent, changed or mismatched.

### F04 — PASS — ACTIVE lifecycle enforcement

- Code: `src/agent_lab/identity_persistence.py:289-302`, `334-370`, `416-430`.
- Observed: party/fact/identity boundaries require an ACTIVE record. INACTIVE, ARCHIVED and UNRESOLVED status tests pass; an independently archived identity remained rejected after store restart.
- Residual risk: authorization of the status transition itself remains part of F02.

### F05 — FAIL — role evidence/correction semantics remain incomplete

- Code: `src/agent_lab/identity_persistence.py:334-356`.
- Observed: overlap across different subjects is now rejected and half-open adjacent intervals work. However evidence and authorization references are only regex-validated, not resolved. There is no governed correction/revision operation for an existing role. An open-ended spouse binding cannot be closed, and a later successor spouse binding is therefore rejected forever as overlapping.
- Reproduction: after an open-ended `SPOUSE_OR_PARTNER` binding for P2, an evidence-backed successor for P3 beginning 2026-01-01 failed with `ValueError: overlapping role binding`.
- Correction required: add an immutable, authorized effective-dated correction/closure operation with monotonic revision and verified evidence, preserving the original history and enforcing cardinality on the resulting timeline.

### F06 — FAIL — same-boundary anchor permits undetected rollback

- Code: `src/agent_lab/identity_persistence.py:88`, `186-224`, `246-263`, `432-438`; operations guidance `docs/oi-0002-persistence-operations.md:7-16`.
- Positive evidence: deletion, event-ID reordering, event rewriting, payload-plus-digest substitution, missing/altered anchor, wrong HMAC key and a database/anchor partial update all failed closed.
- Blocking bypass: the anchor is deliberately stored beside the mutable database and backup copies both as one set. An older valid database and its matching older anchor were copied, a later role event was committed, then both old files were restored. Reopen succeeded and returned zero parties (`VALID_OLD_DB_PLUS_ANCHOR_ROLLBACK_ACCEPTED True`). The HMAC key prevents forgery but does not provide freshness or an independent monotonic trust boundary.
- Correction required: bind continuity to protected monotonic state outside the replaceable database/anchor recovery set (or an equivalently reviewed anti-rollback mechanism), with explicit restore authorization and tests.

### F07 — FAIL — v1 migration is not atomic

- Code: `src/agent_lab/identity_persistence.py:153-184`.
- Observed: legacy validation is followed by a committed DROP transaction, then `_create_schema()` in a second transaction, then insertion in a third. This contradicts the remediation report's claim of a transactional v1-to-v2 migration.
- Reproduction: injecting a crash at schema creation after the committed DROP left no application tables and `user_version=1` (`MIGRATION_CRASH_DESTROYED_SCHEMA True [] 1`).
- Positive evidence: unsupported/nonempty-lineage schemas reject; normal empty-v1 migration, ordinary before-commit rollback, post-commit fail-closed reopen, backup/restore and synchronized-path rejection tests pass.
- Correction required: perform migration in one recoverable transaction or a reviewed copy/verify/atomic-swap procedure; add crash injection at every migration phase. Production ACL and key-custody evidence remain operational Human Gates.

## T01-T12 independent acceptance matrix

| ID | Expected behavior | Independent observation | Result | Residual risk |
|---|---|---|---|---|
| T01 | Stable identity IDs/digests across restart. | Individual test passed; independent restart readback succeeded. | PASS | Privileged access remains over-broad under F02. |
| T02 | Strict owner association; spouse only through role path. | Wrong primary owner rejects and explicit spouse path passes. | PASS | Role evidence is not resolved. |
| T03 | Correct effective history, boundaries and open intervals. | Half-open boundary and open-ended lookup pass. | PASS | Open-ended correction is covered by failing T04. |
| T04 | Conflicts reject; non-overlap and evidence-backed correction preserve history. | Cross-subject overlap rejects and adjacency passes, but open-ended records cannot be corrected/closed and evidence is not resolved. | FAIL | Family history can become permanently unmaintainable. |
| T05 | Unknown and non-active identities and owner mismatch fail closed. | INACTIVE/ARCHIVED/UNRESOLVED, owner mismatch and archived-after-restart reject. | PASS | Status-transition privilege is F02. |
| T06 | Confirmed v1 fact binds through a complete verifiable envelope. | Embedded payload/digest persists, but arbitrary nonexistent declaration/confirmation lineage is accepted. | FAIL | Trust evidence is not independently recoverable. |
| T07 | Wrong scope/state/digest/replay and missing or altered lineage reject. | Submitted negatives pass; missing/unresolvable source evidence is not checked. | FAIL | A syntactically valid fabricated evidence identity becomes a trust root. |
| T08 | Replay is idempotent; ordinary operation crashes create no orphan rows. | Individual tests passed: replay and pre-commit rollback work; post-commit interruption fails closed. | PASS | Migration crash remains F07; post-commit recovery needs operator intervention. |
| T09 | Exact case/year/run/root isolation. | Cross-case/root tests and Kernel scope checks pass. | PASS | In-process storage confinement remains operational. |
| T10 | Corruption, schema, lineage and audit failures block readback. | Local mutations reject, but a valid old database-plus-anchor rollback is accepted. | FAIL | Audit history can be truncated by replaying an older recovery set. |
| T11 | Complete legacy regression remains green. | `1084 passed, 5 skipped`; skips were pre-existing and not reinterpreted as security PASS. | PASS | Regression does not cover the reproduced defects. |
| T12 | Real CASE-001 identity bootstrap remains Human-gated. | No real identity or protected taxpayer data was created. | PASS | Real Person A/B bootstrap remains `HUMAN_REQUIRED`. |

Total: **8 PASS, 4 FAIL, 0 BLOCKED**.

## Commands and reproducible evidence

Environment: Windows, Python 3.14, clean detached worktree at exact SHA `ad263284ff211d6d7d75234c03c3005d43b7d2df`, `PYTHONPATH=src` (plus `tests/unit` only for Kernel fixture construction).

1. Focused persistence/Kernel: `python -m pytest tests/unit/test_identity_persistence.py tests/unit/test_orchestrator_kernel.py -q` — 52 passed, exit 0.
2. Relevant registry/authorization/lineage regression: `python -m pytest tests/unit/test_identity_persistence.py tests/unit/test_orchestrator_kernel.py tests/unit/test_person_entity_registry.py tests/unit/test_case_identity_association.py tests/unit/test_human_declared_fact.py tests/unit/test_durable_approval.py tests/unit/test_case_registry.py -q` — 102 passed, exit 0.
3. T01-T10 and T12 were invoked separately with `python -m pytest tests/unit/test_identity_persistence.py -q -k <id>` — 19 checks passed in total, exit 0. T11 is command 5.
4. Independent adversarial scripts — exit 0 for the authoritative runs: exact expiry/restart and archived-restart rejected; eight audit/key/anchor mutations rejected; generic tax-agent lifecycle, nonexistent lineage, open-ended correction denial, valid old DB+anchor rollback and destructive migration crash were reproduced as described above.
5. Complete unit regression: `python -m pytest tests/unit -q` — 1084 passed, 5 skipped in 237.23 seconds, exit 0.
6. Documentation/governance regression: `python -m pytest tests/unit/test_documentation_index.py tests/unit/test_orchestrator_pilot.py -q` — 15 passed, exit 0.

One exploratory migration probe printed the reproduced defect but exited 1 because the simulated constructor crash left a Windows SQLite handle open during temporary-directory cleanup. It was rerun as two separate processes; the authoritative reproduction exited 0 and showed the same empty-schema result. It is not counted as a passing test.

## Residual risks and Human Gates

- The frozen Kernel Permission Matrix has no dedicated identity lifecycle capability. Adding or reallocating capabilities requires the existing governance/Owner authority; the reviewer does not authorize it.
- Selection and authorization of an immutable protected declaration/confirmation/evidence resolver is required; no private evidence may enter Git.
- The anti-rollback continuity trust boundary, HMAC key custody, filesystem ACLs and production recovery procedure require reviewed operational evidence.
- Nonempty v1 fact stores remain intentionally Human-gated because v1 lacks required lineage, but the empty-v1 migration must first be made crash-safe.
- Real CASE-001 Person A/B resolution/bootstrap remains `HUMAN_REQUIRED` and was not attempted.

## Final handoff

Recommendation: **FAIL**. Keep OI-0002 OPEN and OI-0003/downstream work blocked. Return F02, F03, F05, F06 and F07 to an implementation worker. A new exact remediation commit must then receive another separate independent review. No merge, release, production activation or external action is permitted by this report.

Exact next permitted action: authorize and implement a bounded second remediation for the five unresolved findings without changing frozen contracts unless the corresponding Human Gate is explicitly approved.

## Capacity handoff

- Authenticated ending observation at `2026-10-08T17:44:34Z`: five-hour 40% remaining, reset `2026-10-08T21:47:13Z`; weekly 66% remaining, reset `2026-10-14T16:57:07Z`.
- Source: signed-in Codex account rate-limit service. Readback was unambiguous and remained above the required reserve; no reset credit was used.
