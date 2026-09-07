# D-020 — CASE-001 Approval Context Composition

## Status and scope

Human-accepted at `e6f28e89acf45541e4cfaa55c9efd8db35fc7909` and integrated into main through a non-fast-forward merge. Integrated-main verification: **223 passed, 1 skipped in 2.29s**, using the complete-suite command below. D-020 is closed; approval consumption and physical migration remain outside this acceptance.

`src/agent_lab/case001_approval_context.py` exposes the pure function `compose_approval_context(manifest, live_preflight, *, run_id, actor)`. It returns the generic D-017 `ApprovalExecutionContext`. It has no Case Registry, approval store, audit store, filesystem, or Drive client dependency and performs no external data access. Its inputs must be supplied by the existing case-scoped workflow. Presence checks on run and actor do not establish registry membership, authorization, or execution-attempt provenance.

## Authorized provenance adjustment

`LiveTargetScopeResult.manifest_identity` records the exact existing `manifest.artifact_identity` when live target preflight produces its result. D-020 requires equality of the complete stored identity (kind, version, reference) with the supplied manifest identity. The optional default `None` preserves older construction calls, but such unbound results are rejected by D-020. Missing provenance is never inferred or reconstructed.

This closes an ambiguity: different document mappings can produce the same structural preflight fields and reference. Their manifest references differ, so the stored binding prevents substitution. Identical manifest contents intentionally count as the same artifact identity. No attempt/run provenance is introduced.

The structural `MigrationPreflightResult.artifact_identity` remains the exact D-018 preflight artifact. Its version-1 hashed payload is unchanged. The enclosing live result has no new approval-specific identity scheme. The binding is provenance data, not a signature or proof that a caller-supplied value came from a trusted execution.

## Composition contract

The context preserves the supplied run and actor strings without normalization. Its other fields are:

| Context field | Source |
|---|---|
| `case_id` | Validated manifest case (`CASE-001`) |
| `manifest_identity` | Manifest identity kind |
| `manifest_version` | Manifest identity version (`1`) |
| `manifest_reference` | Exact manifest identity reference |
| `preflight_identity` | Structural preflight identity kind |
| `preflight_reference` | Exact structural preflight identity reference |
| `preflight_result` | `PASSED`, only after successful validation |
| `intended_operation` | `IntendedOperation.PHYSICAL_MIGRATION` |

The preflight version must be `1`, although the existing generic context has no preflight-version field. Expected kinds are `CASE001_MIGRATION_MANIFEST` and `CASE001_MIGRATION_PREFLIGHT`.

Validation rejects missing/blank or non-string run and actor identifiers; invalid artifact types; unsupported kinds or versions; missing/mismatched manifest provenance; non-success structural flags; case, year, source, target, or document-count disagreements; and zero-document manifests. CASE-001 and 2024 remain mandatory.

The enclosing live result must describe an empty folder, have zero children, and identify the same `google_drive:<target_object_id>` target scope. No mismatched value is normalized into agreement. Invalid composition raises `ApprovalContextCompositionError`.

## Side effects and authority

Composition creates only an immutable execution-context value. It does not create a pending approval, grant or consume approval, mutate lifecycle state, audit a consequential action, execute migration, or call Drive. `approval.py` remains generic and unchanged. Manifest generation and live target validation remain independent of approval semantics.

## Verification

All data used by the D-020 tests is synthetic. With process-local `$env:PYTHONPATH="src"`, the existing `.\.venv\Scripts\python.exe` ran:

- `-m pytest -q tests/unit/test_case001_approval_context.py`: **51 passed**.
- `-m pytest -q tests/unit/test_approval.py tests/unit/test_artifact_identity.py tests/unit/test_case001_migration_manifest.py tests/unit/test_case001_migration_preflight.py tests/unit/test_case001_live_target_preflight.py tests/unit/test_case001_approval_context.py`: **104 passed**.
- `-m pytest -q`: **223 passed, 1 skipped**. The opt-in live Drive harness skipped; no live Drive verification is claimed.

Coverage includes exact identity preservation, same-artifact reconstruction, mapping substitution despite identical structural identities, all required mismatch failures, legacy missing provenance, constructor rejection of invalid case/year, no lifecycle calls, and fake live execution exposing only metadata get/list operations.

No test failures required correction. Passing tests does not constitute human acceptance of D-020 or authorization for physical migration.
