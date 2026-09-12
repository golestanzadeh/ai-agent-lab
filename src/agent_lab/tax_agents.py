"""Role contracts for the evidence-first German tax multi-agent runtime."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class TaxAgentRole(str, Enum):
    EVIDENCE = "EVIDENCE_AGENT"
    LAW = "TAX_LAW_AGENT"
    OPPORTUNITY = "OPPORTUNITY_AGENT"
    CALCULATION = "CALCULATION_AGENT"
    REVIEWER = "ADVERSARIAL_REVIEWER_AGENT"
    FORM = "ELSTER_FORM_AGENT"


class FindingStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANDIDATE = "CANDIDATE"
    EVIDENCE_GAP = "EVIDENCE_GAP"
    REJECTED = "REJECTED"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"


class AgentRunStatus(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"


@dataclass(frozen=True, slots=True)
class AgentSpec:
    role: TaxAgentRole
    objective: str
    required_inputs: tuple[str, ...]
    required_outputs: tuple[str, ...]
    permissions: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    handoff_to: TaxAgentRole | None
    instructions: str


@dataclass(frozen=True, slots=True)
class AgentTask:
    case_id: str
    tax_year: int
    goal: str
    case_packet: Mapping[str, object]
    prior_reports: tuple["AgentReport", ...] = ()


@dataclass(frozen=True, slots=True)
class AgentFinding:
    finding_id: str
    title: str
    status: FindingStatus
    amount_eur: float | None = None
    tax_effect_eur: float | None = None
    evidence_refs: tuple[str, ...] = ()
    legal_refs: tuple[str, ...] = ()
    form_refs: tuple[str, ...] = ()
    rationale: str = ""


@dataclass(frozen=True, slots=True)
class AgentReport:
    role: TaxAgentRole
    status: AgentRunStatus
    summary: str
    findings: tuple[AgentFinding, ...] = ()
    evidence_gaps: tuple[str, ...] = ()
    challenges: tuple[str, ...] = ()
    next_action: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


_COMMON = (
    "Operate only on the supplied case_id and tax year. Never invent evidence, amounts, "
    "dates, legal authority, or form placement. NO SOURCE -> NO TAX CLAIM and NO SOURCE "
    "-> NO OPPORTUNITY. Distinguish confirmed facts from candidates and evidence gaps. "
    "Use tax-year/effective-date aware law. Do not submit, sign, merge, release, mutate "
    "source evidence, or contact ELSTER/Finanzamt."
)


def default_tax_agent_specs() -> tuple[AgentSpec, ...]:
    """Return the approved manager-order role graph for one case-scoped run."""
    return (
        AgentSpec(
            TaxAgentRole.EVIDENCE,
            "Inventory and reconcile evidence; expose unused or conflicting facts.",
            ("case_packet",), ("findings", "evidence_gaps"),
            ("READ_CASE_PACKET", "LINK_EVIDENCE"),
            ("case_scope_ambiguous", "evidence_identity_conflict"),
            TaxAgentRole.LAW,
            _COMMON + " Focus on provenance, completeness, payment/service year and party attribution.",
        ),
        AgentSpec(
            TaxAgentRole.LAW,
            "Map supported facts to authoritative German tax law applicable to the tax year.",
            ("evidence_report",), ("legal_findings", "legal_conflicts"),
            ("READ_EVIDENCE", "READ_AUTHORITATIVE_LAW"),
            ("material_law_conflict", "effective_date_uncertain"),
            TaxAgentRole.OPPORTUNITY,
            _COMMON + " Prefer EStG/AO/BMF/official handbooks and identify exact effective dates.",
        ),
        AgentSpec(
            TaxAgentRole.OPPORTUNITY,
            "Search law-to-case and case-to-law for lawful missed tax benefits.",
            ("evidence_report", "law_report"), ("opportunities", "evidence_gaps"),
            ("READ_EVIDENCE", "READ_LAW", "PROPOSE_OPPORTUNITY"),
            ("material_conflict_requires_human",),
            TaxAgentRole.CALCULATION,
            _COMMON + " Never promote a missing-evidence candidate into a claim-ready amount.",
        ),
        AgentSpec(
            TaxAgentRole.CALCULATION,
            "Recalculate independently and quantify tax-base and direct-credit effects.",
            ("evidence_report", "law_report", "opportunity_report"),
            ("calculation_findings", "scenario_results"),
            ("READ_VALIDATED_FACTS", "CALCULATE"),
            ("material_input_missing", "calculation_conflict"),
            TaxAgentRole.REVIEWER,
            _COMMON + " Recompute rather than trust prior totals; check thresholds, offsets and double counting.",
        ),
        AgentSpec(
            TaxAgentRole.REVIEWER,
            "Attack every material conclusion and detect overclaims, omissions and stale-law errors.",
            ("all_prior_reports",), ("accepted_findings", "rejections", "challenges"),
            ("READ_ALL_REPORTS", "CHALLENGE", "REJECT_FINDING"),
            ("consequential_ambiguity", "irreconcilable_conflict"),
            TaxAgentRole.FORM,
            _COMMON + " Treat tax-year version mismatch, duplicate deduction and reimbursement errors as critical.",
        ),
        AgentSpec(
            TaxAgentRole.FORM,
            "Map only reviewer-surviving findings to official forms/ELSTER fields.",
            ("reviewer_report",), ("form_mappings", "unmapped_items"),
            ("READ_ACCEPTED_FINDINGS", "MAP_OFFICIAL_FORM"),
            ("official_form_source_missing", "material_mapping_ambiguous"),
            None,
            _COMMON + " Never invent an Anlage or Zeile and never perform submission.",
        ),
    )
