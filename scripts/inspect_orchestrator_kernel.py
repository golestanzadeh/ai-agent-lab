"""Read-only inspection entry point for an explicit Orchestrator Kernel database."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_lab.orchestrator_kernel import IntegrityError, OrchestratorKernel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path, help="Exact existing Kernel SQLite database")
    args = parser.parse_args()
    try:
        result = OrchestratorKernel.inspect_read_only(args.database)
    except (OSError, IntegrityError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"status": "PASS", **result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
