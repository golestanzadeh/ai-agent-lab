import json
import threading
from concurrent.futures import ThreadPoolExecutor
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
        self.complete_listing = True
        self.listing_limit = None

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

    def read_complete_chain(self, deployment_id):
        if not self.available or not self.complete_listing:
            raise WitnessError("complete witness enumeration unavailable")
        ordered = sorted(
            (value for key, value in self.objects.items() if f"/{deployment_id}/" in key),
            key=lambda value: json.loads(value[1])["sequence"],
        )
        if self.listing_limit is not None:
            raise WitnessError("complete witness enumeration unavailable")
        return tuple(ordered)


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


@pytest.mark.parametrize("boundary", ["PREPARED", "PENDING", "IDENTITY_COMMITTED", "WITNESS_STAGED", "WITNESSED", "COMMITTED"])
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
    assert state.result("TX-TIMEOUT").state == "WITNESS_STAGED"
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


def test_kernel_reservation_failure_cannot_mutate_identity_or_witness(tmp_path, monkeypatch):
    _, kernel, _, witness, _, state = configured(tmp_path)
    original = state.authority.reserve
    monkeypatch.setattr(state.authority, "reserve", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("reserve failed")))
    with pytest.raises(RuntimeError, match="reserve failed"):
        state.begin(transaction_id="TX-NO-RESERVE", operation_id="OP-NO-RESERVE", capability="identity_create", payload={"ref": "synthetic://blocked"})
    row = state.db.execute("SELECT state FROM c09_transaction WHERE transaction_id='TX-NO-RESERVE'").fetchone()
    identity = state.db.execute("SELECT epoch FROM identity_state").fetchone()
    assert row["state"] == "PREPARED" and identity["epoch"] == 0 and witness.objects == {}
    monkeypatch.setattr(state.authority, "reserve", original)
    assert state.recover("TX-NO-RESERVE").state == "COMMITTED"
    state.close(); kernel.close()


@pytest.mark.parametrize("damage", ["missing", "rewritten", "wrong-generation", "reader-outage"])
def test_restart_fails_closed_when_committed_witness_is_unverifiable(tmp_path, damage):
    kernel_path, kernel, context, witness, state_path, state = configured(tmp_path)
    state.begin(transaction_id="TX-DAMAGE", operation_id="OP-DAMAGE", capability="identity_create", payload={"ref": "synthetic://damage"})
    record_key = next(iter(witness.objects))
    if damage == "missing":
        witness.objects.clear()
    elif damage == "rewritten":
        generation, payload = witness.objects[record_key]
        witness.objects[record_key] = (generation, payload + b" ")
    elif damage == "wrong-generation":
        generation, payload = witness.objects[record_key]
        witness.objects[record_key] = (str(int(generation) + 1), payload)
    else:
        witness.available = False
    state.close(); kernel.close()
    reopened_kernel = OrchestratorKernel(kernel_path, CONTRACT_ROOT)
    with pytest.raises((WitnessError, C09TransactionError)):
        DurableC09TransactionState(state_path, reopened_kernel, context, witness, KEY)
    reopened_kernel.close()


def test_truncated_local_witness_chain_is_rejected_after_restart(tmp_path):
    kernel_path, kernel, context, witness, state_path, state = configured(tmp_path)
    state.begin(transaction_id="TX-FIRST", operation_id="OP-FIRST", capability="identity_create", payload={"ref": "synthetic://first"})
    state.begin(transaction_id="TX-SECOND", operation_id="OP-SECOND", capability="identity_create", payload={"ref": "synthetic://second"})
    state.db.execute("DELETE FROM c09_transaction WHERE transaction_id='TX-FIRST'")
    state.close(); kernel.close()
    reopened_kernel = OrchestratorKernel(kernel_path, CONTRACT_ROOT)
    with pytest.raises(C09TransactionError, match="head disagrees|truncated"):
        DurableC09TransactionState(state_path, reopened_kernel, context, witness, KEY)
    reopened_kernel.close()


def test_canonical_witness_bytes_are_durable_before_provider_append(tmp_path):
    _, kernel, _, witness, _, state = configured(tmp_path)
    witness.available = False
    with pytest.raises(WitnessError, match="unavailable"):
        state.begin(transaction_id="TX-STAGED", operation_id="OP-STAGED", capability="identity_create", payload={"ref": "synthetic://staged"})
    row = state.db.execute("SELECT state,witness_bytes,witness_generation FROM c09_transaction WHERE transaction_id='TX-STAGED'").fetchone()
    assert row["state"] == "WITNESS_STAGED" and row["witness_bytes"] and row["witness_generation"] is None
    witness.available = True
    assert state.recover("TX-STAGED").state == "COMMITTED"
    state.close(); kernel.close()


