import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agent_lab.c09_transaction_state import (
    C09TransactionError, DurableC09TransactionState, InjectedCrash,
)
from agent_lab.c09_witness_protocol import WitnessError
from agent_lab.identity_continuity_authority import IdentityContinuityContext
from agent_lab.orchestrator_kernel import OrchestratorKernel, PermissionDenied


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "orchestrator" / "v2"
KEY = b"synthetic-c09-r1-key"


class SyntheticWitness:
    def __init__(self):
        self.objects = {}
        self.available = True
        self.verify_ok = True
        self.timeout_after_create = False

    def append_or_resolve(self, record):
        if not self.available:
            raise WitnessError("witness unavailable")
        existing = self.objects.get(record.object_key)
        if existing is not None:
            if existing[1] != record.to_bytes():
                raise WitnessError("conflicting witness record")
            return existing[0]
        generation = str(len(self.objects) + 101)
        self.objects[record.object_key] = (generation, record.to_bytes())
        if self.timeout_after_create:
            self.timeout_after_create = False
            raise WitnessError("ambiguous provider timeout")
        return generation

    def verify_exact(self, record, generation):
        if not self.available or not self.verify_ok:
            raise WitnessError("independent reader verification failed")
        if self.objects.get(record.object_key) != (generation, record.to_bytes()):
            raise WitnessError("witness readback mismatch")


def configured(tmp_path, *, capabilities=("identity_create",)):
    kernel_path = tmp_path / "kernel.sqlite"
    kernel = OrchestratorKernel(kernel_path, CONTRACT_ROOT)
    now = datetime.now(timezone.utc)
    case = {"case_id": "TEST-C09-R1", "tax_year": 2025, "run_id": "RUN-C09-R1"}
    payload = {"scope": {"case_context": case}, "requested_capabilities": list(capabilities)}
    with kernel._connection:
        kernel._connection.execute(
            "INSERT INTO tasks(task_id,parent_task_id,role_id,actor_instance_id,repository,ref,status,payload_json,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            ("TASK-C09", None, "IDENTITY_ADMINISTRATION_AGENT", "IDENTITY-SYNTHETIC", "repo", "ref", "ACTIVE", json.dumps({"case_context": case}), now.isoformat(), (now + timedelta(hours=1)).isoformat()),
        )
        kernel._connection.execute(
            "INSERT INTO manifests(manifest_id,actor_instance_id,task_id,role_id,state,payload_json,issued_at,expires_at) VALUES(?,?,?,?,?,?,?,?)",
            ("MAN-C09", "IDENTITY-SYNTHETIC", "TASK-C09", "IDENTITY_ADMINISTRATION_AGENT", "ACTIVE", json.dumps(payload), now.isoformat(), (now + timedelta(hours=1)).isoformat()),
        )
        kernel._connection.execute("UPDATE kill_switch SET state='RUNNING'")
    context = IdentityContinuityContext("DEPLOYMENT-C09", case["case_id"], 2025, "TASK-C09", "MAN-C09", case["run_id"], "IDENTITY_COMMIT")
    witness = SyntheticWitness()
    state_path = tmp_path / "identity-state.sqlite"
    state = DurableC09TransactionState(state_path, kernel, context, witness, KEY)
    state.initialize()
    return kernel_path, kernel, context, witness, state_path, state


def test_r1_i01_i02_happy_path_is_durable_and_acknowledges_only_after_kernel_commit(tmp_path):
    _, kernel, _, _, _, state = configured(tmp_path)
    result = state.begin(transaction_id="TX-1", operation_id="OP-1", capability="identity_create", payload={"ref": "synthetic://one"})
    assert result.state == "COMMITTED" and not result.acknowledged
    assert result.receipt_digest.startswith("sha256:") and result.witness_generation == "101"
    assert state.acknowledge("TX-1").state == "ACKNOWLEDGED"
    state.close(); kernel.close()


