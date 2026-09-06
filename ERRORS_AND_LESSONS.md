# Errors and Lessons

This file records only verified implementation failures, corrections, and architectural lessons. It is not a reconstruction of every historical interaction. Unverified memories are deliberately excluded.

## 2026-09-06 — Live manifest readiness

### Lesson: in-memory logical identity is insufficient for a restart-safe real manifest

**Observed condition:** Document Identity was intentionally implemented in memory. That passed the identity and migration unit boundaries, but a fresh process could not retain previously assigned logical `document_id` values.

**Risk:** Rebuilding identities from a fresh live inventory could make a document appear new and would weaken the core invariant that migration preserves logical document identity.

**Correction:** Add a versioned, case-scoped local JSON snapshot export/import boundary and a read-only CASE-001 bootstrap harness. The local snapshot is ignored by Git and may contain private provider object IDs.

**Verification required:** user execution of the bootstrap against the live CASE-001 Documents scope.

## 2026-09-06 — Migration source-scope authority

### Lesson: an explicit migration source scope must agree with the registered case scope

**Observed condition:** The migration compatibility layer accepted an explicit source scope without requiring it to equal the currently registered CASE-001 storage scope.

**Risk:** A caller could construct a migration plan from an unrelated scope while still naming CASE-001.

**Correction:** `Case001MigrationCompatibility.prepare()` and `validate()` now require the source scope to equal the authoritative registered CASE-001 scope (`provider:root_id`).

**Verification required:** user execution of the migration unit suite after this change.

## 2026-09-06 — Manifest tests versus real execution

### Lesson: created tests are not verified tests

**Observed condition:** `tests/unit/test_case001_migration_manifest.py` had been created while CURRENT_STATE still described its verification as pending.

**Correction:** The user subsequently executed the suite and obtained `6 passed in 0.17s`.

**Rule:** CURRENT_STATE must distinguish implementation status from actually executed verification.

## General architectural lessons

- File existence is not proof of correctness.
- A skipped integration test is not a pass.
- Unit tests do not prove live Google Drive isolation or production authorization.
- GitHub remains the source of truth for code, decisions, and verified state; private Drive object IDs remain local evidence.
- Case isolation must be enforced by deterministic code, not prompts.
- Logical document identity is based on provider/object identity and provenance, not filenames.
- Physical migration must remain separate from planning and validation until an explicit human-controlled mutation gate, rollback strategy, and post-migration verification exist.