@pytest.mark.parametrize("successors", [1, 2])
def test_coordinated_local_rollback_cannot_hide_external_successors(tmp_path, successors):
    import shutil

    kernel_path, kernel, context, witness, state_path, state = configured(tmp_path)
    state.begin(transaction_id="TX-BASE", operation_id="OP-BASE", capability="identity_create", payload={"ref": "synthetic://base"})
    state.acknowledge("TX-BASE")
    state.close(); kernel.close()
    kernel_snapshot = tmp_path / "kernel.snapshot"
    state_snapshot = tmp_path / "identity.snapshot"
    shutil.copy2(kernel_path, kernel_snapshot)
    shutil.copy2(state_path, state_snapshot)
    for index in range(successors):
        kernel = OrchestratorKernel(kernel_path, CONTRACT_ROOT)
        state = DurableC09TransactionState(state_path, kernel, context, witness, KEY)
        state.begin(transaction_id=f"TX-TAIL-{index}", operation_id=f"OP-TAIL-{index}", capability="identity_create", payload={"ref": f"synthetic://tail/{index}"})
        state.acknowledge(f"TX-TAIL-{index}")
        state.close(); kernel.close()
    shutil.copy2(kernel_snapshot, kernel_path)
    shutil.copy2(state_snapshot, state_path)
    rolled_kernel = OrchestratorKernel(kernel_path, CONTRACT_ROOT)
    with pytest.raises(C09TransactionError, match="head disagrees"):
        DurableC09TransactionState(state_path, rolled_kernel, context, witness, KEY)
    rolled_kernel.close()


def test_partial_or_stale_external_enumeration_fails_closed(tmp_path):
    kernel_path, kernel, context, witness, state_path, state = configured(tmp_path)
    state.begin(transaction_id="TX-LIST", operation_id="OP-LIST", capability="identity_create", payload={"ref": "synthetic://list"})
    state.close(); kernel.close()
    reopened_kernel = OrchestratorKernel(kernel_path, CONTRACT_ROOT)
    witness.listing_limit = 0
    with pytest.raises(WitnessError, match="enumeration unavailable"):
        DurableC09TransactionState(state_path, reopened_kernel, context, witness, KEY)
    witness.listing_limit = None
    witness.complete_listing = False
    with pytest.raises(WitnessError, match="enumeration unavailable"):
        DurableC09TransactionState(state_path, reopened_kernel, context, witness, KEY)
    reopened_kernel.close()


def test_r2_t03_concurrent_same_predecessor_allows_exactly_one_successor(tmp_path, monkeypatch):
    kernel_path, kernel, context, witness, state_path, state = configured(tmp_path)
    state.close(); kernel.close()
    barrier = threading.Barrier(2)
    original_next_head = DurableC09TransactionState._next_head

    def synchronized_next_head(current, transaction_id, payload_digest):
        result = original_next_head(current, transaction_id, payload_digest)
        barrier.wait(timeout=10)
        return result

    monkeypatch.setattr(DurableC09TransactionState, "_next_head", staticmethod(synchronized_next_head))

    def attempt(index):
        local_kernel = OrchestratorKernel(kernel_path, CONTRACT_ROOT)
        local_state = DurableC09TransactionState(state_path, local_kernel, context, witness, KEY)
        try:
            return local_state.begin(
                transaction_id=f"TX-CONCURRENT-{index}", operation_id=f"OP-CONCURRENT-{index}",
                capability="identity_create", payload={"ref": f"synthetic://concurrent/{index}"},
            ).state
        except Exception as exc:
            return type(exc).__name__
        finally:
            local_state.close(); local_kernel.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, (1, 2)))
    assert outcomes.count("COMMITTED") == 1
    assert len(witness.objects) == 1
    check_kernel = OrchestratorKernel(kernel_path, CONTRACT_ROOT)
    row = check_kernel._connection.execute("SELECT epoch,pending_json FROM identity_continuity").fetchone()
    assert row["epoch"] == 1 and row["pending_json"] is None
    check_kernel.close()


@pytest.mark.parametrize("column,value", [
    ("receipt_json", "{}"),
    ("receipt_digest", "sha256:" + "f" * 64),
])
def test_r2_t05_restart_rejects_altered_durable_receipt(tmp_path, column, value):
    kernel_path, kernel, context, witness, state_path, state = configured(tmp_path)
    state.begin(transaction_id="TX-RECEIPT", operation_id="OP-RECEIPT", capability="identity_create", payload={"ref": "synthetic://receipt"})
    state.db.execute(f"UPDATE c09_transaction SET {column}=? WHERE transaction_id='TX-RECEIPT'", (value,))
    state.close(); kernel.close()
    reopened_kernel = OrchestratorKernel(kernel_path, CONTRACT_ROOT)
    with pytest.raises(C09TransactionError, match="receipt"):
        DurableC09TransactionState(state_path, reopened_kernel, context, witness, KEY)
    reopened_kernel.close()


def test_r2_t05_restart_rejects_validly_signed_wrong_backup_generation(tmp_path):
    from dataclasses import replace

    kernel_path, kernel, context, witness, state_path, state = configured(tmp_path)
    state.begin(transaction_id="TX-BACKUP", operation_id="OP-BACKUP", capability="identity_create", payload={"ref": "synthetic://backup"})
    key = next(iter(witness.objects))
    generation, payload = witness.objects[key]
    from agent_lab.c09_witness_protocol import WitnessRecord
    altered = replace(WitnessRecord.from_bytes(payload, KEY), backup_generation=7).signed(KEY).to_bytes()
    witness.objects[key] = (generation, altered)
    state.db.execute("UPDATE c09_transaction SET witness_bytes=? WHERE transaction_id='TX-BACKUP'", (altered,))
    state.close(); kernel.close()
    reopened_kernel = OrchestratorKernel(kernel_path, CONTRACT_ROOT)
    with pytest.raises(C09TransactionError, match="semantics"):
        DurableC09TransactionState(state_path, reopened_kernel, context, witness, KEY)
    reopened_kernel.close()
