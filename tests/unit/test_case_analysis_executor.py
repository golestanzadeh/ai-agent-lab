import pytest

from agent_lab.case_analysis_executor import (AnalysisRequest, CaseAnalysisExecutor,
                                              AnalysisExecutionBlocked)

REQ = AnalysisRequest('CASE-2025-0001', 2025, 'owner')


def test_accepts_verified_case_and_matching_kernel_receipt():
    called = []
    executor = CaseAnalysisExecutor(
        verify_case=lambda c, y, o: (c, y, o) == ('CASE-2025-0001', 2025, 'owner'),
        kernel_dispatch=lambda req: (called.append(req) or {
            'case_id': req.case_id, 'tax_year': req.tax_year,
            'run_id': 'RUN-1', 'status': 'REGISTERED'}))
    assert executor.execute(REQ)['run_id'] == 'RUN-1'
    assert called == [REQ]


def test_rejects_unauthorized_case_without_dispatch():
    called = []
    executor = CaseAnalysisExecutor(verify_case=lambda *args: False,
                                    kernel_dispatch=lambda req: called.append(req))
    with pytest.raises(AnalysisExecutionBlocked):
        executor.execute(REQ)
    assert not called


@pytest.mark.parametrize('receipt', [None, {}, {'case_id': 'OTHER', 'tax_year': 2025,
    'run_id': 'RUN-1', 'status': 'REGISTERED'}, {'case_id': REQ.case_id,
    'tax_year': REQ.tax_year, 'run_id': 'RUN-1', 'status': 'COMPLETE'}])
def test_rejects_unverified_kernel_receipt(receipt):
    executor = CaseAnalysisExecutor(verify_case=lambda *args: True,
                                    kernel_dispatch=lambda req: receipt)
    with pytest.raises(AnalysisExecutionBlocked):
        executor.execute(REQ)
