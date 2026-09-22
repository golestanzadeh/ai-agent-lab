from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_lab.agent_runtime import DEMO_ACCEPTANCE_CRITERIA, DEMO_OBJECTIVE, LocalAgentRuntime, LocalWorkPackage


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "orchestrator" / "v1"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local synthetic Agent Runtime Activation Layer")
    parser.add_argument("command", choices=("start", "resume", "inspect"))
    parser.add_argument("database", type=Path)
    parser.add_argument("artifact_root", type=Path)
    parser.add_argument("--package-id", default="RUNTIME_DEMO_001")
    args = parser.parse_args()
    runtime = LocalAgentRuntime(args.database, args.artifact_root, ROOT, CONTRACT_ROOT)
    package = LocalWorkPackage(
        package_id=args.package_id,
        objective=DEMO_OBJECTIVE,
        synthetic_inputs=("synthetic://runtime/demo-input",),
        acceptance_criteria=DEMO_ACCEPTANCE_CRITERIA,
    )
    if args.command == "start":
        result = runtime.start(package)
    elif args.command == "resume":
        result = runtime.resume(package)
    else:
        from agent_lab.orchestrator_kernel import OrchestratorKernel
        result = OrchestratorKernel.inspect_read_only(args.database)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
