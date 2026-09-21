import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
INDEX = DOCS / "README.md"


def _indexed_markdown_names() -> set[str]:
    return set(
        re.findall(
            r"^- `([^`/\\]+\.md)`",
            INDEX.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
    )


def test_every_focused_document_is_registered_in_the_index() -> None:
    actual = {path.name for path in DOCS.glob("*.md") if path.name != "README.md"}
    indexed = _indexed_markdown_names()
    assert actual == indexed


def test_index_references_only_existing_focused_documents() -> None:
    for name in _indexed_markdown_names():
        assert (DOCS / name).is_file()


def test_index_preserves_the_canonical_status_entry_point() -> None:
    text = INDEX.read_text(encoding="utf-8")
    assert "Start with the repository-root `PROJECT_CHECKPOINT.md`" in text
    assert "Current CASE status must be taken only from `PROJECT_CHECKPOINT.md`" in text


def test_canonical_current_records_agree_on_latest_ui_package() -> None:
    checkpoint = (ROOT / "PROJECT_CHECKPOINT.md").read_text(encoding="utf-8")
    current = (ROOT / "CURRENT_STATE.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    snapshot = checkpoint.split("All later dated checkpoint sections", 1)[0]

    checkpoint_versions = set(re.findall(r"through UI-(\d+)", snapshot))
    current_versions = set(re.findall(r"through UI-(\d+)", current))
    roadmap_versions = set(re.findall(r"through UI-(\d+)", roadmap))
    assert len(checkpoint_versions) == len(current_versions) == len(roadmap_versions) == 1
    assert checkpoint_versions == current_versions == roadmap_versions


def test_canonical_current_records_agree_on_branch_and_execution_state() -> None:
    checkpoint = (ROOT / "PROJECT_CHECKPOINT.md").read_text(encoding="utf-8")
    current = (ROOT / "CURRENT_STATE.md").read_text(encoding="utf-8")
    snapshot = checkpoint.split("All later dated checkpoint sections", 1)[0]

    for text in (snapshot, current):
        assert "d021-agent-case-provisioning" in text

    execution_states = {"AGENT_LED_CONTINUOUS_EXECUTION_ACTIVE", "TOKEN_PAUSED"}
    checkpoint_states = {state for state in execution_states if state in snapshot}
    current_states = {state for state in execution_states if state in current}
    assert len(checkpoint_states) == len(current_states) == 1
    assert checkpoint_states == current_states


def test_current_limit_controller_allows_safe_package_chaining() -> None:
    current = (ROOT / "CURRENT_STATE.md").read_text(encoding="utf-8")
    controller = (DOCS / "plan-limit-continuation-controller.md").read_text(
        encoding="utf-8"
    )

    for text in (current, controller):
        assert "sequential" in text
        assert "at most one bounded package per heartbeat" not in text

    assert "routine heartbeat-start checks are disabled" in current
    assert "Mandatory continuation rule" in controller
    assert "No fixed package-count limit applies" in controller
    assert "five-minute cadence" in current
    assert "five-minute cadence" in controller
    assert "hard execution-window boundary is not itself a Human Gate" in controller


def test_active_e10_and_ui_records_use_twelve_rule_profile() -> None:
    active_files = (
        ROOT / "CURRENT_STATE.md",
        ROOT / "ROADMAP.md",
        DOCS / "p1-eric-e10-2024-plausibility.md",
        DOCS / "p1-eric-e10-2024-readiness.md",
        DOCS / "ui-synthetic-review-preview.md",
        DOCS / "ui-synthetic-workflow.md",
    )
    for path in active_files:
        text = path.read_text(encoding="utf-8")
        assert "six-rule" not in text
        assert "LOCAL_SIX_RULE_SUBSET_PASS" not in text


def test_historical_p1_contract_docs_do_not_override_current_e10_readiness() -> None:
    adapter = (DOCS / "p1-eric-adapter-contract.md").read_text(encoding="utf-8")
    material = (DOCS / "p1-eric-material-process.md").read_text(encoding="utf-8")
    preview = (DOCS / "p1-synthetic-preview.md").read_text(encoding="utf-8")

    for text in (adapter, material, preview):
        assert "historical" in text
        assert "mapping profile v3" in text
        assert "twelve-rule local plausibility subset" in text
        assert "ERiC-engine execution" in text

    current = (ROOT / "CURRENT_STATE.md").read_text(encoding="utf-8")
    assert "Mapping and executable plausibility validation remain fail-closed" not in current
