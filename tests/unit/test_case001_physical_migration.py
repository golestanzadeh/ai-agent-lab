from dataclasses import replace
from datetime import datetime, timezone

import pytest

from agent_lab.approval import (
    ApprovalAlreadyConsumedError,
    ApprovalExecutionContext,
    ApprovalStatus,
    IntendedOperation,
    MigrationApproval,
)
from agent_lab.case001_migration import DocumentMigrationMapping
from agent_lab.case001_migration_manifest import Case001MigrationManifest
from agent_lab.case001_physical_migration import (
    Case001PhysicalMigrationExecutor,
    MigrationMode,
    PhysicalMigrationPreconditionError,
    PhysicalMigrationRollbackError,
    PhysicalMigrationVerificationError,
)

NOW = datetime(2026, 9, 10, tzinfo=timezone.utc)
SOURCE = "source-parent"
TARGET = "target-parent"


class FakeStorage:
    def __init__(self):
        self.parents = {"obj-1": SOURCE, "obj-2": SOURCE}
        self.fail_move_object = None
        self.fail_rollback_object = None
        self.corrupt_target_listing = False
        self.move_calls = []
        self.list_calls = []

    def list_children(self, parent_id):
        self.list_calls.append(parent_id)
        children = tuple(sorted(obj for obj, parent in self.parents.items() if parent == parent_id))
        if self.corrupt_target_listing and parent_id == TARGET and children:
            return children[:-1]
        return children

    def get_parent(self, object_id):
        return self.parents[object_id]

    def move(self, object_id, new_parent_id, *, expected_old_parent_id):
        self.move_calls.append((object_id, expected_old_parent_id, new_parent_id))
        if self.parents.get(object_id) != expected_old_parent_id:
            raise RuntimeError("guarded parent mismatch")
        if new_parent_id == TARGET and object_id == self.fail_move_object:
            raise RuntimeError("injected move failure")
        if new_parent_id == SOURCE and object_id == self.fail_rollback_object:
            raise RuntimeError("injected rollback failure")
        self.parents[object_id] = new_parent_id


class FakeApprovalStore:
    def __init__(self, approval):
        self.approval = approval
        self.validate_calls = 0
        self.consume_calls = 0
        self.fail_consume = False

    def validate(self, approval_id, context):
        self.validate_calls += 1
        if approval_id != self.approval.approval_id:
            raise RuntimeError("unknown approval")
        if self.approval.approval_status is ApprovalStatus.CONSUMED:
            raise ApprovalAlreadyConsumedError("APPROVAL_ALREADY_CONSUMED")
        return self.approval

    def consume(self, approval_id, context):
        self.consume_calls += 1
        if self.fail_consume:
            raise RuntimeError("injected approval consume failure")
        if self.approval.approval_status is ApprovalStatus.CONSUMED:
            raise ApprovalAlreadyConsumedError("APPROVAL_ALREADY_CONSUMED")
        self.approval = replace(self.approval, approval_status=ApprovalStatus.CONSUMED)
        return self.approval


def manifest():
    mappings = (
        DocumentMigrationMapping(
            source_provider="google_drive",
            source_object_id="obj-1",
            logical_document_id="DOC-1",
            source_scope_ref="google_drive:legacy",
            target_scope_ref="google_drive:target",
        ),
        DocumentMigrationMapping(
            source_provider="google_drive",
            source_object_id="obj-2",
            logical_document_id="DOC-2",
            source_scope_ref="google_drive:legacy",
            target_scope_ref="google_drive:target",
        ),
    )
    return Case001MigrationManifest(
        case_id="CASE-001",
        tax_period_year=2024,
        source_provider="google_drive",
        source_scope_ref="google_drive:legacy",
        target_scope_ref="google_drive:target",
        mappings=mappings,
        inventory_evidence_id="EVIDENCE-1",
    )


