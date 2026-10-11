"""UI25-01 read-only dashboard: explicit authority, never synthetic live fallback."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agent_lab.ui_app import LOCAL_SECURITY_HEADERS, UI_ROOT


@dataclass(frozen=True, slots=True)
class DashboardCase:
    case_id: str
    tax_year: int
    status: str

    def __post_init__(self):
        if not self.case_id.strip() or self.case_id.startswith("SYNTH-"):
            raise ValueError("live dashboard requires a non-synthetic case identifier")
        if not 1900 <= self.tax_year <= 9999:
            raise ValueError("invalid tax year")
        if self.status not in {"CREATED", "ACTIVE", "PROCESSING", "REVIEW_REQUIRED", "COMPLETED", "ARCHIVED", "BLOCKED"}:
            raise ValueError("unverified lifecycle status")


class DashboardUnavailable(RuntimeError):
    """No independently verified, owner-authorized metadata source is connected."""


ReadCases = Callable[[], tuple[DashboardCase, ...]]


def create_dashboard_app(*, read_cases: ReadCases | None = None, test_store=None) -> FastAPI:
    """Expose a fail-closed dashboard; caller must inject an authorized live resolver.

    This is not a substitute for the Kernel's permission or persistence layer.
    No fake cases, inferred 2024 status or case data are returned by default.
    """
    if test_store is not None and read_cases is not None:
        raise ValueError("test store and live case resolver must never be mixed")
    if test_store is not None:
        read_cases = test_store.cases
    app = FastAPI(title="AI-Tax-Agent Dashboard", docs_url=None, redoc_url=None, openapi_url=None)
    templates = Jinja2Templates(directory=str(UI_ROOT / "ui_templates"))
    app.mount("/static", StaticFiles(directory=str(UI_ROOT / "ui_static")), name="static")

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        for name, value in LOCAL_SECURITY_HEADERS.items():
            response.headers[name] = value
        return response

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request, case_id: str | None = None, tab: str = "overview"):
        tabs = {"overview", "cases", "family", "documents", "analysis", "issues", "result", "declaration", "approval", "activity"}
        if tab not in tabs:
            raise HTTPException(status_code=404, detail="Unknown workspace tab")
        state = "unavailable"
        cases: tuple[DashboardCase, ...] = ()
        selected = None
        if read_cases is not None:
            try:
                loaded = read_cases()
                if not isinstance(loaded, tuple) or any(not isinstance(item, DashboardCase) for item in loaded):
                    raise DashboardUnavailable("invalid source response")
                ids = [item.case_id for item in loaded]
                if len(set(ids)) != len(ids):
                    raise DashboardUnavailable("ambiguous case identities")
                cases = tuple(sorted(loaded, key=lambda item: (-item.tax_year, item.case_id)))
                state = "connected"
                if case_id is not None and case_id not in ids:
                    raise HTTPException(status_code=404, detail="Case not found")
                selected = next((item for item in cases if item.case_id == case_id), None) if case_id else (cases[0] if cases else None)
            except DashboardUnavailable:
                if case_id is not None:
                    raise HTTPException(status_code=503, detail="Verified case source unavailable")
                state = "unavailable"
                cases = ()
                selected = None
        elif case_id is not None:
            raise HTTPException(status_code=503, detail="Verified case source unavailable")
        detail = None
        if test_store is not None and selected is not None:
            detail = test_store.detail(selected.case_id)
        return templates.TemplateResponse(request=request, name="dashboard.html", context={
            "state": state, "cases": cases, "selected": selected, "tab": tab,
            "test_mode": test_store is not None, "detail": detail,
        })

    def require_test():
        if test_store is None:
            raise HTTPException(status_code=404, detail="Test operations unavailable")

    @app.post("/test/cases")
    async def create_test_case(case_id: str = Form(...), tax_year: int = Form(...)):
        require_test()
        try:
            test_store.create_case(case_id, tax_year)
        except (ValueError, __import__("sqlite3").IntegrityError):
            raise HTTPException(status_code=400, detail="Invalid or duplicate test case")
        return RedirectResponse("/?tab=cases&case_id="+case_id, status_code=303)

    @app.post("/test/documents")
    async def add_test_document(case_id: str = Form(...), label: str = Form(...), document: UploadFile = File(...)):
        require_test()
        data = await document.read(2_000_001)
        try:
            added = test_store.add_document(case_id, label, data)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid test document or case")
        return RedirectResponse("/?tab=documents&case_id="+case_id+"&added="+str(int(added)), status_code=303)

    @app.post("/test/issues")
    async def create_test_issue(case_id: str = Form(...), question: str = Form(...)):
        require_test()
        try:
            test_store.add_issue(case_id, question)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid test question or case")
        return RedirectResponse("/?tab=issues&case_id="+case_id, status_code=303)

    @app.post("/test/issues/answer")
    async def answer_test_issue(case_id: str = Form(...), issue_id: int = Form(...), answer: str = Form(...)):
        require_test()
        try:
            test_store.answer_issue(case_id, issue_id, answer)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid test issue or answer")
        return RedirectResponse("/?tab=issues&case_id="+case_id, status_code=303)

    @app.get("/health")
    async def health():
        return {"status": "ok", "mode": "isolated-functional-test" if test_store is not None else "read-only-dashboard", "source": "test-only" if test_store is not None else ("configured" if read_cases else "unavailable")}

    return app
