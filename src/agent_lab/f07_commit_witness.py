"""Canonical mutation COMMIT reservation and Witness commitments."""

import re

from agent_lab.c09_witness_protocol import PROTOCOL, WitnessRecord, canonical_bytes, digest as witness_digest
from agent_lab.identity_logical_continuity import H, witness_commitment, witness_slot
from agent_lab.ipc_operational_read import NUM, UUID, digest, exact

PROFILE = "identity-mutation-witness-slot/1"
SLOT_FIELDS = set("profile previous_epoch previous_sequence previous_record epoch sequence backup_generation operation_id object_key".split())


def _number(value):
    if not isinstance(value, str) or not NUM.fullmatch(value):
        raise ValueError("noncanonical Witness slot number")
    return int(value)


def slot_projection(request, *, previous_epoch, previous_sequence, previous_record, backup_generation):
    """Derive a slot from Kernel's verified durable Witness predecessor."""
    if (request["contract"] != "oi0002.kernel-identity-c09/1.1"
            or request["message_type"] != "COMMIT_MUTATION"
            or not UUID.fullmatch(request["transaction_id"])
            or not re.fullmatch(r"[A-Z][A-Z0-9-]{2,63}", request["deployment_id"])):
        raise ValueError("invalid mutation reservation scope")
    digest(request["prepared_request_digest"])
    digest(previous_record)
    old_epoch, old_sequence = _number(previous_epoch), _number(previous_sequence)
    if (old_epoch == 0 or old_sequence == 0) and (old_epoch, old_sequence) != (0, 0):
        raise ValueError("invalid Witness predecessor")
    if (previous_record == "sha256:" + "0" * 64) != ((old_epoch, old_sequence) == (0, 0)):
        raise ValueError("Witness predecessor commitment mismatch")
    _number(backup_generation)
    epoch, sequence = witness_slot(old_epoch, old_sequence, previous_record)
    _number(str(epoch))
    _number(str(sequence))
    slot = dict(profile=PROFILE, previous_epoch=previous_epoch, previous_sequence=previous_sequence,
                previous_record=previous_record, epoch=str(epoch), sequence=str(sequence),
                backup_generation=backup_generation)
    operation = H({**slot, **{key: request[key] for key in (
        "deployment_id", "transaction_id", "prepared_request_digest")}})
    slot["operation_id"] = "MUTATION:" + operation[7:].upper()
    slot["object_key"] = (f"witness/v1/{request['deployment_id']}/epoch-{epoch:020d}/"
                          f"sequence-{sequence:020d}.json")
    return slot


def validate_slot(request, slot):
    exact(slot, SLOT_FIELDS)
    expected = slot_projection(request, **{name: slot[name] for name in (
        "previous_epoch", "previous_sequence", "previous_record", "backup_generation")})
    if slot != expected:
        raise ValueError("Witness slot substitution")


def commit_witness_material(request, *, store_id, backup_generation, audit_count, audit_head, result_digest):
    """Build pre-response material from an admitted COMMIT and durable post-mutation cut."""
    proof = request["kernel_proof"]["kernel_projection"]
    slot = proof["mutation_witness_slot"]
    validate_slot(request, slot)
    if backup_generation != slot["backup_generation"] or not isinstance(store_id, str) or not store_id:
        raise ValueError("Identity store generation mismatch")
    digest(result_digest)
    digest(audit_head)
    if _number(audit_count) <= _number(proof["witnessed_audit_count"]):
        raise ValueError("mutation audit cut must advance")
    for name in ("kernel_pending_head", "projected_head"):
        digest(proof[name])
    if _number(proof["projected_epoch"]) != _number(request["expected_epoch"]) + 1:
        raise ValueError("mutation epoch must advance once")
    composite = witness_commitment(deployment_id=request["deployment_id"],
                                   logical_epoch=proof["projected_epoch"], logical_head=proof["projected_head"],
                                   audit_cut_count=audit_count, audit_cut_head=audit_head)
    record = WitnessRecord(PROTOCOL, request["deployment_id"], int(slot["epoch"]), int(slot["sequence"]),
                           slot["previous_record"], proof["kernel_pending_head"], H(composite),
                           int(backup_generation), slot["operation_id"])
    unsigned = canonical_bytes(record.unsigned())
    receipt = dict(profile="identity-mutation-staged-receipt/1", deployment_id=request["deployment_id"],
                   store_id=store_id, transaction_id=request["transaction_id"],
                   request_digest=request["request_digest"], prepared_request_digest=request["prepared_request_digest"],
                   stage_content_digest=proof["stage_content_digest"], domain_result_digest=result_digest,
                   prior_epoch=request["expected_epoch"], prior_head=request["expected_head"],
                   logical_epoch=proof["projected_epoch"], logical_head=proof["projected_head"],
                   audit_cut_count=audit_count, audit_cut_head=audit_head,
                   kernel_pending_head=proof["kernel_pending_head"], witness_slot=slot.copy(),
                   witness_preimage_digest=witness_digest(unsigned))
    return receipt, unsigned
