"""Loopback-only synthetic FastAPI/Jinja/HTMX prototype."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agent_lab.case_registry import (
    AssessmentMode,
    CaseRecord,
    CaseRegistry,
    CaseType,
    LifecycleStatus,
    OwnerType,
    StorageScopeReference,
    TaxPeriod,
)
from agent_lab.ui_state_contract import (
    HumanGateStatus,
    HumanGateView,
    UIStateError,
    UIWorkspaceState,
    select_synthetic_workspace,
)
from agent_lab.ui_workflow_contract import build_synthetic_ui_workflow
from agent_lab.ui_document_contract import build_synthetic_document_inventory
from agent_lab.ui_review_contract import build_synthetic_review
from agent_lab.ui_decision_contract import build_synthetic_decision_queue
from agent_lab.ui_submission_readiness_contract import build_synthetic_submission_readiness
from agent_lab.ui_support_contract import build_synthetic_ui_support
from agent_lab.ui_status_labels import persian_status_label


UI_ROOT = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(UI_ROOT / "ui_templates"))
TEMPLATES.env.filters["status_label"] = persian_status_label
LOCAL_SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
        "form-action 'none'; base-uri 'none'"
    ),
    "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


def _reference(character: str) -> str:
    return "sha256:" + character * 64


def build_synthetic_registry() -> CaseRegistry:
    """Return isolated synthetic examples; no persistent or external source is read."""
    registry = CaseRegistry()
    now = datetime(2026, 9, 15, tzinfo=timezone.utc)
    examples = (
        ("SYNTH-CASE-001", "SYNTH-PERSON-001", 2024, LifecycleStatus.REVIEW_REQUIRED),
        ("SYNTH-CASE-002", "SYNTH-PERSON-002", 2025, LifecycleStatus.PROCESSING),
    )
    for case_id, owner_id, year, status in examples:
        registry.register(
            CaseRecord(
                case_id=case_id,
                owner_type=OwnerType.PERSON,
                owner_id=owner_id,
                tax_period=TaxPeriod("CALENDAR_YEAR", year),
                case_type=CaseType.INDIVIDUAL,
                assessment_mode=AssessmentMode.INDIVIDUAL_ASSESSMENT,
                lifecycle_status=status,
                storage_scope_reference=StorageScopeReference("SYNTHETIC", case_id),
                schema_version=1,
                created_at=now,
                updated_at=now,
            )
        )
    return registry


def _populate_synthetic_state(state: UIWorkspaceState) -> UIWorkspaceState:
    suffix = state.case_id.rsplit("-", 1)[-1]
    gate = HumanGateView(
        status=HumanGateStatus.REQUIRED,
        action="REVIEW_SYNTHETIC_PREVIEW",
        artifact_reference=_reference("d" if suffix == "001" else "e"),
        destination="LOCAL_SYNTHETIC_PREVIEW",
        expires_at=datetime(2026, 12, 31, tzinfo=timezone.utc),
    )
    return state.with_case_scoped_content(
        case_id=state.case_id,
        run_id=f"SYNTH-RUN-{suffix}",
        document_references=(_reference("a"), _reference("b")),
        finding_references=(_reference("c"),),
        evidence_gap_codes=(
            "OFFICIAL_ERIC_ENGINE_NOT_EXECUTED",
            "REAL_PAYLOAD_NOT_AUTHORIZED",
        ),
        preview_reference=gate.artifact_reference,
        human_gate=gate,
    )


def create_app(*, registry: CaseRegistry | None = None) -> FastAPI:
    case_registry = registry or build_synthetic_registry()
    app = FastAPI(
        title="AI Agent Lab — Synthetic UI Prototype",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.case_registry = case_registry
    app.mount("/static", StaticFiles(directory=str(UI_ROOT / "ui_static")), name="static")

    @app.middleware("http")
    async def local_security_headers(request: Request, call_next):
        response = await call_next(request)
        for name, value in LOCAL_SECURITY_HEADERS.items():
            response.headers[name] = value
        return response

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        cases = case_registry.all_records()
        selected = _populate_synthetic_state(
            select_synthetic_workspace(
                case_registry,
                case_id=cases[0].case_id,
                tax_year=cases[0].tax_period.year,
            )
        )
        return TEMPLATES.TemplateResponse(
            request=request,
            name="index.html",
            context={"cases": cases, "workspace": selected, "workflow": build_synthetic_ui_workflow(selected), "documents": build_synthetic_document_inventory(selected), "review": build_synthetic_review(selected), "decisions": build_synthetic_decision_queue(selected), "readiness": build_synthetic_submission_readiness(selected), "support": build_synthetic_ui_support(selected)},
        )

    @app.get("/workspace", response_class=HTMLResponse)
    async def workspace(request: Request, case_id: str, tax_year: int) -> HTMLResponse:
        try:
            selected = _populate_synthetic_state(
                select_synthetic_workspace(
                    case_registry, case_id=case_id, tax_year=tax_year
                )
            )
        except UIStateError as error:
            raise HTTPException(status_code=404, detail="پروندهٔ مصنوعی معتبر پیدا نشد") from error
        return TEMPLATES.TemplateResponse(
            request=request,
            name="_workspace.html",
            context={"workspace": selected, "workflow": build_synthetic_ui_workflow(selected), "documents": build_synthetic_document_inventory(selected), "review": build_synthetic_review(selected), "decisions": build_synthetic_decision_queue(selected), "readiness": build_synthetic_submission_readiness(selected), "support": build_synthetic_ui_support(selected)},
        )

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok", "mode": "synthetic-local-only"}

    return app


app = create_app()
