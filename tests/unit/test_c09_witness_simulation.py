"""AT-C09-01..15: isolated local proof, never operational acceptance."""

from dataclasses import replace

import pytest

from agent_lab.c09_witness_simulation import WitnessError, WitnessProtocolHarness, WitnessRecord, PROTOCOL, ZERO


def committed() -> WitnessProtocolHarness:
    harness = WitnessProtocolHarness()
    assert harness.execute("OP-1") == "FINALIZED"
    return harness


def test_at_c09_01_both_local_stores_rolled_back_together():
    harness = committed(); old = harness.state.clone(); harness.execute("OP-2"); harness.state = old
    with pytest.raises(WitnessError, match="stale"): harness.recover()


def test_at_c09_02_kernel_only_rollback():
    harness = committed(); harness.state.kernel_head = ZERO
    with pytest.raises(WitnessError, match="stale"): harness.recover()


def test_at_c09_03_identity_only_rollback():
    harness = committed(); harness.state.identity_head = ZERO
    with pytest.raises(WitnessError, match="stale"): harness.recover()


def test_at_c09_04_crash_before_identity_commit_aborts_deterministically():
    harness = WitnessProtocolHarness(); assert harness.execute("OP-1", crash_at="before_identity") == "PENDING"
    assert harness.recover() == "ABORTED_BEFORE_IDENTITY"


def test_at_c09_05_crash_after_identity_before_witness_fails_closed():
    harness = WitnessProtocolHarness(); harness.execute("OP-1", crash_at="after_identity")
    assert harness.recover() == "FAIL_CLOSED_IDENTITY_AHEAD"


def test_at_c09_06_crash_after_witness_finalizes_from_witness():
    harness = WitnessProtocolHarness(); harness.execute("OP-1", crash_at="after_witness")
    assert harness.recover() == "FINALIZED_FROM_WITNESS"


def test_at_c09_07_duplicate_operation_or_replay_rejected():
    harness = committed()
    with pytest.raises(WitnessError, match="duplicate"): harness.execute("OP-1")


def test_at_c09_08_concurrent_conflicting_successors_only_one_wins():
    harness = WitnessProtocolHarness(); harness.state.pending = {"operation_id":"A","kernel_head":ZERO,"identity_head":ZERO}
    first = harness._next_record("A"); harness.store.conditional_create(first)
    second = replace(first, operation_id="B", mac="").signed(harness.key)
    with pytest.raises(WitnessError, match="conflict"): harness.store.conditional_create(second)


def test_at_c09_09_witness_unavailable_blocks_operation():
    harness = WitnessProtocolHarness(); harness.store.available = False
    with pytest.raises(WitnessError, match="unavailable"): harness.execute("OP-1")


def test_at_c09_10_missing_sequence_and_forged_high_sequence_rejected():
    harness = committed(); prior = harness.verify_witness_chain()[-1]
    forged = WitnessRecord(PROTOCOL,harness.deployment_id,1,3,prior.commitment,ZERO,ZERO,0,"OP-3").signed(harness.key)
    harness.store.inject_version(forged.object_key, forged)
    with pytest.raises(WitnessError, match="gap"): harness.verify_witness_chain()


def test_at_c09_11_unauthorized_epoch_fork_or_reset_rejected():
    harness = committed(); prior = harness.verify_witness_chain()[-1]
    fork = WitnessRecord(PROTOCOL,harness.deployment_id,2,1,prior.commitment,ZERO,ZERO,0,"FORK").signed(harness.key)
    harness.store.inject_version(fork.object_key, fork)
    with pytest.raises(WitnessError, match="epoch fork"): harness.verify_witness_chain()


def test_at_c09_12_authorized_restore_accepts_exact_owner_authorization_once():
    harness = committed(); source = harness.verify_witness_chain()[-1].commitment
    authorization = harness.sign_restore("RESTORE-1",source_commitment=source,target_epoch=2)
    harness.authorized_restore(authorization)
    assert (harness.state.epoch, harness.state.sequence, harness.state.backup_generation) == (2, 1, 1)
    assert harness.verify_witness_chain()[-1].record_type == "RESTORE"


def test_at_c09_13_reused_expired_or_mismatched_restore_authorization_rejected():
    harness = committed(); source = harness.verify_witness_chain()[-1].commitment
    authorization = harness.sign_restore("RESTORE-1",source_commitment=source,target_epoch=2)
    harness.authorized_restore(authorization)
    with pytest.raises(WitnessError, match="reused"): harness.authorized_restore(authorization)
    expired = harness.sign_restore("RESTORE-2",source_commitment=source,target_epoch=2,expires="EXPIRED")
    with pytest.raises(WitnessError, match="expired"): harness.authorized_restore(expired)
    mismatch = harness.sign_restore("RESTORE-3",source_commitment=ZERO,target_epoch=2)
    with pytest.raises(WitnessError, match="source"): harness.authorized_restore(mismatch)


def test_at_c09_14_cloud_credential_compromise_cannot_forge_authenticated_record():
    harness = committed(); prior = harness.verify_witness_chain()[-1]
    forged = WitnessRecord(PROTOCOL,harness.deployment_id,1,2,prior.commitment,ZERO,ZERO,0,"ATTACK",mac="hmac-sha256:"+"0"*64)
    harness.store.inject_version(forged.object_key,forged)
    with pytest.raises(WitnessError, match="authentication"): harness.verify_witness_chain()


def test_at_c09_15_object_version_and_delete_marker_ambiguity_rejected():
    harness = committed(); record = harness.verify_witness_chain()[-1]
    harness.store.inject_delete_marker(record.object_key)
    replacement = replace(record,operation_id="REPLACEMENT",mac="").signed(harness.key)
    harness.store.conditional_create(replacement)
    with pytest.raises(WitnessError, match="version or delete-marker"): harness.verify_witness_chain()
