"""UI-03 bounded analysis execution adapter. Kernel owns dispatch authority.

No provider calls or Drive mutations occur until a concrete authorized Kernel
executor has been injected. A missing authority fails closed, never succeeds.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Any


class AnalysisExecutionBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class AnalysisRequest:
    case_id: str
    tax_year: int
    owner_id: str
    successor_task_id: str | None = None
    scope: str = 'CASE'
    document_id: str | None = None
    execution_intent: str = 'NORMAL'
    request_id: str | None = None
    expected_sha256: str | None = None


class CaseAnalysisExecutor:
    def __init__(self, *, verify_case: Callable[[str, int, str], Any],
                 kernel_dispatch: Callable[[AnalysisRequest], Mapping[str, Any]]):
        if not callable(verify_case) or not callable(kernel_dispatch):
            raise ValueError('Verified case resolver and Kernel dispatcher required')
        self._verify_case = verify_case
        self._kernel_dispatch = kernel_dispatch

    def execute(self, request: AnalysisRequest) -> dict[str, Any]:
        if not isinstance(request, AnalysisRequest) or not request.case_id or not request.owner_id:
            raise AnalysisExecutionBlocked('Invalid case-scoped request')
        if type(request.tax_year) is not int or not 1900 <= request.tax_year <= 9999:
            raise AnalysisExecutionBlocked('Invalid tax year')
        if request.request_id is not None:
            import re
            if (request.scope not in ('CASE','DOCUMENT') or request.execution_intent not in ('NORMAL','EXPLICIT_RERUN')
                    or not re.fullmatch(r'[a-zA-Z0-9-]{16,80}',request.request_id)
                    or (request.scope=='DOCUMENT' and (not isinstance(request.document_id,str) or not 1<=len(request.document_id)<=256))
                    or (request.scope=='CASE' and (request.document_id is not None or request.execution_intent!='NORMAL'))
                    or request.successor_task_id is not None
                    or (request.execution_intent=='EXPLICIT_RERUN' and (request.scope!='DOCUMENT' or not isinstance(request.expected_sha256,str)
                        or not re.fullmatch(r'[0-9a-f]{64}',request.expected_sha256)))):
                raise AnalysisExecutionBlocked('Invalid unified analysis command')
        if request.successor_task_id is not None and (not isinstance(request.successor_task_id,str)
                or not request.successor_task_id.startswith('TASK-') or len(request.successor_task_id)>128):
            raise AnalysisExecutionBlocked('Invalid successor task reference')
        verified = self._verify_case(request.case_id, request.tax_year, request.owner_id)
        if verified is not True:
            raise AnalysisExecutionBlocked('Case authority unavailable')
        result = self._kernel_dispatch(request)
        if not isinstance(result, Mapping):
            raise AnalysisExecutionBlocked('Kernel did not return an execution receipt')
        if result.get('case_id') != request.case_id or result.get('tax_year') != request.tax_year:
            raise AnalysisExecutionBlocked('Kernel receipt scope mismatch')
        if result.get('status') not in ('REGISTERED', 'RUNNING', 'HUMAN_REQUIRED', 'BLOCKED'):
            raise AnalysisExecutionBlocked('Kernel receipt status invalid')
        run_id = result.get('run_id')
        if not isinstance(run_id, str) or not run_id:
            raise AnalysisExecutionBlocked('Kernel run identity missing')
        return {'case_id': request.case_id, 'tax_year': request.tax_year,
                'run_id': run_id, 'status': result['status']}
