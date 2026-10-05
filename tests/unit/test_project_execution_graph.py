import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agent_lab.plan_limit_controller import CapacityState, evaluate_capacity, fresh_observation
from agent_lab.orchestrator_kernel import OrchestratorKernel
from agent_lab.project_execution_graph import NextAuthorizedAction, ProjectGraphError, TechnicalRecoverable, arm_capacity_continuation, build_hot_context, load_graph, next_authorized_action, notification_decision, run_closed_loop_action, run_until_boundary
from agent_lab.elster_dry_run import ApprovalStatus, ContentReleaseApproval, DestinationTransmissionApproval
from test_durable_approval import make_store

ROOT = Path(__file__).resolve().parents[2]
GRAPH = ROOT / "contracts/project-execution/v1/master-execution-graph.json"
NOTIFICATION = ROOT / "contracts/project-execution/v1/notification-contract.json"
NOW = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)


def capacity(five=98, weekly=74):
    obs = fresh_observation(five, weekly, observed_at=NOW, five_hour_resets_at=NOW + timedelta(hours=4), weekly_resets_at=NOW + timedelta(days=4))
    return evaluate_capacity(obs, now=NOW)


def test_graph_selects_exact_dr04_without_dispatching():
    graph = load_graph(GRAPH)
    action = next_authorized_action(graph, branch=graph["branch"], repository_safe=True, recovery_checkpoint="ad4f69f", capacity=capacity(), now=NOW)
    assert action.outcome == "READY_PACKAGE"
    assert action.action_id == "DR-04-REMEDIATE-AND-ACCEPT"
    assert action.cost_class == "BOUNDED"


def test_graph_fails_closed_on_ambiguous_ready_action():
    graph = load_graph(GRAPH)
    graph["nodes"][5]["status"] = "READY"
    graph["nodes"][6]["depends_on"] = ["R5-CLOSED-LOOP"]
    with pytest.raises(ProjectGraphError, match="ambiguous"):
        next_authorized_action(graph, branch=graph["branch"], repository_safe=True, recovery_checkpoint="x", capacity=capacity(), now=NOW)


def test_graph_rejects_forward_or_unknown_dependency(tmp_path):
    graph = load_graph(GRAPH)
    graph["nodes"][0]["depends_on"] = ["DR-03-REGISTER-AND-COMPLETE"]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(graph), encoding="utf-8")
    with pytest.raises(ProjectGraphError, match="dependency"):
        load_graph(path)


@pytest.mark.parametrize("five,weekly,expected", [(15, 74, CapacityState.TOKEN_PAUSED.value), (98, 10, CapacityState.TOKEN_PAUSED.value)])
def test_capacity_stop_precedes_selection(five, weekly, expected):
    graph = load_graph(GRAPH)
    action = next_authorized_action(graph, branch=graph["branch"], repository_safe=True, recovery_checkpoint="x", capacity=capacity(five, weekly), now=NOW)
    assert action.outcome == expected
    assert action.action_id == "DR-04-REMEDIATE-AND-ACCEPT"
    assert action.cost_class == "BOUNDED"
    assert action.reset_timestamp is not None


def test_repository_mismatch_stops_closed():
    graph = load_graph(GRAPH)
    action = next_authorized_action(graph, branch="main", repository_safe=True, recovery_checkpoint="x", capacity=capacity(), now=NOW)
    assert action.outcome == "STOP_DIAGNOSTIC"


def test_existing_kernel_hosts_read_only_next_action_query(tmp_path):
    contract_root = ROOT / "contracts/orchestrator/v1"
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", contract_root) as kernel:
        kernel.create_checkpoint("CHECKPOINT-R6")
        before = kernel._connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
        action = kernel.next_authorized_project_action(GRAPH, branch="d021-agent-case-provisioning", repository_safe=True, capacity=capacity(), now=NOW)
        after = kernel._connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
    assert action.action_id == "DR-04-REMEDIATE-AND-ACCEPT"
    assert before == after


def test_hot_context_is_deterministic_and_hash_bound():
    graph = load_graph(GRAPH)
    action = next_authorized_action(graph, branch=graph["branch"], repository_safe=True, recovery_checkpoint="checkpoint", capacity=capacity(), now=NOW)
    observation = {"five_hour_remaining_percent":98,"weekly_remaining_percent":74,"five_hour_resets_at":"2026-10-05T01:39:36Z","weekly_resets_at":"2026-10-11T10:37:32Z"}
    first = build_hot_context(graph, action, head="ad4f69f", capacity_observation=observation)
    second = build_hot_context(graph, action, head="ad4f69f", capacity_observation=observation)
    assert first == second
    changed = build_hot_context(graph, action, head="different", capacity_observation=observation)
    assert changed["context_digest"] != first["context_digest"]


