"""UI25-01 read-only dashboard: explicit authority, never synthetic live fallback."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import FastAPI, HTTPException, Request
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


def create_dashboard_app(*, read_cases: ReadCases | None = None) -> FastAPI:
    """Expose a fail-closed dashboard; caller must inject an authorized live resolver.

    This is not a substitute for the Kernel's permission or persistence layer.
    No fake cases, inferred 2024 status or case data are returned by default.
    """
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
    async def dashboard(request: Request, case_id: str | None = None):
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
        return templates.TemplateResponse(request=request, name="dashboard.html", context={
            "state": state, "cases": cases, "selected": selected,
        })

    @app.get("/health")
    async def health():
        return {"status": "ok", "mode": "read-only-dashboard", "source": "configured" if read_cases else "unavailable"}

    return app
