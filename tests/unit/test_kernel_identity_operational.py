"""Real Kernel task/gate/manifest APIs and separate Identity SQLite authority."""
from datetime import datetime,timedelta,timezone
from copy import deepcopy
from pathlib import Path
import base64

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec,utils
from agent_lab.orchestrator_kernel import OrchestratorKernel,PermissionDenied
from agent_lab.identity_logical_continuity import H,ORDER,enrollment_preimage
from test_orchestrator_kernel import task,manifest
from test_identity_logical_runtime import store_at,owner_artifact,OWNER,KERNEL

ROOT=Path(__file__).parents[2]/"contracts/orchestrator/v2"


def bootstrap(tmp_path):
    identity=store_at(tmp_path/"identity.sqlite")
    owner=owner_artifact(identity);now=datetime.now(timezone.utc)
    fmt=lambda t:t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    owner.update(issued_at=fmt(now),not_before=fmt(now),expires_at=fmt(now+timedelta(minutes=5)))
    r,s=utils.decode_dss_signature(OWNER.sign(enrollment_preimage(owner),ec.ECDSA(hashes.SHA256())))
    owner["signature"]=base64.urlsafe_b64encode(r.to_bytes(32,"big")+min(s,ORDER-s).to_bytes(32,"big")).rstrip(b"=").decode()
    logical=identity.enroll_logical_identity(owner)
    kernel=OrchestratorKernel(tmp_path/"kernel.sqlite",ROOT)
    work=task(task_id=owner["bootstrap_task_id"],role_id=owner["bootstrap_role_id"],actor_instance_id=owner["bootstrap_actor_instance_id"],permissions=["inspect_operational_metadata"])
    work["inputs"]=[H(owner)]
    kernel.register_task(work,gate_triggers=["IDENTITY_ENROLLMENT"])
    kernel.record_human_gate_decision(work["task_id"],"IDENTITY_ENROLLMENT","APPROVED",actor_id="HUMAN_PROJECT_OWNER",authority_reference=H(owner))
    grant=manifest(work,manifest_id=owner["bootstrap_manifest_id"],tiers=["A1"])
    kernel.register_manifest(grant);kernel.validate_manifest(grant["manifest_id"])
    kernel.set_kill_switch("RUNNING",actor_id="HUMAN_PROJECT_OWNER",authority_reference="TEST-OWNER-ONLY")
    kernel.activate_manifest(grant["manifest_id"])
    state=kernel.bind_identity_enrollment(owner,OWNER.public_key(),"TEST-OWNER-KEY")
    return kernel,identity,owner,state


def issue(kernel,owner,**changes):
    kwargs=dict(deployment_id=owner["deployment_id"],manifest_id=owner["bootstrap_manifest_id"],task_id=owner["bootstrap_task_id"],run_id=owner["bootstrap_run_id"],case_id="*",tax_year="*",operation="READ_ENROLLMENT_STATUS",payload={"enrollment_id":owner["enrollment_id"],"owner_authorization_digest":H(owner)},authorization_references=[H(owner)],signing_key=KERNEL,key_id="TEST-KERNEL-KEY-1")
    kwargs.update(changes)
    return kernel.issue_identity_read(**kwargs)


def test_actual_kernel_owner_broker_proof_and_identity_metadata(tmp_path):
    kernel,identity,owner,state=bootstrap(tmp_path)
    try:
        assert state["status"]=="GENESIS_PENDING"
        assert kernel.permission_decision(owner["bootstrap_manifest_id"],"identity_enrollment_status").outcome=="HUMAN_REQUIRED"
        request=issue(kernel,owner)
        assert request["capability"]=="identity_enrollment_status"
        response=identity.read_operational_identity(request,allowed_case_ids=frozenset())
        assert response["outcome"]=="ENROLLMENT_READY" and "items" not in response["result"]
        assert response["identity_head"]==state["logical_head"]
        kernel._verify_identity_protocol_state();identity._verify_logical_integrity()
        with pytest.raises(PermissionError):identity.read_operational_identity(request,allowed_case_ids=frozenset())
        with pytest.raises(PermissionDenied):issue(kernel,owner,operation="READ_FACTS",case_id="C1",tax_year=2025)
    finally:identity.close();kernel.close()


@pytest.mark.parametrize("change",[{"authorization_references":[]},{"case_id":"C1"},{"task_id":"OTHER"},{"run_id":"OTHER"}])
def test_bootstrap_does_not_widen_identity_read(tmp_path,change):
    kernel,identity,owner,state=bootstrap(tmp_path)
    try:
        with pytest.raises(PermissionDenied):issue(kernel,owner,**change)
    finally:identity.close();kernel.close()


def test_kill_switch_blocks_proof_before_transport(tmp_path):
    kernel,identity,owner,state=bootstrap(tmp_path)
    try:
        kernel.set_kill_switch("HALTED",actor_id="HUMAN_PROJECT_OWNER",authority_reference="TEST-STOP")
        with pytest.raises(PermissionDenied):issue(kernel,owner)
        assert kernel._connection.execute("SELECT count(*) FROM identity_kernel_request").fetchone()[0]==0
    finally:identity.close();kernel.close()
