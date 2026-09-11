import pytest

from agent_lab.case001_physical_migration import MigrationMode
from scripts.case001_controlled_migration import (
    ControlledMigrationHarnessError,
    LIVE_SENTINEL,
    parse_args,
    safe_summary,
    validate_live_authorization,
)


def test_default_mode_is_dry_run():
    assert parse_args([]).mode == "dry-run"


def test_live_mode_requires_exact_sentinel_before_authority_inputs_are_accepted():
    with pytest.raises(ControlledMigrationHarnessError, match="sentinel"):
        validate_live_authorization(
            sentinel="YES",
            approver="human-001",
            authorization_reference="AUTH-001",
        )


def test_live_mode_requires_human_approver():
    with pytest.raises(ControlledMigrationHarnessError, match="HUMAN_APPROVER"):
        validate_live_authorization(
            sentinel=LIVE_SENTINEL,
            approver="",
            authorization_reference="AUTH-001",
        )


def test_live_mode_requires_authorization_reference():
    with pytest.raises(ControlledMigrationHarnessError, match="AUTHORIZATION_REFERENCE"):
        validate_live_authorization(
            sentinel=LIVE_SENTINEL,
            approver="human-001",
            authorization_reference="",
        )


def test_exact_live_authorization_inputs_pass_validation():
    assert validate_live_authorization(
        sentinel=LIVE_SENTINEL,
        approver="human-001",
        authorization_reference="AUTH-001",
    ) == ("human-001", "AUTH-001")


def test_safe_summary_contains_no_provider_object_or_parent_ids():
    summary = safe_summary(
        mode=MigrationMode.DRY_RUN,
        document_count=15,
        folder_count=0,
        manifest_reference="sha256:manifest",
        preflight_reference="sha256:preflight",
        approval_status=None,
        approval_consumed=False,
        drive_mutation=False,
    )
    assert summary["case_id"] == "CASE-001"
    assert summary["mode"] == "DRY_RUN"
    assert summary["document_count"] == 15
    assert "source_root_id" not in summary
    assert "target_root_id" not in summary
    assert "mappings" not in summary
    assert "object_ids" not in summary


