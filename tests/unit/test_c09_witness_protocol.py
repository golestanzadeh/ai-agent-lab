import pytest

from agent_lab.c09_witness_protocol import (
    PROTOCOL,
    ZERO,
    WitnessError,
    WitnessRecord,
    verify_chain,
)


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


def test_r1_p02_schema_types_and_mac_substitution_fail_closed():
    record = _record()
    unsigned = record.unsigned()

    missing = {**unsigned, "mac": record.mac}
    del missing["backup_generation"]
    with pytest.raises(WitnessError, match="schema"):
        WitnessRecord.from_bytes(
            __import__("json").dumps(missing, sort_keys=True, separators=(",", ":")).encode(),
            KEY,
        )

    boolean_epoch = WitnessRecord(**{**unsigned, "epoch": True}, mac=record.mac)
    with pytest.raises(WitnessError, match="contract"):
        WitnessRecord.from_bytes(boolean_epoch.to_bytes(), KEY)

    substituted = WitnessRecord(**unsigned, mac="hmac-sha256:" + "0" * 64)
    with pytest.raises(WitnessError, match="authentication"):
        WitnessRecord.from_bytes(substituted.to_bytes(), KEY)


def test_r1_p03_ordered_chain_accepts_contiguous_and_rejects_gap_reorder_and_fork():
    first = _record()
    second = WitnessRecord(
        **{
            **first.unsigned(),
            "sequence": 2,
            "previous_record": first.commitment,
            "operation_id": "R1:PROTOCOL:002",
        }
    ).signed(KEY)
    assert verify_chain([first, second], KEY, deployment_id=first.deployment_id) == (
        first,
        second,
    )

    gap = WitnessRecord(
        **{**second.unsigned(), "sequence": 3, "operation_id": "R1:PROTOCOL:003"}
    ).signed(KEY)
    with pytest.raises(WitnessError, match="gap"):
        verify_chain([first, gap], KEY, deployment_id=first.deployment_id)
    with pytest.raises(WitnessError, match="gap"):
        verify_chain([second, first], KEY, deployment_id=first.deployment_id)

    fork = WitnessRecord(
        **{**second.unsigned(), "previous_record": ZERO, "operation_id": "R1:PROTOCOL:FORK"}
    ).signed(KEY)
    with pytest.raises(WitnessError, match="fork"):
        verify_chain([first, fork], KEY, deployment_id=first.deployment_id)
