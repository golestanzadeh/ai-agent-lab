from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "scripts" / "start_local_ui.cmd"
FUNCTIONAL_LAUNCHER = ROOT / "scripts" / "start_functional_ui_test.cmd"


def _launcher_text() -> str:
    return LAUNCHER.read_text(encoding="utf-8")


def test_launcher_is_repository_relative_and_loopback_only() -> None:
    text = _launcher_text()
    assert 'cd /d "%~dp0.."' in text
    assert 'set "PYTHONPATH=%CD%\\src"' in text
    assert "agent_lab.ui_product_app:app" in text
    assert "--host 127.0.0.1" in text
    assert 'start "" "http://127.0.0.1:8000"' in text


def test_launcher_contains_no_public_binding_external_url_or_secret_input() -> None:
    text = _launcher_text().lower()
    for forbidden in (
        "0.0.0.0",
        "--host ::",
        "https://",
        "elster.de",
        "finanzamt",
        "password",
        "token",
        "credential",
        "manufacturer-id",
        "/submit",
    ):
        assert forbidden not in text


def test_launcher_explains_the_visible_stop_boundary() -> None:
    text = _launcher_text()
    assert "Close this window to stop the local interface." in text
    assert "Protected case data remains unavailable until an accepted runtime injects the CaseRegistry source." in text
    assert "No external connection was attempted." in text


def test_functional_launcher_connects_existing_test_store_and_kernel() -> None:
    text = FUNCTIONAL_LAUNCHER.read_text(encoding="utf-8")
    assert 'set "AI_TAX_UI_TEST_DB=%LOCALAPPDATA%\\AI-Tax-Agent\\ui-functional-test.sqlite3"' in text
    assert 'set "AI_TAX_UI_KERNEL_DB=%LOCALAPPDATA%\\AI-Tax-Agent\\ui-functional-kernel.sqlite3"' in text
    assert "agent_lab.ui_functional_test_app:create_functional_test_app --factory" in text
    assert "--host 127.0.0.1" in text