def test_notification_requires_ordered_article_one_approvals_and_deduplicates():
    contract = json.loads(NOTIFICATION.read_text(encoding="utf-8"))
    assert notification_decision(contract, event="HUMAN_REQUIRED", event_identity="GATE-1", stage_one=False, stage_two=False, delivered_identities=()) == "ARTICLE_1_STAGE_ONE_REQUIRED"
    assert notification_decision(contract, event="HUMAN_REQUIRED", event_identity="GATE-1", stage_one=True, stage_two=False, delivered_identities=()) == "ARTICLE_1_STAGE_TWO_REQUIRED"
    assert notification_decision(contract, event="HUMAN_REQUIRED", event_identity="GATE-1", stage_one=True, stage_two=True, delivered_identities=()) == "AUTHORIZED_ONCE"
    assert notification_decision(contract, event="HUMAN_REQUIRED", event_identity="GATE-1", stage_one=True, stage_two=True, delivered_identities=("GATE-1",)) == "DEDUPLICATED"
    assert notification_decision(contract, event="PACKAGE_PASS", event_identity="P-1", stage_one=True, stage_two=True, delivered_identities=()) == "NOT_ELIGIBLE"
    with pytest.raises(ProjectGraphError, match="exact booleans"):
        notification_decision(contract, event="HUMAN_REQUIRED", event_identity="GATE-2", stage_one=1, stage_two=True, delivered_identities=())


def test_selected_node_cost_class_cannot_be_bypassed():
    graph = load_graph(GRAPH)
    action = next_authorized_action(graph, branch=graph["branch"], repository_safe=True, recovery_checkpoint="x", capacity=capacity(30, 30), now=NOW)
    assert action.outcome == "CAPACITY_DEFERRED"
    assert action.action_id == "DR-04-REMEDIATE-AND-ACCEPT"


def test_closed_loop_executes_repairs_accepts_checkpoints_reopens_and_arms(tmp_path):
    database = tmp_path / "kernel.sqlite3"
    calls = []
    failed = {"value": False}
    def execute(action):
        calls.append(("execute", action))
        if not failed["value"]:
            failed["value"] = True
            raise TechnicalRecoverable("injected")
    with OrchestratorKernel(database, ROOT / "contracts/orchestrator/v1") as kernel:
        result = run_closed_loop_action(kernel=kernel, action_id="SYNTHETIC-A", execute=execute, remediate=lambda a,e: calls.append(("remediate",a)), run_tests=lambda a: True, independent_accept=lambda a: True, publish_checkpoint=lambda c: calls.append(("publish",c)), checkpoint_id="CHECKPOINT-A")
        assert result.remediation_count == 1
        armed = []
        pause = arm_capacity_continuation(kernel=kernel, action_id="SYNTHETIC-B", capacity_state="CAPACITY_DEFERRED", cost_class="BOUNDED", reset_timestamp="2026-10-05T01:39:36+00:00", checkpoint_id="CHECKPOINT-A", arm=lambda a,r: armed.append((a,r)), verify=lambda a,r: armed == [(a,r)])
        assert pause.outcome == "CAPACITY_DEFERRED"
    with OrchestratorKernel(database, ROOT / "contracts/orchestrator/v1") as reopened:
        assert reopened.recover_latest_checkpoint()["checkpoint_id"] == "CHECKPOINT-A"
        reopened.verify_audit_chain()
    assert calls == [("execute","SYNTHETIC-A"),("remediate","SYNTHETIC-A"),("execute","SYNTHETIC-A"),("publish","CHECKPOINT-A")]


def test_scheduler_binding_is_single_and_reset_aligned():
    binding = json.loads((ROOT / "contracts/project-execution/v1/scheduler-binding.json").read_text(encoding="utf-8-sig"))
    assert binding["logical_identity"] == "plan-limit-continuation-guard"
    assert binding["duplicate_count"] == 0
    assert binding["capacity_pause_policy"].startswith("ONE_RESET_ALIGNED_WAKE")
    assert "actual reset timestamp" in binding["arm_preconditions"]


