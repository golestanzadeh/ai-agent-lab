from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_lab.milestone_a import load_json, register_queue, validate_golden_journey
from agent_lab.orchestrator_kernel import OrchestratorKernel


def main() -> int:
    parser = argparse.ArgumentParser(description="Register the approved local synthetic Milestone A queue without dispatching it.")
    parser.add_argument("database", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    journey = load_json(root / "contracts/product/milestone-a/v1/golden-journey.json")
    authority = load_json(root / "contracts/orchestrator/v1/milestone-a-authority.json")
    journey_hash = validate_golden_journey(journey)
    with OrchestratorKernel(args.database, root / "contracts/orchestrator/v1") as kernel:
        result = register_queue(kernel, authority)
        kernel.create_checkpoint("CHECKPOINT-MILESTONE-A-REGISTERED")
    print(json.dumps({**result, "journey_hash": journey_hash}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
