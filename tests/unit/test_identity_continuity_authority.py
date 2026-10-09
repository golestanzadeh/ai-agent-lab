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