def approval():
    return MigrationApproval(
        approval_id="APP-00000001",
        case_id="CASE-001",
        run_id="RUN-00000001",
        manifest_identity="sha256:manifest",
        manifest_version="1",
        manifest_reference="manifest://case001",
        preflight_identity="sha256:preflight",
        preflight_reference="preflight://case001",
        preflight_result="PASSED",
        intended_operation=IntendedOperation.PHYSICAL_MIGRATION,
        approver="human-001",
        actor="executor-001",
        approval_timestamp=NOW,
        authorization_reference="AUTH-001",
        approval_status=ApprovalStatus.APPROVED,
        audit_reference="AUDIT-00000002",
    )


def context():
    return ApprovalExecutionContext(
        case_id="CASE-001",
        run_id="RUN-00000001",
        manifest_identity="sha256:manifest",
        manifest_version="1",
        manifest_reference="manifest://case001",
        preflight_identity="sha256:preflight",
        preflight_reference="preflight://case001",
        preflight_result="PASSED",
        intended_operation=IntendedOperation.PHYSICAL_MIGRATION,
        actor="executor-001",
    )


def test_dry_run_is_default_and_performs_zero_mutations_or_consumption():
    storage = FakeStorage()
    auth = FakeApprovalStore(approval())
    result = Case001PhysicalMigrationExecutor(storage=storage).execute(
        manifest(), source_parent_id=SOURCE, target_parent_id=TARGET,
        approval_store=auth, approval_id="APP-00000001", approval_context=context(),
    )
    assert result.mode is MigrationMode.DRY_RUN
    assert result.verified is True
    assert result.approval_consumed is False
    assert storage.move_calls == []
    assert auth.validate_calls == 0
    assert auth.consume_calls == 0
    assert storage.parents == {"obj-1": SOURCE, "obj-2": SOURCE}


def test_live_disabled_fails_before_any_storage_inspection():
    storage = FakeStorage()
    auth = FakeApprovalStore(approval())
    with pytest.raises(PhysicalMigrationPreconditionError, match="not explicitly enabled"):
        Case001PhysicalMigrationExecutor(storage=storage).execute(
            manifest(),
            source_parent_id=SOURCE,
            target_parent_id=TARGET,
            mode=MigrationMode.LIVE,
            live_enabled=False,
            approval_store=auth,
            approval_id="APP-00000001",
            approval_context=context(),
        )
    assert storage.list_calls == []
    assert storage.move_calls == []
    assert auth.validate_calls == 0


def test_live_success_moves_exact_objects_then_consumes_approval():
    storage = FakeStorage()
    auth = FakeApprovalStore(approval())
    result = Case001PhysicalMigrationExecutor(storage=storage).execute(
        manifest(),
        source_parent_id=SOURCE,
        target_parent_id=TARGET,
        mode=MigrationMode.LIVE,
        live_enabled=True,
        approval_store=auth,
        approval_id="APP-00000001",
        approval_context=context(),
    )
    assert result.moved_object_ids == ("obj-1", "obj-2")
    assert result.approval_consumed is True
    assert storage.parents == {"obj-1": TARGET, "obj-2": TARGET}
    assert auth.validate_calls == 1
    assert auth.consume_calls == 1
    assert auth.approval.approval_status is ApprovalStatus.CONSUMED


def test_replay_of_consumed_approval_fails_before_storage_inspection():
    storage = FakeStorage()
    consumed = replace(approval(), approval_status=ApprovalStatus.CONSUMED)
    auth = FakeApprovalStore(consumed)
    with pytest.raises(ApprovalAlreadyConsumedError, match="APPROVAL_ALREADY_CONSUMED"):
        Case001PhysicalMigrationExecutor(storage=storage).execute(
            manifest(),
            source_parent_id=SOURCE,
            target_parent_id=TARGET,
            mode=MigrationMode.LIVE,
            live_enabled=True,
            approval_store=auth,
            approval_id="APP-00000001",
            approval_context=context(),
        )
    assert storage.list_calls == []
    assert storage.move_calls == []


