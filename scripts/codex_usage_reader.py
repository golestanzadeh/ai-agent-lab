"""Write normalized Codex usage telemetry to local runtime state."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_lab.codex_usage_reader import read_codex_usage, write_snapshot


def main() -> None:
    snapshot = read_codex_usage()
    output = Path(".runtime/usage/CODEX_USAGE.json")
    write_snapshot(snapshot, output)
    print(output)


if __name__ == "__main__":
    main()
