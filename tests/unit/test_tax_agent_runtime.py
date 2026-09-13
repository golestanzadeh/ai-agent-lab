from agent_lab.tax_agent_runtime import TaxAgentOrchestrator, TaxAgentRuntimeError
from agent_lab.tax_agents import AgentReport, AgentRunStatus, TaxAgentRole, default_tax_agent_specs


class RecordingBackend:
    def __init__(self, *, stop_role=None, stop_status=AgentRunStatus.PASS):
        self.roles = []
        self.stop_role = stop_role
        self.stop_status = stop_status

    def run(self, spec, task):
        self.roles.append(spec.role)
        status = self.stop_status if spec.role == self.stop_role else AgentRunStatus.PASS
        return AgentReport(role=spec.role, status=status, summary=f"{spec.role.value} complete")


def packet():
    return {"case_id": "CASE-001", "tax_year": 2024, "facts": []}


def test_default_graph_has_six_real_roles_and_explicit_handoffs():
    specs = default_tax_agent_specs()
    assert [s.role for s in specs] == [
        TaxAgentRole.EVIDENCE, TaxAgentRole.LAW, TaxAgentRole.OPPORTUNITY,
        TaxAgentRole.CALCULATION, TaxAgentRole.REVIEWER, TaxAgentRole.FORM,
    ]
    assert [s.handoff_to for s in specs[:-1]] == [s.role for s in specs[1:]]
    assert specs[-1].handoff_to is None


def test_orchestrator_runs_all_roles_in_manager_order():
    backend = RecordingBackend()
    result = TaxAgentOrchestrator(backend).run(
        case_id="CASE-001", tax_year=2024, goal="audit", case_packet=packet()
    )
    assert result.status == AgentRunStatus.PASS
    assert backend.roles == [s.role for s in default_tax_agent_specs()]
    assert result.final_report.role == TaxAgentRole.FORM


def test_human_required_is_terminal_and_stops_handoff():
    backend = RecordingBackend(stop_role=TaxAgentRole.REVIEWER, stop_status=AgentRunStatus.HUMAN_REQUIRED)
    result = TaxAgentOrchestrator(backend).run(
        case_id="CASE-001", tax_year=2024, goal="audit", case_packet=packet()
    )
    assert result.status == AgentRunStatus.HUMAN_REQUIRED
    assert TaxAgentRole.FORM not in backend.roles
    assert result.final_report.role == TaxAgentRole.REVIEWER


def test_case_scope_mismatch_fails_closed():
    backend = RecordingBackend()
    bad = {"case_id": "CASE-002", "tax_year": 2024}
    try:
        TaxAgentOrchestrator(backend).run(
            case_id="CASE-001", tax_year=2024, goal="audit", case_packet=bad
        )
    except TaxAgentRuntimeError as exc:
        assert "another case" in str(exc)
    else:
        raise AssertionError("scope mismatch must fail closed")


def test_tax_year_mismatch_fails_closed():
    backend = RecordingBackend()
    bad = {"case_id": "CASE-001", "tax_year": 2025}
    try:
        TaxAgentOrchestrator(backend).run(
            case_id="CASE-001", tax_year=2024, goal="audit", case_packet=bad
        )
    except TaxAgentRuntimeError as exc:
        assert "another tax year" in str(exc)
    else:
        raise AssertionError("tax-year mismatch must fail closed")


def test_evidence_gap_human_required_is_normalized_and_handoff_continues():
    backend = RecordingBackend(stop_role=TaxAgentRole.EVIDENCE, stop_status=AgentRunStatus.HUMAN_REQUIRED)
    result = TaxAgentOrchestrator(backend).run(
        case_id="CASE-001", tax_year=2024, goal="audit", case_packet=packet()
    )
    assert result.status == AgentRunStatus.PASS
    assert backend.roles == [s.role for s in default_tax_agent_specs()]
    assert result.reports[0].status == AgentRunStatus.PASS
    assert result.reports[0].metadata["escalation_normalized"] == "human_required_evidence_gap_nonterminal"

