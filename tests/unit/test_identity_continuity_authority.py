"""Synthetic-only integration with the real persistent Orchestrator Kernel."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agent_lab.identity_continuity_authority import IdentityContinuityAuthority, IdentityContinuityContext, IdentityContinuityError
from agent_lab.orchestrator_kernel import OrchestratorKernel, PermissionDenied

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "orchestrator" / "v1"
H0 = "sha256:" + "0" * 64
H1 = "sha256:" + "1" * 64


def configured(tmp_path, *, case="CASE-SYNTHETIC", year=2025, run="RUN-SYNTHETIC-1"):
    kernel = OrchestratorKernel(tmp_path / "kernel" / "control.sqlite", CONTRACT_ROOT)
    now = datetime.now(timezone.utc)
    task_id, manifest_id, actor = "TASK-ID-1", "MAN-ID-1", "IDENTITY-SERVICE-1"
    context = {"case_id":case,"tax_year":year,"run_id":run}
    with kernel._connection:
        kernel._connection.execute(
            "INSERT INTO tasks(task_id,parent_task_id,role_id,actor_instance_id,repository,ref,status,payload_json,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (task_id,None,"IMPLEMENTATION_AGENT",actor,"repo","ref","ACTIVE",json.dumps({"case_context":context}),now.isoformat(),(now+timedelta(hours=1)).isoformat()),
        )
        kernel._connection.execute(
            "INSERT INTO manifests(manifest_id,actor_instance_id,task_id,role_id,state,payload_json,issued_at,expires_at) VALUES(?,?,?,?,?,?,?,?)",
            (manifest_id,actor,task_id,"IMPLEMENTATION_AGENT","ACTIVE",json.dumps({"scope":{"case_context":context}}),now.isoformat(),(now+timedelta(hours=1)).isoformat()),
        )
        kernel._connection.execute("UPDATE kill_switch SET state='RUNNING'")
    ctx = IdentityContinuityContext("DEPLOYMENT-SYNTHETIC",case,year,task_id,manifest_id,run,"IDENTITY_COMMIT")
    return kernel, IdentityContinuityAuthority(kernel,ctx), ctx


def test_real_kernel_monotonic_commit_restart_and_rollback(tmp_path):
    kernel, authority, ctx = configured(tmp_path)
    authority.initialize(H0); authority.reserve(0,H0,H1); authority.finalize(0,H1); authority.verify(1,H1)
    kernel.close()
    reopened = OrchestratorKernel(tmp_path / "kernel" / "control.sqlite",CONTRACT_ROOT)
    IdentityContinuityAuthority(reopened,ctx).verify(1,H1)
    with pytest.raises(IdentityContinuityError): IdentityContinuityAuthority(reopened,ctx).verify(0,H0)
    reopened.close()


def test_crash_boundaries_and_deterministic_reconciliation(tmp_path):
    kernel, authority, ctx = configured(tmp_path)
    authority.initialize(H0); authority.reserve(0,H0,H1); kernel.close()
    reopened = OrchestratorKernel(tmp_path / "kernel" / "control.sqlite",CONTRACT_ROOT)
    pending = IdentityContinuityAuthority(reopened,ctx)
    with pytest.raises(IdentityContinuityError): pending.verify(0,H0)
    pending.reconcile(1,H1); pending.verify(1,H1)
    reopened.close()


def test_exact_case_task_manifest_binding(tmp_path):
    kernel, authority, ctx = configured(tmp_path)
    authority.initialize(H0)
    bad = IdentityContinuityContext(ctx.deployment_id,"OTHER",ctx.tax_year,ctx.task_id,ctx.manifest_id,ctx.run_id,ctx.operation)
    with pytest.raises(PermissionDenied): IdentityContinuityAuthority(kernel,bad).reserve(0,H0,H1)
    bad = IdentityContinuityContext(ctx.deployment_id,ctx.case_id,ctx.tax_year,"OTHER",ctx.manifest_id,ctx.run_id,ctx.operation)
    with pytest.raises(PermissionDenied): IdentityContinuityAuthority(kernel,bad).reserve(0,H0,H1)
    kernel.close()


def test_unauthorized_initialization_is_rejected(tmp_path):
    kernel, authority, ctx = configured(tmp_path)
    with pytest.raises(PermissionDenied):
        kernel.initialize_identity_continuity(
            deployment_id=ctx.deployment_id, case_id=ctx.case_id, tax_year=ctx.tax_year,
            manifest_id="ATTACKER", task_id=ctx.task_id, run_id=ctx.run_id,
            operation=ctx.operation, head=H0,
        )
    authority.initialize(H0)
    with pytest.raises(IdentityContinuityError, match="already initialized"):
        authority.initialize(H1)
    kernel.close()

def test_governed_restore_is_exact_expiring_and_one_time(tmp_path):
    kernel,_,ctx=configured(tmp_path)
    expires=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
    values=dict(authorization_id="RESTORE-1",deployment_id="DEPLOYMENT-SYNTHETIC",case_id="CASE-SYNTHETIC",tax_year=2025,backup_digest=H0,expected_epoch=3,expected_head=H1,target_generation=4,operator_id="IDENTITY-SERVICE-1")
    governed={"manifest_id":ctx.manifest_id,"task_id":ctx.task_id,"run_id":ctx.run_id,"operation":"IDENTITY_RESTORE"}
    with kernel._connection:
        kernel._connection.execute("INSERT INTO task_human_gates VALUES(?, 'IDENTITY_RESTORE', 'APPROVED', ?, ?)",(ctx.task_id,"OWNER-SYNTHETIC-RESTORE",datetime.now(timezone.utc).isoformat()))
    with pytest.raises(PermissionDenied): kernel.register_identity_restore_authorization(**values,**governed,expires_at=expires,owner_authority_reference="OWNER-FORGED")
    kernel.register_identity_restore_authorization(**values,**governed,expires_at=expires,owner_authority_reference="OWNER-SYNTHETIC-RESTORE")
    with pytest.raises(PermissionDenied): kernel.consume_identity_restore_authorization(**{**values,**governed,"backup_digest":H1})
    with pytest.raises(PermissionDenied,match="operator"):
        kernel.consume_identity_restore_authorization(**{**values,**governed,"operator_id":"ATTACKER"})
    kernel.consume_identity_restore_authorization(**values,**governed)
    with pytest.raises(PermissionDenied): kernel.consume_identity_restore_authorization(**values,**governed)
    kernel.close()


def test_restore_requires_active_kernel_context_and_approved_gate(tmp_path):
    kernel,_,ctx=configured(tmp_path)
    expires=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
    values=dict(authorization_id="RESTORE-UNAUTHORIZED",deployment_id=ctx.deployment_id,case_id=ctx.case_id,tax_year=ctx.tax_year,backup_digest=H0,expected_epoch=0,expected_head=H0,target_generation=1,operator_id="RECOVERY-OPERATOR",expires_at=expires,owner_authority_reference="OWNER-SYNTHETIC-RESTORE",manifest_id=ctx.manifest_id,task_id=ctx.task_id,run_id=ctx.run_id,operation="IDENTITY_RESTORE")
    with pytest.raises(PermissionDenied,match="Human Gate"):
        kernel.register_identity_restore_authorization(**values)
    with pytest.raises(PermissionDenied):
        kernel.register_identity_restore_authorization(**{**values,"manifest_id":"ATTACKER"})
    kernel.close()
