"""Explicit opt-in local functional-test launcher; never production."""
from __future__ import annotations

import os
from pathlib import Path

from agent_lab.ui_dashboard import create_dashboard_app
from agent_lab.ui_functional_test_store import FunctionalTestStore


def create_functional_test_app():
    if os.environ.get("AI_TAX_UI_FUNCTIONAL_TEST") != "I_UNDERSTAND_TEST_ONLY":
        raise RuntimeError("Functional test mode requires explicit opt-in")
    db_path = Path(os.environ.get("AI_TAX_UI_TEST_DB", str(Path.home() / ".ai-tax-agent" / "ui-functional-test.sqlite3")))
    if any(segment.casefold() in {"google drive","onedrive","dropbox"} for segment in db_path.parts):
        raise RuntimeError("Test database cannot be stored in a synced folder")
    return create_dashboard_app(test_store=FunctionalTestStore(db_path))
