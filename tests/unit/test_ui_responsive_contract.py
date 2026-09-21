from pathlib import Path

from fastapi.testclient import TestClient

from agent_lab.ui_app import create_app


ROOT = Path(__file__).resolve().parents[2]
CSS = (ROOT / "src" / "agent_lab" / "ui_static" / "app.css").read_text(encoding="utf-8")


def test_phone_document_preserves_rtl_viewport_skip_link_and_all_safety_panels() -> None:
    text = TestClient(create_app()).get("/").text
    assert '<html lang="fa" dir="rtl">' in text
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in text
    assert 'class="skip-link" href="#main"' in text
    for visible_boundary in (
        "Human Gate",
        "ارسال تولیدی مجاز و پیاده‌سازی نشده است",
        "OFFICIAL_ERIC_ENGINE_NOT_EXECUTED",
        "RECEIPT_NOT_AVAILABLE_NO_TRANSMISSION",
    ):
        assert visible_boundary in text


def test_phone_breakpoints_stack_content_without_hiding_safety_information() -> None:
    assert "@media(max-width:720px)" in CSS
    assert ".grid,.scope-strip{grid-template-columns:1fr}" in CSS
    assert ".gate{grid-template-columns:1fr}" in CSS
    assert "@media(max-width:520px){.timeline{grid-template-columns:1fr}" in CSS
    assert "display:none" not in CSS
    assert "visibility:hidden" not in CSS


def test_long_codes_touch_targets_and_keyboard_focus_remain_legible() -> None:
    assert "overflow-wrap:anywhere" in CSS
    assert "button:focus-visible" in CSS
    assert "summary:focus-visible" in CSS
    assert "button{border:0;border-radius:11px;padding:.8rem 1.1rem;font:inherit;font-weight:700;min-height:44px}" in CSS
    assert ".case-picker select" in CSS and "min-height:44px" in CSS
    assert ".diagnostics summary" in CSS and "min-height:44px" in CSS


def test_document_table_and_mixed_direction_values_are_semantic() -> None:
    text = TestClient(create_app()).get("/").text
    assert "<caption>مدارک مصنوعیِ همین پرونده و اجرای انتخاب‌شده</caption>" in text
    assert text.count('scope="col"') == 5
    assert text.count('scope="row"') == 2
    assert 'class="mono" dir="ltr"' in text
    assert '<time dir="ltr" datetime=' in text
    assert 'class="stage-index" aria-hidden="true"' in text


def test_dynamic_workspace_announces_only_a_concise_case_change() -> None:
    text = TestClient(create_app()).get("/").text
    assert '<section id="workspace" class="workspace" data-case-id=' in text
    assert 'class="sr-only" role="status" aria-live="polite" aria-atomic="true"' in text
    assert "برای سال 2024 نمایش داده شد" in text
    assert ".sr-only{position:absolute;width:1px;height:1px" in CSS
