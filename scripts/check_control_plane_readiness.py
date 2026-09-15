"""Evaluate an explicit non-secret Phase O5 readiness evidence file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_lab.control_plane_readiness import ReadinessEvidenceError, evaluate_readiness


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.evidence.read_text(encoding="utf-8"))
        result = evaluate_readiness(payload)
    except (OSError, json.JSONDecodeError, ReadinessEvidenceError) as exc:
        print(json.dumps({"outcome": "BLOCKED", "ready": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0 if result.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