def test_scheduler_arm_failure_is_durable(tmp_path):
    database=tmp_path/"kernel.sqlite3"
    with OrchestratorKernel(database,ROOT/"contracts/orchestrator/v1") as kernel:
        with pytest.raises(ProjectGraphError,match="SCHEDULER_ARM_FAILURE"):
            arm_capacity_continuation(kernel=kernel,action_id="A",capacity_state="CAPACITY_DEFERRED",cost_class="BOUNDED",reset_timestamp="2026-10-05T01:39:36+00:00",checkpoint_id="C",arm=lambda a,r:None,verify=lambda a,r:False)
        row=kernel._connection.execute("SELECT event_type FROM audit_events WHERE event_type='SCHEDULER_ARM_FAILURE'").fetchone()
        assert row["event_type"] == "SCHEDULER_ARM_FAILURE"
        kernel.verify_audit_chain()


def test_notification_audit_enforces_approvals_uses_kernel_chain_and_deduplicates(tmp_path):
    contract = json.loads(NOTIFICATION.read_text(encoding="utf-8"))
    _,_,approval_store=make_store(tmp_path / "approval.sqlite3")
    content=ContentReleaseApproval("SYNTH-NOTIFY-CONTENT","SYNTH-HUMAN-1","CASE-2024-0001","RUN-00000001","sha256:test","1","OPERATIONAL_NON_SENSITIVE","OWNER_EXCEPTION_NOTIFICATION",NOW,NOW+timedelta(hours=1),ApprovalStatus.APPROVED)
    destination=DestinationTransmissionApproval("SYNTH-NOTIFY-DEST","SYNTH-HUMAN-2",content.approval_id,content.case_id,content.run_id,content.artifact_reference,"1",contract["destination_reference"],"EMAIL",content.purpose,NOW,NOW+timedelta(hours=1),False,ApprovalStatus.APPROVED)
    approval_store.register_submission_approval(content); approval_store.register_submission_approval(destination)
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", ROOT / "contracts/orchestrator/v1") as kernel:
        from agent_lab.orchestrator_kernel import PermissionDenied
        with pytest.raises(PermissionDenied):
            kernel.record_governed_notification_audit(contract=contract,event_identity="GATE-0",event_class="HUMAN_REQUIRED",state="DELIVERED",content_hash="sha256:no",actor_id="SYNTHETIC_TEST",original_blocker="GATE-0",approval_store=approval_store,content_approval_id=content.approval_id,destination_approval_id=destination.approval_id,artifact_version="1",case_id=content.case_id,run_id=content.run_id,purpose=content.purpose,destination_identity=destination.destination_identity,now=NOW)
        args=dict(contract=contract,event_identity="GATE-1",event_class="HUMAN_REQUIRED",state="DELIVERED",content_hash="sha256:test",actor_id="SYNTHETIC_TEST",original_blocker="GATE-1",approval_store=approval_store,content_approval_id=content.approval_id,destination_approval_id=destination.approval_id,artifact_version="1",case_id=content.case_id,run_id=content.run_id,purpose=content.purpose,destination_identity=destination.destination_identity,now=NOW)
        assert kernel.record_governed_notification_audit(**args) == "DELIVERED"
        assert kernel.record_governed_notification_audit(**args) == "DEDUPLICATED"
        kernel.verify_audit_chain()
    approval_store.close()


def test_notification_binds_contract_destination_and_limits_one_retry(tmp_path):
    contract=json.loads(NOTIFICATION.read_text(encoding="utf-8")); _,_,store=make_store(tmp_path/"a.sqlite3")
    content=ContentReleaseApproval("SYNTH-C2","SYNTH-H1","CASE-2024-0001","RUN-00000001","sha256:x","1","OPERATIONAL_NON_SENSITIVE","OWNER_EXCEPTION_NOTIFICATION",NOW,NOW+timedelta(hours=1),ApprovalStatus.APPROVED)
    wrong=DestinationTransmissionApproval("SYNTH-D2","SYNTH-H2",content.approval_id,content.case_id,content.run_id,content.artifact_reference,"1","OTHER_EMAIL","EMAIL",content.purpose,NOW,NOW+timedelta(hours=1),True,ApprovalStatus.APPROVED)
    store.register_submission_approval(content);store.register_submission_approval(wrong)
    common=dict(contract=contract,event_identity="GATE-X",event_class="HUMAN_REQUIRED",state="DELIVERY_FAILED",content_hash="sha256:x",actor_id="SYNTHETIC_TEST",original_blocker="GATE-X",approval_store=store,content_approval_id=content.approval_id,destination_approval_id=wrong.approval_id,artifact_version="1",case_id=content.case_id,run_id=content.run_id,purpose=content.purpose,destination_identity=wrong.destination_identity,now=NOW)
    from agent_lab.orchestrator_kernel import PermissionDenied
    with OrchestratorKernel(tmp_path/"k.sqlite3",ROOT/"contracts/orchestrator/v1") as kernel:
        with pytest.raises(PermissionDenied,match="binding mismatch"):
            kernel.record_governed_notification_audit(**common)
    store.close()

    _,_,store=make_store(tmp_path/"b.sqlite3"); right=replace(wrong,approval_id="SYNTH-D3",destination_identity=contract["destination_reference"])
    store.register_submission_approval(content);store.register_submission_approval(right)
    common.update(approval_store=store,destination_approval_id=right.approval_id,destination_identity=right.destination_identity)
    with OrchestratorKernel(tmp_path/"k2.sqlite3",ROOT/"contracts/orchestrator/v1") as kernel:
        assert kernel.record_governed_notification_audit(**common) == "DELIVERY_FAILED"
        assert kernel.record_governed_notification_audit(**common) == "DELIVERY_FAILED"
        assert kernel.record_governed_notification_audit(**common) == "RETRY_BUDGET_EXHAUSTED"
    store.close()


