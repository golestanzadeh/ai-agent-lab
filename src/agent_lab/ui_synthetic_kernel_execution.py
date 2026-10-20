"""One-shot synthetic UI worker governed by the existing Orchestrator Kernel."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_lab.orchestrator_kernel import (
    ContractError, IntegrityError, OrchestratorKernel, PermissionDenied,
)
from agent_lab.ui_synthetic_document_parser import (
    CONTENT_TYPE, PARSER_SCHEMA, SyntheticExtraction,
    parse_synthetic_wage_statement,
)


AUTHORITY_REFERENCE = "human-authorization://UI25-05/synthetic-kernel-execution"
DOCUMENT_AUTHORITY_REFERENCE = "human-authorization://UI25/synthetic-document-evidence"
EXTRACTION_AUTHORITY_REFERENCE = "human-authorization://UI25-07/synthetic-content-extraction"
WORKER_ID = "UI25-SYNTHETIC-WORKER-V1"
_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class SyntheticExecutionConflict(ContractError):
    """Stable, privacy-safe UI classification for an existing synthetic run."""


class SyntheticRunReplay(SyntheticExecutionConflict):
    def __init__(self, run_id: str):
        super().__init__("synthetic run already has a durable response")
        self.run_id = run_id


class SyntheticIncompleteRun(SyntheticExecutionConflict):
    def __init__(self, run_id: str):
        super().__init__("synthetic run has an incomplete recovery attempt")
        self.run_id = run_id


class SyntheticDocumentRunConflict(PermissionDenied):
    def __init__(self, run_id: str):
        super().__init__("document is already bound to another run in the exact case scope")
        self.run_id = run_id


class SyntheticRunScopeConflict(PermissionDenied):
    """A run identity is already bound outside the requested exact scope."""


class SyntheticPermissionMatrixRejected(PermissionDenied):
    """The Kernel Permission Matrix rejected the bounded worker."""


class SyntheticKillSwitchRejected(PermissionDenied):
    """The Kernel Kill Switch rejected execution."""


class SyntheticBudgetRejected(PermissionDenied):
    """The Kernel budget rejected execution."""


class SyntheticCaseKernelExecutor:
    """Explicit one-task adapter; it is neither a scheduler nor an authority store."""

    def __init__(self, database_path: str | Path, contract_root: str | Path):
        self.database_path = Path(database_path).resolve()
        self.contract_root = Path(contract_root).resolve()

    @staticmethod
    def _validate_scope(case_id: str, tax_year: int, run_id: str, synthetic_value: int) -> None:
        if not isinstance(case_id, str) or not case_id.startswith("TEST-") or not _IDENTIFIER.fullmatch(case_id):
            raise PermissionDenied("synthetic execution requires an exact TEST case")
        if tax_year != 2025:
            raise PermissionDenied("synthetic UI25 execution is restricted to tax year 2025")
        if not isinstance(run_id, str) or not _IDENTIFIER.fullmatch(run_id):
            raise ContractError("run_id must be a bounded ASCII identifier")
        if isinstance(synthetic_value, bool) or not isinstance(synthetic_value, int) or not 0 <= synthetic_value <= 1_000_000:
            raise ContractError("synthetic value is outside the bounded range")

    @staticmethod
    def _validate_document_scope(
        case_id: str, tax_year: int, run_id: str,
        document_reference: str, document_digest: str,
    ) -> None:
        SyntheticCaseKernelExecutor._validate_scope(case_id, tax_year, run_id, 0)
        if not isinstance(document_digest, str) or not _SHA256.fullmatch(document_digest):
            raise ContractError("document digest must be an exact lowercase SHA-256")
        expected = f"test-document://{case_id}/sha256:{document_digest}"
        if document_reference != expected:
            raise PermissionDenied("document reference is not bound to the exact case and digest")

    @staticmethod
    def _identities(case_id: str, tax_year: int, run_id: str) -> tuple[str, str, str]:
        scope = f"{case_id}:{tax_year}:{run_id}".encode("ascii")
        suffix = hashlib.sha256(scope).hexdigest()[:20].upper()
        return f"TASK-UI25-{suffix}", f"MAN-UI25-{suffix}", f"RESP-UI25-{suffix}"

    @staticmethod
    def _recovery_identities(case_id: str, tax_year: int, run_id: str) -> tuple[str, str, str]:
        scope = f"{case_id}:{tax_year}:{run_id}:RECOVERY:1".encode("ascii")
        suffix = hashlib.sha256(scope).hexdigest()[:20].upper()
        return f"TASK-UI25-R-{suffix}", f"MAN-UI25-R-{suffix}", f"RESP-UI25-R-{suffix}"

    @staticmethod
    def _actor_instance_id(task_id: str) -> str:
        suffix = hashlib.sha256(task_id.encode("ascii")).hexdigest()[:16].upper()
        return f"{WORKER_ID}-{suffix}"

    @staticmethod
    def _run_worker(
        kernel: OrchestratorKernel, *, manifest_id: str, case_id: str,
        tax_year: int, run_id: str, synthetic_value: int | None = None,
        document_reference: str | None = None, document_digest: str | None = None,
        document_content: bytes | None = None, content_type: str | None = None,
        expected_extraction_digest: str | None = None,
    ) -> tuple[Any, str, str]:
        decision = kernel.permission_decision(
            manifest_id, "report_evidence", case_id=case_id,
            tax_year=tax_year, run_id=run_id,
        )
        if not decision.allowed:
            raise SyntheticPermissionMatrixRejected("Kernel denied the fixed synthetic worker")
        if not kernel.consume_budget(
            manifest_id, tokens=0, tool_calls=1, cost_usd=0.0
        ).allowed:
            raise SyntheticBudgetRejected("Kernel denied the fixed worker budget")
        if synthetic_value is not None and document_reference is None and document_digest is None:
            result = synthetic_value * 2
            envelope = {
                "operation": "DOUBLE_SYNTHETIC_INTEGER", "worker_id": WORKER_ID,
                "case_id": case_id, "tax_year": tax_year, "run_id": run_id,
                "synthetic_value": synthetic_value, "deterministic_result": result,
            }
            summary = f"SYNTHETIC_RESULT={result}; WORKER={WORKER_ID}"
        elif (
            synthetic_value is None and document_reference is not None
            and document_digest is not None and document_content is None
            and content_type is None and expected_extraction_digest is None
        ):
            SyntheticCaseKernelExecutor._validate_document_scope(
                case_id, tax_year, run_id, document_reference, document_digest
            )
            result = "VALID"
            envelope = {
                "operation": "VALIDATE_SYNTHETIC_DOCUMENT_EVIDENCE",
                "worker_id": WORKER_ID, "case_id": case_id,
                "tax_year": tax_year, "run_id": run_id,
                "document_reference": document_reference,
                "document_digest": f"sha256:{document_digest}",
                "content_interpretation": "NOT_PERFORMED", "result": result,
            }
            summary = (
                f"SYNTHETIC_DOCUMENT_EVIDENCE={result}; "
                f"DOCUMENT_REFERENCE={document_reference}; "
                f"DOCUMENT_DIGEST=sha256:{document_digest}; "
                f"CONTENT_INTERPRETATION=NOT_PERFORMED; WORKER={WORKER_ID}"
            )
        elif (
            synthetic_value is None and document_reference is not None
            and document_digest is not None and document_content is not None
            and content_type is not None and expected_extraction_digest is not None
        ):
            SyntheticCaseKernelExecutor._validate_document_scope(
                case_id, tax_year, run_id, document_reference, document_digest
            )
            if hashlib.sha256(document_content).hexdigest() != document_digest:
                raise ContractError("document bytes do not match the bound digest")
            extraction = parse_synthetic_wage_statement(document_content, content_type)
            if extraction.digest != expected_extraction_digest:
                raise ContractError("structured extraction does not match the task input")
            result = extraction.as_dict()
            envelope = {
                "operation": "EXTRACT_SYNTHETIC_DOCUMENT_CONTENT",
                "worker_id": WORKER_ID, "case_id": case_id,
                "tax_year": tax_year, "run_id": run_id,
                "document_reference": document_reference,
                "document_digest": f"sha256:{document_digest}",
                "parser_schema": PARSER_SCHEMA,
                "structured_extraction": result,
                "structured_extraction_digest": extraction.digest,
                "tax_interpretation": "NOT_PERFORMED",
            }
            summary = (
                "SYNTHETIC_CONTENT_EXTRACTION=VALID; NOT_TAX_ANALYSIS; "
                f"DOCUMENT_REFERENCE={document_reference}; "
                f"DOCUMENT_DIGEST=sha256:{document_digest}; "
                f"PARSER_SCHEMA={PARSER_SCHEMA}; EXTRACTION_DIGEST={extraction.digest}; "
                f"DOCUMENT_TYPE={extraction.document_type}; TAX_YEAR={extraction.tax_year}; "
                f"EMPLOYER_ID={extraction.employer_id}; "
                f"GROSS_EMPLOYMENT_INCOME={extraction.gross_employment_income}; "
                f"WITHHELD_WAGE_TAX={extraction.withheld_wage_tax}; "
                f"CURRENCY={extraction.currency}; WORKER={WORKER_ID}"
            )
        else:
            raise ContractError("exactly one bounded synthetic operation is required")
        evidence = "sha256:" + hashlib.sha256(
            _canonical(envelope).encode("utf-8")
        ).hexdigest()
        return result, evidence, summary

    def execute(
        self, *, case_id: str, tax_year: int, run_id: str,
        synthetic_value: int | None = None, document_reference: str | None = None,
        document_digest: str | None = None,
        document_content: bytes | None = None, content_type: str | None = None,
    ) -> dict[str, Any]:
        if synthetic_value is not None and document_reference is None and document_digest is None:
            self._validate_scope(case_id, tax_year, run_id, synthetic_value)
            operation_inputs = [f"synthetic://ui25/value/{synthetic_value}"]
            objective = "Execute one bounded deterministic UI25 synthetic calculation"
            acceptance = "deterministic synthetic result is durably recorded"
            authority_reference = AUTHORITY_REFERENCE
            response_test_name = "deterministic-synthetic-double"
            expected_extraction: SyntheticExtraction | None = None
        elif (
            synthetic_value is None and document_reference is not None
            and document_digest is not None and document_content is None
            and content_type is None
        ):
            self._validate_document_scope(
                case_id, tax_year, run_id, document_reference, document_digest
            )
            operation_inputs = [document_reference, f"sha256:{document_digest}"]
            objective = "Validate one case-owned synthetic document digest without interpreting content"
            acceptance = "case-owned synthetic document evidence is durably validated"
            authority_reference = DOCUMENT_AUTHORITY_REFERENCE
            response_test_name = "deterministic-synthetic-document-evidence-validation"
            expected_extraction = None
        elif (
            synthetic_value is None and document_reference is not None
            and document_digest is not None and document_content is not None
            and content_type is not None
        ):
            self._validate_document_scope(
                case_id, tax_year, run_id, document_reference, document_digest
            )
            if hashlib.sha256(document_content).hexdigest() != document_digest:
                raise ContractError("document bytes do not match the bound digest")
            expected_extraction = parse_synthetic_wage_statement(document_content, content_type)
            operation_inputs = [
                document_reference, f"sha256:{document_digest}",
                f"parser://{PARSER_SCHEMA}",
                f"extraction://{expected_extraction.digest}",
            ]
            objective = "Extract one bounded synthetic document without tax interpretation"
            acceptance = "case-owned content produces a lineage-bound structured extraction"
            authority_reference = EXTRACTION_AUTHORITY_REFERENCE
            response_test_name = "deterministic-synthetic-content-extraction"
        else:
            raise ContractError("exactly one bounded synthetic operation is required")
        base_task_id, base_manifest_id, base_response_id = self._identities(
            case_id, tax_year, run_id
        )
        context = {"case_id": case_id, "tax_year": tax_year, "run_id": run_id}
        with OrchestratorKernel(self.database_path, self.contract_root) as kernel:
            kernel.verify_audit_chain()
            if kernel.kill_switch_state() != "HALTED":
                raise SyntheticKillSwitchRejected(
                    "one-shot synthetic execution requires the HALTED boundary"
                )
            parent_task_id = None
            task_id, manifest_id, response_id = (
                base_task_id, base_manifest_id, base_response_id
            )
            base_row = kernel._connection.execute(
                "SELECT status,payload_json FROM tasks WHERE task_id=?", (base_task_id,)
            ).fetchone()
            if base_row is not None:
                existing = json.loads(base_row["payload_json"])
                if (
                    existing.get("case_context") != context
                    or existing.get("inputs") != operation_inputs
                    or existing.get("objective") != objective
                ):
                    raise PermissionDenied("existing task identity is not bound to this exact operation")
                manifests = kernel._connection.execute(
                    "SELECT COUNT(*) FROM manifests WHERE task_id=?", (base_task_id,)
                ).fetchone()[0]
                responses = kernel._connection.execute(
                    "SELECT COUNT(*) FROM responses WHERE task_id=?", (base_task_id,)
                ).fetchone()[0]
                if responses:
                    raise SyntheticRunReplay(run_id)
                if manifests > 1:
                    raise IntegrityError("incomplete synthetic run has ambiguous manifests")
                parent_task_id = base_task_id
                task_id, manifest_id, response_id = self._recovery_identities(
                    case_id, tax_year, run_id
                )
                if kernel._connection.execute(
                    "SELECT 1 FROM tasks WHERE task_id=?", (task_id,)
                ).fetchone() is not None:
                    recovery_responses = kernel._connection.execute(
                        "SELECT COUNT(*) FROM responses WHERE task_id=?", (task_id,)
                    ).fetchone()[0]
                    if recovery_responses:
                        raise SyntheticRunReplay(run_id)
                    raise SyntheticIncompleteRun(run_id)
            for row in kernel._connection.execute(
                "SELECT task_id, payload_json FROM tasks ORDER BY task_id"
            ).fetchall():
                existing = json.loads(row["payload_json"])
                existing_context = existing.get("case_context")
                if row["task_id"] in {base_task_id, task_id}:
                    continue
                if (
                    isinstance(existing_context, dict)
                    and existing_context.get("run_id") == run_id
                    and existing_context != context
                ):
                    raise SyntheticRunScopeConflict(
                        "run identity is already bound to another case or year"
                    )
                if (
                    document_reference is not None
                    and document_reference in existing.get("inputs", ())
                    and existing_context != context
                ):
                    if (
                        isinstance(existing_context, dict)
                        and existing_context.get("case_id") == case_id
                        and existing_context.get("tax_year") == tax_year
                        and isinstance(existing_context.get("run_id"), str)
                    ):
                        raise SyntheticDocumentRunConflict(existing_context["run_id"])
                    raise SyntheticRunScopeConflict(
                        "document reference is already bound outside the exact case scope"
                    )
            now = datetime.now(timezone.utc)
            actor_instance_id = self._actor_instance_id(task_id)
            task = {
                "schema_version": 1, "task_id": task_id, "parent_task_id": parent_task_id,
                "objective": objective,
                "role_id": "IMPLEMENTATION_AGENT", "actor_instance_id": actor_instance_id,
                "repository": "golestanzadeh/ai-agent-lab", "ref": "oi0002-identity-persistence",
                "case_context": context,
                "inputs": operation_inputs,
                "expected_outputs": [f"kernel://ui25/result/{task_id}"],
                "allowed_tools": ["synthetic_ui25_deterministic_worker"],
                "permissions": ["report_evidence"],
                "forbidden_actions": [
                    "external_transfer", "use_real_data", "protected_persistence",
                    "agent_spawn", "subprocess", "network_io",
                ],
                "budget": {"token_limit": 1, "tool_call_limit": 1, "cost_limit_usd": 0.01},
                "timeout_seconds": 30, "max_retries": 0,
                "acceptance_criteria": [acceptance],
                "stop_conditions": ["scope mismatch", "kill switch not RUNNING", "duplicate task"],
                "escalation_route": ["MASTER_PROJECT_ORCHESTRATOR", "HUMAN_PROJECT_OWNER"],
                "created_at": now.isoformat(), "expires_at": (now + timedelta(minutes=10)).isoformat(),
                "status": "REGISTERED",
            }
            manifest = {
                "schema_version": 1, "manifest_id": manifest_id,
                "role_id": task["role_id"], "actor_instance_id": actor_instance_id,
                "task_id": task_id, "parent_task_id": parent_task_id,
                "scope": {
                    "repository": task["repository"], "ref": task["ref"],
                    "allowed_paths": [], "case_context": context,
                },
                "inputs": task["inputs"], "expected_outputs": task["expected_outputs"],
                "allowed_tools": task["allowed_tools"], "requested_access_tiers": ["A1"],
                "requested_capabilities": task["permissions"],
                "forbidden_actions": task["forbidden_actions"], "budget": task["budget"],
                "timeout_seconds": task["timeout_seconds"], "max_retries": 0,
                "stop_conditions": task["stop_conditions"],
                "escalation_route": task["escalation_route"],
                "issued_at": task["created_at"], "expires_at": task["expires_at"],
                "status": "PROPOSED",
            }
            # The explicit UI POST is the bounded Owner action represented here.
            with kernel.atomic_execution():
                kernel.set_kill_switch(
                    "RUNNING", actor_id="HUMAN_PROJECT_OWNER",
                    authority_reference=authority_reference,
                )
                kernel.register_task(task, gate_triggers=())
                kernel.register_manifest(manifest)
                kernel.validate_manifest(manifest_id)
                kernel.activate_manifest(manifest_id)
                result, evidence, result_summary = self._run_worker(
                    kernel, manifest_id=manifest_id, case_id=case_id,
                    tax_year=tax_year, run_id=run_id, synthetic_value=synthetic_value,
                    document_reference=document_reference,
                    document_digest=document_digest,
                    document_content=document_content, content_type=content_type,
                    expected_extraction_digest=(
                        expected_extraction.digest if expected_extraction is not None else None
                    ),
                )
                response = {
                    "schema_version": 1, "response_id": response_id,
                    "task_id": task_id, "parent_task_id": parent_task_id,
                    "role_id": task["role_id"], "actor_instance_id": actor_instance_id,
                    "status": "PASS",
                    "result_summary": result_summary,
                    "artifact_references": task["expected_outputs"],
                    "changed_paths_or_state": [f"kernel://response/{response_id}"],
                    "tests": [{
                        "name": response_test_name, "outcome": "PASS",
                        "evidence_reference": evidence,
                    }],
                    "evidence": [evidence], "authority_used": [authority_reference],
                    "costs": {"tokens_used": 0, "tool_calls_used": 1, "cost_usd": 0.0},
                    "unresolved_risks": [],
                    "recommended_next_action": "independent acceptance remains separate",
                    "human_required": False, "created_at": datetime.now(timezone.utc).isoformat(),
                }
                kernel.record_response(manifest_id, response)
                kernel.set_kill_switch(
                    "HALTED", actor_id="MASTER_PROJECT_ORCHESTRATOR",
                    authority_reference="ui25://synthetic-one-shot-complete",
                )
                kernel.verify_audit_chain()
        return {
            "task_id": task_id, "run_id": run_id, "result": result,
            "evidence": evidence, "status": "AWAITING_ACCEPTANCE",
            "recovered_from_task_id": parent_task_id,
        }
