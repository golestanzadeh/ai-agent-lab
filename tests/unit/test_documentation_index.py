import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
INDEX = DOCS / "README.md"
CANONICAL_STATE_FILES = (
    ROOT / "PROJECT_CHECKPOINT.md",
    ROOT / "CURRENT_STATE.md",
    ROOT / "ROADMAP.md",
    ROOT / "OPEN_ITEMS.md",
)


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

    assert "AGENT_LED_CONTINUOUS_EXECUTION_ACTIVE" in snapshot
    assert "CAPACITY_DEFERRED" in current
    assert "TOKEN_PAUSED" in current


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
    assert "No five-minute polling policy is current" in current
    assert "CAPACITY_DEFERRED" in controller
    assert "hard execution-window boundary is not itself a Human Gate" in controller


def test_case001_continuation_does_not_regress_to_completed_declaration_packages() -> None:
    current = (ROOT / "CURRENT_STATE.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    for text in (current, roadmap):
        assert "DR-01" in text and "DR-02" in text and "DR-03" in text
        assert "DR-01, DR-02 and DR-03 are `PASS`" in text
        assert "DR-05" in text and ("NOT_STARTED" in text or "blocked" in text.lower())
        assert "Exact next package is DR-01" not in text
        assert "all packages remain unstarted" not in text
    exact_next = current.split("## Exact next action", 1)[1].split("## Non-negotiable", 1)[0]
    assert "ten reviewed plausibility rules" in exact_next
    assert "exact accepted artifacts" in exact_next
    assert "DR-05" in exact_next
    assert "resume exactly at dependency-ready DR-02" not in exact_next

def test_active_e10_and_ui_records_use_current_rule_profile() -> None:
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
        assert " six-rule local plausibility" not in text
        assert " six-rule-subset" not in text
        assert "LOCAL_SIX_RULE_SUBSET_PASS" not in text


def test_canonical_current_records_use_mapping_profile_v13() -> None:
    checkpoint = (ROOT / "PROJECT_CHECKPOINT.md").read_text(encoding="utf-8")
    current = (ROOT / "CURRENT_STATE.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    snapshot = checkpoint.split("All later dated checkpoint sections", 1)[0]

    for text in (snapshot, current, roadmap):
        assert "mapping profile v14" in text or "mapping profile version 14" in text

    assert "mapping profile version 2 for the bounded Anlage N" not in current


def test_historical_p1_contract_docs_do_not_override_current_e10_readiness() -> None:
    adapter = (DOCS / "p1-eric-adapter-contract.md").read_text(encoding="utf-8")
    material = (DOCS / "p1-eric-material-process.md").read_text(encoding="utf-8")
    preview = (DOCS / "p1-synthetic-preview.md").read_text(encoding="utf-8")

    for text in (adapter, material, preview):
        assert "historical" in text
        assert "mapping profile v14" in text
        assert "thirty-nine-rule local plausibility subset" in text
        assert "ERiC-engine execution" in text

    current = (ROOT / "CURRENT_STATE.md").read_text(encoding="utf-8")
    assert "Mapping and executable plausibility validation remain fail-closed" not in current


def test_canonical_state_markers_are_identical() -> None:
    expected = {
        "CURRENT_PROJECT_STAGE": "SYNTHETIC_UI_ACCEPTED_REAL_PRODUCT_GATED",
        "CURRENT_NEXT_ACTION": "C09_R3_HG02_INCREMENTAL_EXECUTION",
        "CURRENT_ACTIVE_OPEN_ITEMS": "OI-0002..OI-0008,OI-0010,OI-0012",
    }
    for path in CANONICAL_STATE_FILES:
        text = path.read_text(encoding="utf-8")
        for key, value in expected.items():
            assert f"<!-- {key}: {value} -->" in text, path


def test_open_item_ids_are_unique_and_active_closed_are_disjoint() -> None:
    text = (ROOT / "OPEN_ITEMS.md").read_text(encoding="utf-8")
    active, closed = text.split("## Closed items (not active)", 1)
    active_ids = re.findall(r"^\| (OI-\d{4}) \|", active, flags=re.MULTILINE)
    closed_ids = re.findall(r"^- `(OI-\d{4})`", closed, flags=re.MULTILINE)
    assert len(active_ids) == len(set(active_ids))
    assert set(active_ids).isdisjoint(closed_ids)
    assert active_ids == [
        *(f"OI-{number:04d}" for number in range(2, 9)),
        "OI-0010",
        "OI-0012",
    ]
    assert "OI-0009" in closed_ids


def test_oi_0009_is_owner_terminated_and_not_an_execution_dependency() -> None:
    checkpoint = (ROOT / "PROJECT_CHECKPOINT.md").read_text(encoding="utf-8")
    current = (ROOT / "CURRENT_STATE.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    open_items = (ROOT / "OPEN_ITEMS.md").read_text(encoding="utf-8")
    decision = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    design = (DOCS / "supervisor-loop-design.md").read_text(encoding="utf-8")

    active, closed = open_items.split("## Closed items (not active)", 1)
    assert "| OI-0009 |" not in active
    assert "`OI-0009`" in closed
    for text in (checkpoint, current, roadmap, closed, decision, design):
        assert "OWNER_TERMINATED / PERMANENTLY_OUT_OF_SCOPE" in text
    for text in (checkpoint, current, roadmap, closed, decision):
        assert "not a technical PASS" in text or "not `TECHNICAL_PASS`" in text
        assert "new explicit Owner directive" in text


def test_oi_0011_is_owner_deferred_and_not_an_execution_dependency() -> None:
    checkpoint = (ROOT / "PROJECT_CHECKPOINT.md").read_text(encoding="utf-8")
    current = (ROOT / "CURRENT_STATE.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    open_items = (ROOT / "OPEN_ITEMS.md").read_text(encoding="utf-8")
    decision = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")

    active, deferred = open_items.split("## Owner-deferred decisions (not active)", 1)
    deferred = deferred.split("## Closed items (not active)", 1)[0]
    assert "| OI-0011 |" not in active
    assert "`OI-0011`" in deferred
    for text in (checkpoint, current, roadmap, deferred, decision):
        assert "OWNER_DEFERRED / OPTIONAL / NONBLOCKING" in text
        assert "not a technical PASS" in text or "not `TECHNICAL_PASS`" in text
        assert "new explicit Owner directive" in text


def test_current_acceptance_does_not_close_formal_ui25_packages() -> None:
    for path in CANONICAL_STATE_FILES:
        text = path.read_text(encoding="utf-8")
        assert "increment" in text.lower(), path
        assert "formal ui25-10" in text.lower(), path
        assert "approval/export" in text.lower(), path

    plan = (DOCS / "ui25-execution-and-acceptance-plan.md").read_text(
        encoding="utf-8"
    )
    assert "UI25-05 synthetic worker is not automatic intake dispatch" in plan
    assert "Formal Approval/Export remains disabled and unaccepted" in plan


def test_current_governance_commit_references_resolve() -> None:
    checkpoint = (ROOT / "PROJECT_CHECKPOINT.md").read_text(encoding="utf-8")
    required = (
        "9b4cec532c97483cbf072c4fc90e8bcd3cf89538",
        "f0845868218db3f0b46fc46f3c835008fed6a097",
        "4161997720fd51c9b7a9a2feebf7c096e554a8c9",
    )
    for commit in required:
        assert commit in checkpoint
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        assert result.returncode == 0, commit


def test_mandatory_current_documents_and_links_exist() -> None:
    mandatory = (
        ROOT / "AGENTS.md",
        ROOT / "PROJECT_CHECKPOINT.md",
        ROOT / "OPEN_ITEMS.md",
        ROOT / "CURRENT_STATE.md",
        ROOT / "ROADMAP.md",
        ROOT / "DECISIONS.md",
        DOCS / "ui25-execution-and-acceptance-plan.md",
        DOCS / "oi-0002-final-closure-matrix-20261012.md",
        DOCS / "case001-declaration-readiness-2024.md",
        DOCS / "case001-declaration-readiness-2024.json",
    )
    assert all(path.is_file() for path in mandatory)


def test_ui25_11_acceptance_is_not_promoted_to_independent_pass() -> None:
    checkpoint = (ROOT / "PROJECT_CHECKPOINT.md").read_text(encoding="utf-8")
    current = (ROOT / "CURRENT_STATE.md").read_text(encoding="utf-8")
    for text in (checkpoint, current):
        snapshot = text.split("## UI25-05 synthetic execution", 1)[0]
        assert "UI25-11" in snapshot
        assert "no independent UI25-11 review is claimed" in snapshot
        assert "UI25-11: INDEPENDENT_PASS" not in snapshot