@pytest.mark.parametrize("boundary", ["PENDING", "IDENTITY_COMMITTED", "WITNESSED", "COMMITTED"])
def test_r1_i04_process_termination_at_every_boundary_recovers_exactly_once(tmp_path, boundary):
    kernel_path, kernel, context, witness, state_path, state = configured(tmp_path)
    with pytest.raises(InjectedCrash, match=boundary):
        state.begin(transaction_id="TX-CRASH", operation_id="OP-CRASH", capability="identity_create", payload={"ref": "synthetic://crash"}, stop_after=boundary)
    state.close(); kernel.close()
    reopened_kernel = OrchestratorKernel(kernel_path, CONTRACT_ROOT)
    reopened = DurableC09TransactionState(state_path, reopened_kernel, context, witness, KEY)
    result = reopened.recover("TX-CRASH")
    assert result.state == "COMMITTED" and len(witness.objects) == 1
    assert reopened.acknowledge("TX-CRASH").acknowledged
    reopened.close(); reopened_kernel.close()


def test_r1_i04_timeout_after_create_recovers_without_duplicate(tmp_path):
    _, kernel, _, witness, _, state = configured(tmp_path)
    witness.timeout_after_create = True
    with pytest.raises(WitnessError, match="ambiguous"):
        state.begin(transaction_id="TX-TIMEOUT", operation_id="OP-TIMEOUT", capability="identity_create", payload={"ref": "synthetic://timeout"})
    assert state.result("TX-TIMEOUT").state == "IDENTITY_COMMITTED"
    assert state.recover("TX-TIMEOUT").state == "COMMITTED"
    assert len(witness.objects) == 1
    state.close(); kernel.close()


def test_r1_i04_reader_failure_and_missing_credentials_never_acknowledge(tmp_path):
    _, kernel, _, witness, _, state = configured(tmp_path)
    witness.verify_ok = False
    with pytest.raises(WitnessError, match="verification"):
        state.begin(transaction_id="TX-VERIFY", operation_id="OP-VERIFY", capability="identity_create", payload={"ref": "synthetic://verify"})
    with pytest.raises(C09TransactionError, match="cannot be acknowledged"):
        state.acknowledge("TX-VERIFY")
    witness.available = False
    with pytest.raises(WitnessError, match="unavailable"):
        state.recover("TX-VERIFY")
    assert not state.result("TX-VERIFY").acknowledged
    state.close(); kernel.close()


def test_r1_i02_replay_duplicate_and_conflicting_receipt_are_rejected(tmp_path):
    _, kernel, _, _, _, state = configured(tmp_path)
    first = state.begin(transaction_id="TX-REPLAY", operation_id="OP-REPLAY", capability="identity_create", payload={"ref": "synthetic://same"})
    again = state.begin(transaction_id="TX-REPLAY", operation_id="OP-REPLAY", capability="identity_create", payload={"ref": "synthetic://same"})
    assert first.receipt_digest == again.receipt_digest
    with pytest.raises(C09TransactionError, match="conflicting"):
        state.begin(transaction_id="TX-REPLAY", operation_id="OP-REPLAY", capability="identity_create", payload={"ref": "synthetic://changed"})
    with pytest.raises(C09TransactionError, match="conflicting"):
        state.begin(transaction_id="TX-OTHER", operation_id="OP-REPLAY", capability="identity_create", payload={"ref": "synthetic://same"})
    state.close(); kernel.close()


def test_r1_i03_capabilities_are_defined_default_deny_and_never_granted(tmp_path):
    matrix = json.loads((CONTRACT_ROOT / "permission-matrix.json").read_text(encoding="utf-8"))
    for capability in ("identity_backup", "identity_restore"):
        assert matrix["capabilities"][capability] == {
            "maximum_tier": "A4", "case_run_required": True,
            "human_gate_required": True, "no_standing_agent_permission": True,
        }
        assert all(capability not in role for role in matrix["role_permissions"])
    _, kernel, _, _, _, state = configured(tmp_path, capabilities=("identity_create", "identity_backup", "identity_restore"))
    for capability in ("identity_backup", "identity_restore"):
        with pytest.raises(PermissionDenied, match="no operational grant"):
            state.begin(transaction_id="TX-" + capability, operation_id="OP-" + capability, capability=capability, payload={})
    with pytest.raises(PermissionDenied, match="Kernel denied"):
        state.begin(transaction_id="TX-FORGED", operation_id="OP-FORGED", capability="identity_update", payload={})
    state.close(); kernel.close()
