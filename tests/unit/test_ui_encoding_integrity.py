"""Reject replacement-character and placeholder-corrupted UI strings."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2] / "src" / "agent_lab"
PATTERNS = [
    re.compile(r"[?]{3,}"),
    re.compile(r"\ufffd"),
    re.compile(r"(?<![A-Za-z])[?](?:[A-Za-z]{2,})[?]"),
]
def test_ui_localization_has_no_corrupt_placeholders():
    violations = []
    for directory, pattern in (("ui_static", "*.js"), ("ui_templates", "*.html")):
        for path in (ROOT / directory).glob(pattern):
            if path.name == "htmx.min.js":
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "?" not in line and "\ufffd" not in line:
                    continue
                # A run of 3+ question marks indicates irreversible text loss.
                if PATTERNS[0].search(line) or PATTERNS[1].search(line):
                    violations.append(f"{path.name}:{number}")
    assert not violations, "Corrupted UI text: " + ", ".join(violations)
