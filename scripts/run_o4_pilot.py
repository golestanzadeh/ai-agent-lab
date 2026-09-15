"""Run or inspect the bounded local Phase O4 pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_lab.orchestrator_kernel import OrchestratorKernel
from agent_lab.orchestrator_pilot import resume_pilot, start_pilot


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "orchestrator" / "v1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "resume", "inspect"))
    parser.add_argument("database", type=Path)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    if args.action in {"start", "resume"} and args.evidence is None:
        parser.error("--evidence is required for start and resume")
    if args.action == "start":
        result = start_pilot(args.database, args.evidence, ROOT, CONTRACT_ROOT)
    elif args.action == "resume":
        result = resume_pilot(args.database, args.evidence, ROOT, CONTRACT_ROOT)
    else:
        result = OrchestratorKernel.inspect_read_only(args.database)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
