import json

from agent_lab.orchestrator_kernel import OrchestratorKernel
from scripts.ma05_stop_diagnostic import persist_stop_diagnostic


def test_failure_diagnostic_uses_existing_kernel_and_recovers(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "synthetic/ai-agent-lab")
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    output = tmp_path / "stop"
    record = persist_stop_diagnostic(output)
    assert record["authoritative"] is False
    assert record["diagnostic"]["category"] == "VERIFICATION_FAILURE"
    assert record["diagnostic"]["continuation_point"].endswith("/runs/12345@" + "a" * 40)
    assert json.loads((output / "ma05-ci-stop-diagnostic.json").read_text())["checkpoint_hash"] == record["checkpoint_hash"]
    with OrchestratorKernel(output / "ma05-ci-kernel.sqlite3", "contracts/orchestrator/v1") as kernel:
        recovered = kernel.recover_latest_checkpoint()
    rows = recovered["snapshot"]["stop_diagnostics"]
    assert len(rows) == 1
    assert json.loads(rows[0]["payload_json"]) == record["diagnostic"]