def test_stale_capacity_fails_closed():
    graph = load_graph(GRAPH)
    stale_now = NOW + timedelta(hours=1)
    action = next_authorized_action(graph, branch=graph["branch"], repository_safe=True, recovery_checkpoint="x", capacity=capacity(), now=stale_now)
    assert action.outcome == "UNKNOWN_PAUSED"


def test_both_window_deferral_uses_later_relevant_reset():
    graph=load_graph(GRAPH)
    next(node for node in graph["nodes"] if node["id"]=="DR-04-REMEDIATE-AND-ACCEPT")["cost_class"]="EXPENSIVE"
    action=next_authorized_action(graph,branch=graph["branch"],repository_safe=True,recovery_checkpoint="x",capacity=capacity(50,25),now=NOW)
    assert action.outcome == "CAPACITY_DEFERRED"
    assert action.reset_timestamp == (NOW+timedelta(days=4)).isoformat()


def test_closed_loop_continues_without_owner_prompt_until_capacity_boundary(tmp_path):
    queue = [
        NextAuthorizedAction("READY_PACKAGE","A","AUTH","SATISFIED","NONE","BOUNDED","START","sha256:g"),
        NextAuthorizedAction("READY_PACKAGE","B","AUTH","SATISFIED","NONE","BOUNDED","START","sha256:g"),
        NextAuthorizedAction("CAPACITY_DEFERRED","C","AUTH","SATISFIED","NONE","BOUNDED","AUTO-2-B","sha256:g","2026-10-05T01:39:36+00:00"),
    ]
    published=[]; armed=[]
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", ROOT / "contracts/orchestrator/v1") as kernel:
        result=run_until_boundary(kernel=kernel,derive_next=lambda:queue.pop(0),execute=lambda a:None,remediate=lambda a,e:None,run_tests=lambda a:True,independent_accept=lambda a:True,publish_checkpoint=lambda c:published.append(c),arm_scheduler=lambda a,r:armed.append((a,r)),verify_scheduler=lambda a,r:armed==[(a,r)],max_actions=5)
        kernel.verify_audit_chain()
    assert result.outcome == "CAPACITY_DEFERRED"
    assert result.completed_actions == ("A","B")
    assert published == ["AUTO-1-A","AUTO-2-B"]
    assert armed == [("C","2026-10-05T01:39:36+00:00")]


def test_unknown_pause_is_durable_without_invented_reset(tmp_path):
    decision=NextAuthorizedAction("UNKNOWN_PAUSED","C","AUTH","SATISFIED","NONE","BOUNDED","CHECKPOINT","sha256:g",None)
    with OrchestratorKernel(tmp_path/"kernel.sqlite3",ROOT/"contracts/orchestrator/v1") as kernel:
        result=run_until_boundary(kernel=kernel,derive_next=lambda:decision,execute=lambda a:None,remediate=lambda a,e:None,run_tests=lambda a:True,independent_accept=lambda a:True,publish_checkpoint=lambda c:None,arm_scheduler=lambda a,r:None,verify_scheduler=lambda a,r:True,max_actions=1)
        assert result.outcome == "UNKNOWN_PAUSED"
        assert kernel._connection.execute("SELECT COUNT(*) FROM audit_events WHERE event_type='UNKNOWN_CAPACITY_PAUSE'").fetchone()[0] == 1
