import pytest
from agent_lab.case_document_move import MoveIntent, MoveBlocked, validate_intent


def test_valid_scoped_intent():
    intent = MoveIntent('CASE-2025-0001', 2025, 'file1', 'source', 'target', 'intent1')
    assert validate_intent(intent, authorized_id='intent1', case_id='CASE-2025-0001', tax_year=2025, file_id='file1', parent_id='source')


@pytest.mark.parametrize('override', [{'authorized_id': 'other'}, {'case_id': 'OTHER'}, {'tax_year': 2024}, {'file_id': 'other'}, {'parent_id': 'other'}])
def test_wrong_scope_or_authority(override):
    intent = MoveIntent('CASE-2025-0001', 2025, 'file1', 'source', 'target', 'intent1')
    args = dict(authorized_id='intent1', case_id='CASE-2025-0001', tax_year=2025, file_id='file1', parent_id='source')
    args.update(override)
    with pytest.raises((MoveBlocked, PermissionError)):
        validate_intent(intent, **args)


def test_same_folder_denied():
    intent = MoveIntent('CASE-2025-0001', 2025, 'file1', 'source', 'source', 'intent1')
    with pytest.raises(MoveBlocked):
        validate_intent(intent, authorized_id='intent1', case_id='CASE-2025-0001', tax_year=2025, file_id='file1', parent_id='source')
