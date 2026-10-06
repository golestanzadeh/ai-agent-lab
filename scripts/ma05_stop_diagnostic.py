"""Write a closed, privacy-safe MA-05 CI STOP diagnostic after test failure."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from agent_lab.orchestrator_kernel import CONTRACT_SET_ID, OrchestratorKernel


def persist_stop_diagnostic(output_root: Path) -> dict[str, object]:
    output_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "diagnostic_id": "STOP-MA05-CI-FAILURE",
        "category": "VERIFICATION_FAILURE",
        "summary": "MA-05 synthetic acceptance workflow failed",
        "impact": "MA-05 is not accepted; no successor work or external action is authorized",
        "automated_recovery": "No automatic retry or project mutation was performed",
        "required_next_action": "Inspect the failed CI step, repair within MA-05 authority, rerun all acceptance checks, and require independent acceptance",
        "continuation_point": "github-actions://"
        + os.environ.get("GITHUB_REPOSITORY", "local/unknown")
        + "/runs/"
        + os.environ.get("GITHUB_RUN_ID", "UNKNOWN")
        + "@"
        + os.environ.get("GITHUB_SHA", "UNKNOWN"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    database = output_root / "ma05-ci-kernel.sqlite3"
    with OrchestratorKernel(database, Path("contracts/orchestrator/v1")) as kernel:
        kernel.record_stop_diagnostic(payload)
        checkpoint_hash = kernel.create_checkpoint("CHECKPOINT-MA05-CI-FAILURE")
        recovered = kernel.recover_latest_checkpoint()
    record = {
        "schema_version": 1,
        "kernel_contract_set": CONTRACT_SET_ID,
        "checkpoint_id": recovered["checkpoint_id"],
        "checkpoint_hash": checkpoint_hash,
        "diagnostic": payload,
        "authoritative": False,
        "purpose": "CI recovery evidence only; never executable authority",
    }
    (output_root / "ma05-ci-stop-diagnostic.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return record


def main() -> None:
    persist_stop_diagnostic(Path("artifacts/ma05-ci-stop"))


if __name__ == "__main__":
    main()
