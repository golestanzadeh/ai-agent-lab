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
