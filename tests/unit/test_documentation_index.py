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
