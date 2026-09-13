"""Case-scoped manager runtime for coordinated German tax agents."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from agent_lab.tax_agents import (
    AgentFinding, AgentReport, AgentRunStatus, AgentSpec, AgentTask,
    FindingStatus, TaxAgentRole, chief_tax_auditor_spec, default_tax_agent_specs,
)


class TaxAgentBackend(Protocol):
    def run(self, spec: AgentSpec, task: AgentTask) -> AgentReport: ...


class TaxAgentRuntimeError(RuntimeError):
    pass


class TaxAgentBlockedError(TaxAgentRuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class TaxAgentRunResult:
    case_id: str
    tax_year: int
    reports: tuple[AgentReport, ...]
    status: AgentRunStatus

    @property
    def final_report(self) -> AgentReport:
        return self.reports[-1]


class TaxAgentOrchestrator:
    """Manager-pattern orchestrator with explicit handoffs and terminal gates."""

    def __init__(self, backend: TaxAgentBackend, *, specs: tuple[AgentSpec, ...] | None = None) -> None:
        self._backend = backend
        self._specs = specs or default_tax_agent_specs()
        self._validate_graph()

    def run(self, *, case_id: str, tax_year: int, goal: str, case_packet: dict[str, object]) -> TaxAgentRunResult:
        if not case_id.strip():
            raise ValueError("case_id is required")
        if tax_year < 1900:
            raise ValueError("tax_year is invalid")
        packet_case = case_packet.get("case_id")
        if packet_case is not None and packet_case != case_id:
            raise TaxAgentRuntimeError("case_packet belongs to another case")
        packet_year = case_packet.get("tax_year")
        if packet_year is not None and int(packet_year) != tax_year:
            raise TaxAgentRuntimeError("case_packet belongs to another tax year")

        reports: list[AgentReport] = []
        for spec in self._specs:
            task = AgentTask(
                case_id=case_id,
                tax_year=tax_year,
                goal=goal,
                case_packet=case_packet,
                prior_reports=tuple(reports),
            )
            report = self._backend.run(spec, task)
            self._validate_report(spec, report)
            reports.append(report)
            if report.status == AgentRunStatus.BLOCKED:
                if spec.role == TaxAgentRole.EVIDENCE and not self._has_consequential_evidence_conflict(report):
                    reports[-1] = self._normalize_evidence_gap_status(report, "blocked_evidence_gap_nonterminal")
                    continue
                return TaxAgentRunResult(case_id, tax_year, tuple(reports), report.status)
            if report.status == AgentRunStatus.HUMAN_REQUIRED:
                if self._is_terminal_human_gate(spec, report):
                    return TaxAgentRunResult(case_id, tax_year, tuple(reports), report.status)
                reports[-1] = self._normalize_evidence_gap_status(report, "human_required_evidence_gap_nonterminal")

        return TaxAgentRunResult(case_id, tax_year, tuple(reports), AgentRunStatus.PASS)

    @staticmethod
    def _is_terminal_human_gate(spec: AgentSpec, report: AgentReport) -> bool:
        # Evidence gaps are normal outputs; only explicit consequential findings stop the run.
        if spec.role == TaxAgentRole.EVIDENCE:
            return any(f.status == FindingStatus.HUMAN_REQUIRED for f in report.findings)
        return True

    @staticmethod
    def _has_consequential_evidence_conflict(report: AgentReport) -> bool:
        return any(f.status == FindingStatus.HUMAN_REQUIRED for f in report.findings)

    @staticmethod
    def _normalize_evidence_gap_status(report: AgentReport, reason: str) -> AgentReport:
        return AgentReport(
            role=report.role, status=AgentRunStatus.PASS, summary=report.summary,
            findings=report.findings, evidence_gaps=report.evidence_gaps,
            challenges=report.challenges, next_action=report.next_action,
            metadata={**dict(report.metadata), "escalation_normalized": reason},
        )

    def _validate_graph(self) -> None:
        if not self._specs:
            raise ValueError("at least one agent is required")
        roles = [spec.role for spec in self._specs]
        if len(set(roles)) != len(roles):
            raise ValueError("duplicate agent roles")
        for index, spec in enumerate(self._specs):
            expected = self._specs[index + 1].role if index + 1 < len(self._specs) else None
            if spec.handoff_to != expected:
                raise ValueError(f"invalid handoff from {spec.role.value}")

    @staticmethod
    def _validate_report(spec: AgentSpec, report: AgentReport) -> None:
        if report.role != spec.role:
            raise TaxAgentRuntimeError("backend returned report for wrong role")
        for finding in report.findings:
            if finding.status == FindingStatus.CONFIRMED:
                if spec.role in {TaxAgentRole.LAW, TaxAgentRole.OPPORTUNITY, TaxAgentRole.CALCULATION, TaxAgentRole.REVIEWER, TaxAgentRole.FORM}:
                    if not finding.legal_refs:
                        raise TaxAgentRuntimeError(f"confirmed finding lacks legal source: {finding.finding_id}")
                if spec.role != TaxAgentRole.LAW and not finding.evidence_refs:
                    raise TaxAgentRuntimeError(f"confirmed finding lacks evidence: {finding.finding_id}")
            if spec.role == TaxAgentRole.FORM and finding.status == FindingStatus.CONFIRMED and not finding.form_refs:
                raise TaxAgentRuntimeError(f"confirmed form finding lacks form reference: {finding.finding_id}")


@dataclass(frozen=True, slots=True)
class ChiefTaxAuditResult:
    specialist_run: TaxAgentRunResult
    chief_report: AgentReport
    status: AgentRunStatus


class ChiefTaxAuditOrchestrator:
    """Supervisory manager: specialists investigate; Chief challenges and decides closure."""

    def __init__(self, backend: TaxAgentBackend, *, max_investigation_rounds: int = 2) -> None:
        if max_investigation_rounds < 1:
            raise ValueError("max_investigation_rounds must be >= 1")
        self._backend = backend
        self._chief_spec = chief_tax_auditor_spec()
        self._specialists = TaxAgentOrchestrator(backend)
        self._max_rounds = max_investigation_rounds

    def run(self, *, case_id: str, tax_year: int, goal: str, case_packet: dict[str, object]) -> ChiefTaxAuditResult:
        specialist_run = self._specialists.run(
            case_id=case_id, tax_year=tax_year, goal=goal, case_packet=case_packet
        )
        chief_task = AgentTask(
            case_id=case_id, tax_year=tax_year,
            goal=(goal + "\nPerform final suspicion pass. Reject premature closure; identify residual suspicious areas "
                  "and issue concrete specialist re-check directives when warranted."),
            case_packet=case_packet, prior_reports=specialist_run.reports,
        )
        chief_report = self._backend.run(self._chief_spec, chief_task)
        TaxAgentOrchestrator._validate_report(self._chief_spec, chief_report)
        status = chief_report.status
        return ChiefTaxAuditResult(specialist_run, chief_report, status)


def _report_to_payload(report: AgentReport) -> dict[str, object]:
    return asdict(report)


def _task_payload(task: AgentTask) -> dict[str, object]:
    return {
        "case_id": task.case_id,
        "tax_year": task.tax_year,
        "goal": task.goal,
        "case_packet": dict(task.case_packet),
        "prior_reports": [_report_to_payload(report) for report in task.prior_reports],
    }


_REPORT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": [x.value for x in AgentRunStatus]},
        "summary": {"type": "string"},
        "findings": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "finding_id": {"type": "string"}, "title": {"type": "string"},
                "status": {"type": "string", "enum": [x.value for x in FindingStatus]},
                "amount_eur": {"type": ["number", "null"]},
                "tax_effect_eur": {"type": ["number", "null"]},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "legal_refs": {"type": "array", "items": {"type": "string"}},
                "form_refs": {"type": "array", "items": {"type": "string"}},
                "rationale": {"type": "string"},
            },
            "required": ["finding_id", "title", "status", "amount_eur", "tax_effect_eur",
                         "evidence_refs", "legal_refs", "form_refs", "rationale"],
            "additionalProperties": False,
        }},
        "evidence_gaps": {"type": "array", "items": {"type": "string"}},
        "challenges": {"type": "array", "items": {"type": "string"}},
        "next_action": {"type": ["string", "null"]},
    },
    "required": ["status", "summary", "findings", "evidence_gaps", "challenges", "next_action"],
    "additionalProperties": False,
}


class GeminiTaxAgentBackend:
    """LLM backend using the installed google.genai interaction API."""

    def __init__(self, client: Any, *, model: str = "gemini-3.8-flash") -> None:
        self._client = client
        self._model = model

    def run(self, spec: AgentSpec, task: AgentTask) -> AgentReport:
        prompt = (
            f"ROLE: {spec.role.value}\nOBJECTIVE: {spec.objective}\n"
            f"INSTRUCTIONS: {spec.instructions}\n"
            "Return only the requested JSON. Use references exactly as supplied in the packet/reports; "
            "never fabricate a source identifier. A confirmed finding must carry the required evidence, "
            "legal, and form references for this role.\nTASK:\n"
            + json.dumps(_task_payload(task), ensure_ascii=False, default=str)
        )
        interaction = self._client.interactions.create(
            model=self._model,
            input=[{"type": "text", "text": prompt}],
            response_format={"type": "text", "mime_type": "application/json", "schema": _REPORT_SCHEMA},
        )
        return _parse_agent_report(spec.role, interaction.output_text)


def _parse_agent_report(role: TaxAgentRole, raw: str) -> AgentReport:
    payload = json.loads(raw)
    findings = tuple(
        AgentFinding(
            finding_id=str(item["finding_id"]),
            title=str(item["title"]),
            status=FindingStatus(str(item["status"])),
            amount_eur=item["amount_eur"],
            tax_effect_eur=item["tax_effect_eur"],
            evidence_refs=tuple(str(x) for x in item["evidence_refs"]),
            legal_refs=tuple(str(x) for x in item["legal_refs"]),
            form_refs=tuple(str(x) for x in item["form_refs"]),
            rationale=str(item["rationale"]),
        )
        for item in payload["findings"]
    )
    return AgentReport(
        role=role,
        status=AgentRunStatus(str(payload["status"])),
        summary=str(payload["summary"]),
        findings=findings,
        evidence_gaps=tuple(str(x) for x in payload["evidence_gaps"]),
        challenges=tuple(str(x) for x in payload["challenges"]),
        next_action=payload["next_action"],
    )
