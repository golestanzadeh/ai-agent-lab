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

def validate_commit_material(value, *, original_commit, response, store_id, backup_generation):
    """Check canonical material returned across the authenticated Kernel/Identity boundary."""
    from agent_lab.c09_custodian_operational import pack
    from agent_lab.ipc_wire_primitives import canonical_json_bytes
    from agent_lab.identity_logical_continuity import successor_preimage

    exact(value, {"profile", "receipt", "unsigned_record_bytes"})
    if value["profile"] != "identity-mutation-commit-material/1":
        raise ValueError("unknown mutation material profile")
    receipt = value["receipt"]
    if not isinstance(receipt, dict) or len(canonical_json_bytes(receipt)) > 4096:
        raise ValueError("invalid staged receipt size")
    result_digest = receipt.get("domain_result_digest")
    digest(result_digest)
    stable_mutation = {key: item for key, item in original_commit.items() if key not in {
        "message_type", "request_digest", "kernel_proof", "expires_at", "prepared_request_digest"}}
    successor = successor_preimage(
        deployment_id=original_commit["deployment_id"], prior_epoch=original_commit["expected_epoch"],
        prior_head=original_commit["expected_head"], case_id=original_commit["case_id"],
        tax_year=original_commit["tax_year"], transaction_id=original_commit["transaction_id"],
        domain_operation=original_commit["domain_operation"], mutation_content_digest=H(stable_mutation),
        domain_result_digest=result_digest)
    expected, unsigned = commit_witness_material(
        original_commit, store_id=store_id, backup_generation=backup_generation,
        audit_count=response["identity_audit_count"], audit_head=response["identity_audit_head"],
        result_digest=result_digest)
    if (receipt != expected or len(unsigned) > 4096 or value["unsigned_record_bytes"] != pack(unsigned)
            or H(receipt) != response["staged_receipt_digest"]
            or expected["witness_preimage_digest"] != response["witness_preimage_digest"]
            or (expected["logical_epoch"], expected["logical_head"]) !=
            (response["identity_epoch"], response["identity_head"])
            or H(successor) != response["identity_head"]
            or original_commit["transaction_id"] != response["transaction_id"]):
        raise ValueError("mutation Commit material binding mismatch")
