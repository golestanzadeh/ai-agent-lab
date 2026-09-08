from dataclasses import replace
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest

from agent_lab.approval import ApprovalExecutionContext
from agent_lab.case001_approval_context import ApprovalContextCompositionError
from agent_lab.case001_migration import DocumentMigrationMapping
from agent_lab.case001_migration_manifest import Case001MigrationManifest
from agent_lab.case001_migration_preflight import Case001MigrationPreflight
from agent_lab.case001_live_target_preflight import LiveTargetScopeResult

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from case001_prepare_approval import prepare_pending
sys.path.pop(0)


def artifacts():
    mapping = DocumentMigrationMapping("google_drive", "source-object", "logical-document", "google_drive:source", "google_drive:target")
    manifest = Case001MigrationManifest("CASE-001", 2024, "google_drive", mapping.source_scope_ref, mapping.target_scope_ref, (mapping,))
    preflight = Case001MigrationPreflight().run(manifest, target_scope_is_actual=True, target_is_empty=True)
    return manifest, LiveTargetScopeResult("target", "Documents", "application/vnd.google-apps.folder", True, True, 0, preflight, manifest.artifact_identity)


def test_only_pending_creation_is_called():
    manifest, live = artifacts()
    store = Mock(spec=["create_pending"])
    context, record = prepare_pending(manifest, live, run_id="run", actor="actor", approvals=store)
    assert isinstance(context, ApprovalExecutionContext)
    assert record is store.create_pending.return_value
    assert [call[0] for call in store.method_calls] == ["create_pending"]
    assert store.create_pending.call_args.kwargs["manifest_reference"] == manifest.artifact_identity.reference
    assert "approver" not in store.create_pending.call_args.kwargs


def test_bad_provenance_creates_no_record():
    manifest, live = artifacts()
    store = Mock(spec=["create_pending"])
    with pytest.raises(ApprovalContextCompositionError):
        prepare_pending(manifest, replace(live, manifest_identity=None), run_id="run", actor="actor", approvals=store)
    assert not store.method_calls