def test_nonempty_target_fails_without_mutation_or_consumption():
    storage = FakeStorage()
    storage.parents["unexpected"] = TARGET
    auth = FakeApprovalStore(approval())
    with pytest.raises(PhysicalMigrationPreconditionError, match="target parent is not empty"):
        Case001PhysicalMigrationExecutor(storage=storage).execute(
            manifest(),
            source_parent_id=SOURCE,
            target_parent_id=TARGET,
            mode=MigrationMode.LIVE,
            live_enabled=True,
            approval_store=auth,
            approval_id="APP-00000001",
            approval_context=context(),
        )
    assert storage.move_calls == []
    assert auth.consume_calls == 0


def test_partial_move_failure_rolls_back_in_reverse_order_and_keeps_approval():
    storage = FakeStorage()
    storage.fail_move_object = "obj-2"
    auth = FakeApprovalStore(approval())
    with pytest.raises(RuntimeError, match="injected move failure"):
        Case001PhysicalMigrationExecutor(storage=storage).execute(
            manifest(),
            source_parent_id=SOURCE,
            target_parent_id=TARGET,
            mode=MigrationMode.LIVE,
            live_enabled=True,
            approval_store=auth,
            approval_id="APP-00000001",
            approval_context=context(),
        )
    assert storage.parents["obj-1"] == SOURCE
    assert storage.parents["obj-2"] == SOURCE
    assert storage.move_calls[-1] == ("obj-1", TARGET, SOURCE)
    assert auth.consume_calls == 0
    assert auth.approval.approval_status is ApprovalStatus.APPROVED


def test_post_verification_failure_rolls_back_all_moves_and_keeps_approval():
    storage = FakeStorage()
    storage.corrupt_target_listing = True
    auth = FakeApprovalStore(approval())
    with pytest.raises(PhysicalMigrationVerificationError, match="target contents"):
        Case001PhysicalMigrationExecutor(storage=storage).execute(
            manifest(),
            source_parent_id=SOURCE,
            target_parent_id=TARGET,
            mode=MigrationMode.LIVE,
            live_enabled=True,
            approval_store=auth,
            approval_id="APP-00000001",
            approval_context=context(),
        )
    assert storage.parents == {"obj-1": SOURCE, "obj-2": SOURCE}
    assert auth.consume_calls == 0


def test_approval_consume_failure_rolls_back_storage():
    storage = FakeStorage()
    auth = FakeApprovalStore(approval())
    auth.fail_consume = True
    with pytest.raises(RuntimeError, match="consume failure"):
        Case001PhysicalMigrationExecutor(storage=storage).execute(
            manifest(),
            source_parent_id=SOURCE,
            target_parent_id=TARGET,
            mode=MigrationMode.LIVE,
            live_enabled=True,
            approval_store=auth,
            approval_id="APP-00000001",
            approval_context=context(),
        )
    assert storage.parents == {"obj-1": SOURCE, "obj-2": SOURCE}
    assert auth.approval.approval_status is ApprovalStatus.APPROVED


def test_incomplete_rollback_is_explicit_terminal_failure():
    storage = FakeStorage()
    storage.fail_move_object = "obj-2"
    storage.fail_rollback_object = "obj-1"
    auth = FakeApprovalStore(approval())
    with pytest.raises(PhysicalMigrationRollbackError) as excinfo:
        Case001PhysicalMigrationExecutor(storage=storage).execute(
            manifest(),
            source_parent_id=SOURCE,
            target_parent_id=TARGET,
            mode=MigrationMode.LIVE,
            live_enabled=True,
            approval_store=auth,
            approval_id="APP-00000001",
            approval_context=context(),
        )
    assert excinfo.value.object_ids == ("obj-1",)
    assert storage.parents["obj-1"] == TARGET
    assert auth.approval.approval_status is ApprovalStatus.APPROVED
