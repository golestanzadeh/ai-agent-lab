import pytest

from agent_lab.c09_witness_protocol import PROTOCOL, ZERO, WitnessError, WitnessRecord


KEY = b"synthetic-r1-protocol-key"


def _record() -> WitnessRecord:
    return WitnessRecord(
        protocol=PROTOCOL,
        deployment_id="C09-R1-SYNTHETIC",
        epoch=1,
        sequence=1,
        previous_record=ZERO,
        kernel_head=ZERO,
        identity_head=ZERO,
        backup_generation=0,
        operation_id="R1:PROTOCOL:001",
    ).signed(KEY)


def test_r1_p01_strict_canonical_decode_rejects_reformatted_and_duplicate_json():
    record = _record()
    assert WitnessRecord.from_bytes(record.to_bytes(), KEY) == record

    reformatted = record.to_bytes().replace(b'"backup_generation":0', b'"backup_generation": 0')
    with pytest.raises(WitnessError, match="non-canonical"):
        WitnessRecord.from_bytes(reformatted, KEY)

    duplicate = record.to_bytes().replace(
        b'{"backup_generation":0', b'{"backup_generation":0,"backup_generation":0'
    )
    with pytest.raises(WitnessError, match="duplicate"):
        WitnessRecord.from_bytes(duplicate, KEY)
