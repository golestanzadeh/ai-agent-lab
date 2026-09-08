"""D-021 create-only target provisioning and local PENDING approval evidence.

Private outputs are review exports, not a durable ApprovalStore or authority to
reload/grant/consume approvals. All provider identifiers remain under artifacts/.
"""
from dataclasses import asdict
from datetime import datetime
from enum import Enum
import json
import os
from pathlib import Path
import uuid

from googleapiclient.discovery import build

from agent_lab.approval import ApprovalStore
from agent_lab.audit import ActorType, AuditEventType, AuditStatus, AuditStore
from agent_lab.case001_approval_context import compose_approval_context
from agent_lab.case001_live_target_preflight import GoogleDriveLiveTargetScopePreflight
from agent_lab.case001_migration_manifest import Case001MigrationManifestGenerator
from agent_lab.case_scoped_drive import CaseScopedDriveResolver
from agent_lab.case_state import CaseStateStore
from agent_lab.document_identity import DocumentIdentityRegistry
from agent_lab.document_inventory import DocumentInventoryService
from agent_lab.google_drive_auth import get_drive_credentials
from agent_lab.google_drive_provisioning import GoogleDriveStorageScopeCreator
from agent_lab.google_drive_storage import GoogleDriveMetadataAdapter
from case001_live_target_preflight import build_case_registry


def prepare_pending(manifest, live, *, run_id, actor, approvals):
    context = compose_approval_context(manifest, live, run_id=run_id, actor=actor)
    return context, approvals.create_pending(**asdict(context))


def json_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    raise TypeError("unsupported private evidence value")


def main():
    root = os.environ.get("AI_TAX_AGENT_DRIVE_ROOT_ID", "").strip()
    source = os.environ.get("CASE_001_DOCUMENTS_ROOT_ID", "").strip()
    if not root or not source or root == source:
        raise ValueError("explicit distinct system and source roots required")
    actor = "codex-d021-provisioning-agent"
    cases = build_case_registry(source)
    case = cases.get("CASE-001")
    states = CaseStateStore(cases)
    run = states.create_run("CASE-001", request_id=f"d021-{uuid.uuid4()}")
    audit = AuditStore(cases, states)
    identities = DocumentIdentityRegistry(cases, states)
    identities.load_snapshot("CASE-001", Path("artifacts/case001/document_identity.json"))
    records = identities.list_for_case("CASE-001")
    if len(records) != 15 or any(r.source_scope_ref != f"google_drive:{source}" for r in records):
        raise ValueError("source snapshot does not match registered source scope/count")
    drive = build("drive", "v3", credentials=get_drive_credentials(), cache_discovery=False)
    storage = GoogleDriveMetadataAdapter(drive_service=drive, resolver=CaseScopedDriveResolver(cases))
    inventory = DocumentInventoryService(storage).build("CASE-001")
    if inventory.document_count != 15 or inventory.folder_count != 0:
        raise ValueError("live source inventory differs from verified count")

    class Sink:
        def record(self, event):
            audit.append(case_id=event.case_id, run_id=run.run_id,
                         event_type=AuditEventType.TOOL_CALLED if event.outcome == "CREATE_INTENT" else AuditEventType.TOOL_COMPLETED,
                         actor_type=ActorType.AGENT, actor_id=actor, operation=event.operation,
                         status=AuditStatus.INFO if event.outcome == "CREATE_INTENT" else AuditStatus.SUCCESS,
                         metadata={"path": event.path, "outcome": event.outcome})

    creator = GoogleDriveStorageScopeCreator(drive_service=drive, system_root_id=root,
        journal_path=Path("artifacts/case001/provisioning.json"), audit=Sink())
    target = creator.documents_scope(case.tax_period, case.case_id)
    manifest = Case001MigrationManifestGenerator(cases, identities).generate(
        inventory, source_provider="google_drive", source_scope_ref=f"google_drive:{source}",
        target_scope_ref=f"google_drive:{target.root_id}")
    live = GoogleDriveLiveTargetScopePreflight(drive_service=drive).run(manifest, target_object_id=target.root_id)
    context, pending = prepare_pending(manifest, live, run_id=run.run_id, actor=actor,
        approvals=ApprovalStore(case_registry=cases, case_state=states, audit_store=audit))
    audit.validate()
    evidence = {
        "case": asdict(case), "run": asdict(run), "inventory": asdict(inventory),
        "manifest": asdict(manifest), "manifest_identity": asdict(manifest.artifact_identity),
        "live_preflight": asdict(live), "preflight_identity": asdict(live.structural_preflight.artifact_identity),
        "context": asdict(context), "pending_approval": asdict(pending),
        "audit": [asdict(e) for e in audit.list_events("CASE-001", run.run_id)],
        "limitation": "Review export only; no persistent ApprovalStore lifecycle or execution authority.",
    }
    output = Path("artifacts/case001") / f"d021-review-{uuid.uuid4()}.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, default=json_value, indent=2)
    print(json.dumps({
        "case_id": "CASE-001", "run_id": run.run_id, "actor": actor,
        "document_count": manifest.document_count,
        "manifest_identity": asdict(manifest.artifact_identity),
        "preflight_identity": asdict(live.structural_preflight.artifact_identity),
        "preflight_result": context.preflight_result, "target_scope_consistent": True,
        "intended_operation": context.intended_operation.value, "approval_state": pending.approval_status.value,
        "approval_id": pending.approval_id, "review_file": str(output),
        "approval_consumed": False, "source_mutation": False,
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Provider errors can contain private URLs/IDs. Emit only a safe class.
        print(f"D-021 stopped: {type(exc).__name__}; private diagnostics required")
        raise SystemExit(1) from None