def test_live_harness_end_to_end_creates_grants_consumes_and_moves(tmp_path, monkeypatch, capsys):
    import json
    from types import SimpleNamespace

    import scripts.case001_controlled_migration as harness
    from agent_lab.approval import ApprovalExecutionContext, ApprovalStatus, IntendedOperation
    from agent_lab.case001_migration import DocumentMigrationMapping
    from agent_lab.case001_migration_manifest import Case001MigrationManifest
    from agent_lab.case_state import CaseStateStore
    from agent_lab.durable_approval import DurableApprovalStore

    source = "source-parent"
    target = "target-parent"
    snapshot = tmp_path / "identity.json"
    snapshot.write_text("{}", encoding="utf-8")
    db = tmp_path / "approval.sqlite3"

    class FakeStorage:
        def __init__(self):
            self.parents = {f"obj-{i:02d}": source for i in range(1, 16)}

        def list_children(self, parent_id):
            return tuple(sorted(obj for obj, parent in self.parents.items() if parent == parent_id))

        def get_parent(self, object_id):
            return self.parents[object_id]

        def move(self, object_id, new_parent_id, *, expected_old_parent_id):
            assert self.parents[object_id] == expected_old_parent_id
            self.parents[object_id] = new_parent_id

    storage = FakeStorage()
    inventory = SimpleNamespace(document_count=15, folder_count=0)
    identity_records = tuple(
        SimpleNamespace(source_scope_ref=f"google_drive:{source}") for _ in range(15)
    )
    mappings = tuple(
        DocumentMigrationMapping(
            source_provider="google_drive",
            source_object_id=f"obj-{i:02d}",
            logical_document_id=f"DOC-{i:02d}",
            source_scope_ref=f"google_drive:{source}",
            target_scope_ref=f"google_drive:{target}",
        )
        for i in range(1, 16)
    )
    manifest = Case001MigrationManifest(
        case_id="CASE-001",
        tax_period_year=2024,
        source_provider="google_drive",
        source_scope_ref=f"google_drive:{source}",
        target_scope_ref=f"google_drive:{target}",
        mappings=mappings,
        inventory_evidence_id="EVIDENCE-E2E",
    )


    preflight = SimpleNamespace(
        target_is_empty=True,
        child_count=0,
        structural_preflight=SimpleNamespace(
            artifact_identity=SimpleNamespace(reference="sha256:preflight-e2e")
        ),
    )

    class FakeInventoryService:
        def __init__(self, metadata):
            pass

        def build(self, case_id):
            assert case_id == "CASE-001"
            return inventory

    class FakeIdentityRegistry:
        def __init__(self, cases, states):
            pass

        def load_snapshot(self, case_id, path):
            assert case_id == "CASE-001"
            assert path == snapshot

        def list_for_case(self, case_id):
            return identity_records

    class FakeManifestGenerator:
        def __init__(self, cases, identities):
            pass

        def generate(self, built_inventory, **kwargs):
            assert built_inventory is inventory
            assert kwargs["source_scope_ref"] == f"google_drive:{source}"
            assert kwargs["target_scope_ref"] == f"google_drive:{target}"
            return manifest

    class FakePreflightRunner:
        def __init__(self, *, drive_service):
            pass

        def run(self, generated_manifest, *, target_object_id):
            assert generated_manifest is manifest
            assert target_object_id == target
            return preflight

    def fake_compose(generated_manifest, live_preflight, *, run_id, actor):
        assert generated_manifest is manifest
        assert live_preflight is preflight
        return ApprovalExecutionContext(
            case_id="CASE-001",
            run_id=run_id,
            manifest_identity=manifest.artifact_identity.kind,
            manifest_version=manifest.artifact_identity.version,
            manifest_reference=manifest.artifact_identity.reference,
            preflight_identity="CASE001_LIVE_TARGET_PREFLIGHT",
            preflight_reference="sha256:preflight-e2e",
            preflight_result="PASSED",
            intended_operation=IntendedOperation.PHYSICAL_MIGRATION,
            actor=actor,
        )

    monkeypatch.setattr(harness, "get_drive_credentials", lambda: object())
    monkeypatch.setattr(harness, "build", lambda *args, **kwargs: object())
    monkeypatch.setattr(harness, "GoogleDriveMetadataAdapter", lambda **kwargs: object())
    monkeypatch.setattr(harness, "DocumentInventoryService", FakeInventoryService)
    monkeypatch.setattr(harness, "DocumentIdentityRegistry", FakeIdentityRegistry)
    monkeypatch.setattr(harness, "Case001MigrationManifestGenerator", FakeManifestGenerator)
    monkeypatch.setattr(harness, "GoogleDriveLiveTargetScopePreflight", FakePreflightRunner)
    monkeypatch.setattr(harness, "compose_approval_context", fake_compose)
    monkeypatch.setattr(harness, "GoogleDriveMutationAdapter", lambda **kwargs: storage)

    monkeypatch.setenv("CASE_001_DOCUMENTS_ROOT_ID", source)
    monkeypatch.setenv("CASE_001_TARGET_DOCUMENTS_ROOT_ID", target)
    monkeypatch.setenv("CASE_001_IDENTITY_SNAPSHOT", str(snapshot))
    monkeypatch.setenv("CASE_001_DURABLE_APPROVAL_DB", str(db))
    monkeypatch.setenv("CASE_001_LIVE_MIGRATION_AUTHORIZED", LIVE_SENTINEL)
    monkeypatch.setenv("CASE_001_HUMAN_APPROVER", "human-e2e")
    monkeypatch.setenv("CASE_001_AUTHORIZATION_REFERENCE", "AUTH-E2E-001")

    assert harness.main(["--mode", "live"]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["approval_status"] == "CONSUMED"
    assert summary["approval_consumed"] is True
    assert summary["drive_mutation"] is True
    assert set(storage.parents.values()) == {target}

    cases = harness.build_case_registry(source)
    states = CaseStateStore(cases)
    states.create_run("CASE-001", request_id="reopen-e2e")
    with DurableApprovalStore(db, case_registry=cases, case_state=states) as approvals:
        restored = approvals.get("APP-00000001")
        assert restored.approval_status is ApprovalStatus.CONSUMED
        assert restored.authorization_reference == "AUTH-E2E-001"
