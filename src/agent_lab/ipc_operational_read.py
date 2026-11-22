"""Operational read schema only; no grants, signing, state or mutation."""
from copy import deepcopy

from datetime import datetime,date

import base64

import re

from cryptography.hazmat.primitives import hashes

from cryptography.hazmat.primitives.asymmetric import ec,utils

from agent_lab.ipc_wire_primitives import canonical_json_bytes,canonical_sha256,encode_frame,decode_frame

from agent_lab.ipc_envelope import (OPERATION_CAPABILITIES as DEV_CAPABILITIES,
    MUTATION_OPERATIONS as DEV_MUTATIONS, READ_OPERATIONS as DEV_READS)

# Additive operational 1.1 coverage; the frozen development 1.0 stays closed.
OPERATION_CAPABILITIES={**DEV_CAPABILITIES,"CORRECT_PERSON":"identity_update",
                        "LIST_RELATIONSHIPS":"identity_read","READ_FAMILY":"identity_read"}
MUTATION_OPERATIONS=DEV_MUTATIONS|{"CORRECT_PERSON"}
READ_OPERATIONS=DEV_READS|{"LIST_RELATIONSHIPS","READ_FAMILY"}

from agent_lab.identity_persistence import PARTY_ROLES

CONTRACT="oi0002.kernel-identity-c09/1.0"

DOMAIN=b"AI-TAX-AGENT\x00C09-KERNEL-PROOF\x00"

FIELDS=set("contract message_type transaction_id request_digest deployment_id scope_kind case_id tax_year run_id task_id manifest_id actor_instance_id role_id capability domain_operation expected_epoch expected_head authorization_references expires_at payload kernel_proof prepared_request_digest".split())

PROOF=set("proof_version key_id algorithm pending_row_digest kernel_projection authorization_state_version nonce issued_at not_after signature".split())

P256_ORDER=0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551

RESP=set("contract message_type transaction_id request_digest outcome response_digest identity_epoch identity_head staged_receipt_digest witness_preimage_digest signed_record_digest denial_code result".split())

DIGEST=re.compile(r"sha256:[0-9a-f]{64}\Z")

NUM=re.compile(r"0|[1-9][0-9]{0,19}\Z")

UUID=re.compile(r"tx:v1:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")

DENIALS={"AUTHORIZATION_DENIED","SCOPE_DENIED","TRANSACTION_CONFLICT","CONTINUITY_CONFLICT","REQUEST_INVALID","EXPIRED","UNSUPPORTED","TEMPORARY_FAILURE"}

PAYLOADS={
 "CORRECT_PERSON":set("request_id subject_id identity_record_ref expected_record_digest evidence_refs".split()),
 "REGISTER_IDENTITY":set("request_id subject_id identity_record_ref evidence_refs".split()),
 "UPDATE_IDENTITY_STATUS":set("request_id subject_id from_status to_status effective_date evidence_refs".split()),
 "BIND_PARTY":set("request_id subject_id party_role valid_from valid_to_exclusive evidence_refs".split()),
 "CORRECT_PARTY_ROLE":set("request_id prior_binding_ref replacement_binding_ref effective_date evidence_refs".split()),
 "BIND_FACT":set("request_id subject_id fact_envelope_ref valid_from valid_to_exclusive evidence_refs".split()),
}

def exact(value,fields):
    if not isinstance(value,dict) or set(value)!=fields: raise ValueError("closed fields mismatch")

def text(value,empty=False):
    if not isinstance(value,str) or (not value and not empty) or len(value.encode())>256: raise ValueError("invalid bounded string")

def digest(value):
    if not isinstance(value,str) or not DIGEST.fullmatch(value): raise ValueError("invalid digest")

def timestamp(value):
    if not isinstance(value,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z",value): raise ValueError("timestamp")
    return datetime.strptime(value,"%Y-%m-%dT%H:%M:%S.%fZ")

def refs(value,minimum=0):
    if not isinstance(value,list) or not minimum<=len(value)<=64 or value!=sorted(set(value)): raise ValueError("reference list")
    for item in value:digest(item)

def unsigned(request,for_digest=False):
    value=deepcopy(request);value["kernel_proof"].pop("signature",None)
    if for_digest:value.pop("request_digest",None)
    return value

def signing_bytes(request): return DOMAIN+canonical_json_bytes(unsigned(request))

def validate_request(value,public_key,*,expected_scope,now,expected_key_id,expected_contract=CONTRACT,bootstrap_artifact=None, mutation_commit_contract=False, mutation_runtime=False):
    exact(value,FIELDS)
    bootstrap=bootstrap_artifact is not None
    if bootstrap:
        from agent_lab.identity_logical_continuity import H,genesis_preimage
        if expected_contract!="oi0002.kernel-identity-c09/1.1" or value["message_type"]!="GET_ENROLLMENT_STATUS" or value["domain_operation"]!="READ_ENROLLMENT_STATUS" or value["capability"]!="identity_enrollment_status":raise ValueError("closed bootstrap operation required")
        owner=bootstrap_artifact
        for field,target in (("task_id","bootstrap_task_id"),("manifest_id","bootstrap_manifest_id"),("run_id","bootstrap_run_id"),("actor_instance_id","bootstrap_actor_instance_id"),("role_id","bootstrap_role_id")):
            if value[field]!=owner[target]:raise ValueError("bootstrap Owner scope mismatch")
        if value["deployment_id"]!=owner["deployment_id"] or value["authorization_references"]!=[H(owner)] or value["expected_epoch"]!="0" or value["expected_head"]!=H(genesis_preimage(owner)):raise ValueError("bootstrap authority/head mismatch")
    elif mutation_runtime:
        if (expected_contract != "oi0002.kernel-identity-c09/1.1"
                or value["message_type"] not in {"PREPARE_MUTATION", "COMMIT_MUTATION", "FINALIZE_MUTATION", "GET_TRANSACTION", "ABORT_PREPARED"}
                or value["domain_operation"] not in MUTATION_OPERATIONS):
            raise ValueError("closed mutation runtime required")
    elif mutation_commit_contract:
        if (expected_contract!="oi0002.kernel-identity-c09/1.1" or value["message_type"]!="COMMIT_MUTATION"
                or value["domain_operation"] not in MUTATION_OPERATIONS):
            raise ValueError("versioned mutation COMMIT required")
    elif value["message_type"]!="READ_IDENTITY_STATE" or value["domain_operation"] not in READ_OPERATIONS:raise ValueError("protected or unknown operation disabled")
    exact(expected_scope,set("deployment_id case_id tax_year run_id task_id manifest_id actor_instance_id role_id".split()))
    for scoped in expected_scope.values():text(scoped)
    text(expected_key_id)
    if expected_contract not in {CONTRACT,"oi0002.kernel-identity-c09/1.1"} or value["contract"]!=expected_contract or not UUID.fullmatch(value["transaction_id"]):raise ValueError("contract or transaction")
    for name in FIELDS-{"payload","kernel_proof","authorization_references"}:text(value[name],name=="prepared_request_digest")
    digest(value["request_digest"]);digest(value["expected_head"])
    if not NUM.fullmatch(value["expected_epoch"]):raise ValueError("epoch")
    if bootstrap:
        if value["scope_kind"]!="DEPLOYMENT_STORE" or value["case_id"]!="*" or value["tax_year"]!="*":raise ValueError("bootstrap metadata scope")
    elif value["scope_kind"]!="CASE_YEAR" or not re.fullmatch(r"\d{4}",value["tax_year"]) or not 1900<=int(value["tax_year"])<=9998:raise ValueError("scope")
    if {k:value[k] for k in expected_scope}!=expected_scope:raise ValueError("cross scope")
    operation=value["domain_operation"];message=value["message_type"]
    if operation in {"CORRECT_PERSON","LIST_RELATIONSHIPS","READ_FAMILY"} and expected_contract!="oi0002.kernel-identity-c09/1.1":raise ValueError("Family operations require operational 1.1")
    if not bootstrap and (operation not in OPERATION_CAPABILITIES or value["capability"]!=OPERATION_CAPABILITIES[operation]):raise ValueError("capability")
    reads=operation in READ_OPERATIONS or bootstrap
    if not bootstrap and (reads and message!="READ_IDENTITY_STATE" or not reads and message not in {"PREPARE_MUTATION","COMMIT_MUTATION","FINALIZE_MUTATION","GET_TRANSACTION","ABORT_PREPARED"}):raise ValueError("message mapping")
    if message=="COMMIT_MUTATION":digest(value["prepared_request_digest"])
    elif value["prepared_request_digest"]!="":raise ValueError("unexpected prepared digest")
    payload=value["payload"]
    if bootstrap:
        exact(payload,{"enrollment_id","owner_authorization_digest"})
        if payload!={"enrollment_id":owner["enrollment_id"],"owner_authorization_digest":H(owner)}:raise ValueError("bootstrap artifact substitution")
    elif reads:
        exact(payload,{"subject_id","as_of_date"});text(payload["subject_id"],operation in {"LIST_PARTIES","LIST_RELATIONSHIPS","READ_FAMILY"})
        if operation in {"LIST_PARTIES","LIST_RELATIONSHIPS","READ_FAMILY"} and payload["subject_id"]!="":raise ValueError("list subject must be empty")
        if operation=="READ_FACTS" and payload["as_of_date"]!="":raise ValueError("facts use tax year")
        if operation!="READ_FACTS":
            parsed=date.fromisoformat(payload["as_of_date"])
            if parsed.isoformat()!=payload["as_of_date"] or parsed.year!=int(value["tax_year"]):raise ValueError("as-of date")
    elif message in {"GET_TRANSACTION","ABORT_PREPARED"}:
        exact(payload,{"original_request_digest"});digest(payload["original_request_digest"])
    elif message=="FINALIZE_MUTATION":
        exact(payload,set("staged_receipt_digest witness_object_key witness_generation witness_preimage_digest signed_record_digest custodian_verification_digest custodian_nonce".split()))
    else:
        fields=PAYLOADS[operation]
        if operation in {"REGISTER_IDENTITY","CORRECT_PERSON","BIND_PARTY"} and "owner_input_digest" in payload:
            fields=fields|{"owner_input_digest"}
            digest(payload["owner_input_digest"])
        exact(payload,fields)
        for k,v in payload.items():
            if k=="evidence_refs":refs(v,1)
            else:text(v,k=="valid_to_exclusive")
    if not reads and message in {"PREPARE_MUTATION","COMMIT_MUTATION"}:
        if operation=="CORRECT_PERSON":digest(payload["expected_record_digest"])
    proof=value["kernel_proof"];exact(proof,PROOF)
    if proof["proof_version"]!="1" or proof["algorithm"]!="ECDSA-P256-SHA256" or proof["key_id"]!=expected_key_id:raise ValueError("proof identity")
    digest(proof["pending_row_digest"])
    projection=proof["kernel_projection"];expected=read_projection(value)
    if mutation_commit_contract or mutation_runtime and message == "COMMIT_MUTATION":
        from agent_lab.f07_commit_witness import validate_slot
        validate_slot(value, projection.get("mutation_witness_slot"))
        expected["mutation_witness_slot"]=projection["mutation_witness_slot"]
    exact(projection,set(expected))
    if bootstrap and (projection["witnessed_audit_count"],projection["witnessed_audit_head"])!=(owner["enrollment_audit_count"],owner["enrollment_audit_head"]):raise ValueError("bootstrap witnessed prefix substitution")
    if canonical_sha256(projection)!=proof["pending_row_digest"]:raise ValueError("projection digest")
    for name in expected:
        if name not in {"projected_epoch","projected_head","kernel_pending_head"} and projection[name]!=expected[name]:raise ValueError("projection correlation")
    if message=="COMMIT_MUTATION":
        digest(projection["kernel_pending_head"]);digest(projection["projected_head"])
        if not isinstance(projection["projected_epoch"],str) or not NUM.fullmatch(projection["projected_epoch"]):raise ValueError("projected epoch")
    elif reads and any(projection[name]!=expected[name] for name in ("projected_epoch","projected_head","kernel_pending_head")):raise ValueError("read projection")
    if not NUM.fullmatch(proof["authorization_state_version"]):raise ValueError("authorization revision")
    if not re.fullmatch(r"[0-9a-f]{64}",proof["nonce"]):raise ValueError("nonce")
    issued=timestamp(proof["issued_at"]);expires=timestamp(proof["not_after"])
    if not issued<=now<expires or not 0<(expires-issued).total_seconds()<=5 or timestamp(value["expires_at"])!=expires:raise ValueError("expiry")
    refs(value["authorization_references"])
    if canonical_sha256(unsigned(value,True))!=value["request_digest"]:raise ValueError("request digest")
    sig=proof["signature"]
    if not isinstance(sig,str) or not re.fullmatch(r"[A-Za-z0-9_-]{86}",sig):raise ValueError("signature encoding")
    raw=base64.urlsafe_b64decode(sig+"==")
    if base64.urlsafe_b64encode(raw).rstrip(b"=").decode()!=sig:raise ValueError("noncanonical signature")
    if not isinstance(public_key.curve,ec.SECP256R1):raise ValueError("curve")
    r,s=int.from_bytes(raw[:32],"big"),int.from_bytes(raw[32:],"big")
    if not 1<=r<P256_ORDER or not 1<=s<=P256_ORDER//2:raise ValueError("noncanonical high-S signature")
    public_key.verify(utils.encode_dss_signature(r,s),signing_bytes(value),ec.ECDSA(hashes.SHA256()))
    decode_frame(encode_frame(value))

PERSON=set("person_id status preferred_display_name created_at updated_at schema_version lookup_attributes".split())

ENTITY=(PERSON-{"person_id"})|{"entity_id"}

PARTY=set("binding_id case_id subject_type subject_id role valid_from valid_to_exclusive evidence_ref authorization_ref".split())

FACT=set("request_id case_id tax_year subject_type subject_id semantic_key fact_artifact_ref declaration_artifact_ref confirmation_ref authorization_ref valid_from valid_to_exclusive audit_lineage revision".split())

def validate_result(result,request):
    exact(result,{"case_id","tax_year","run_id","domain_operation","items"})
    for key in set(result)-{"items"}:
        if result[key]!=request[key]:raise ValueError("result scope")
    items=result["items"];operation=request["domain_operation"]
    if not isinstance(items,list) or len(items)>64:raise ValueError("result limit")
    if operation=="READ_FAMILY":
        if len(items)!=1:raise ValueError("family snapshot cardinality")
        snapshot=items[0];exact(snapshot,{"people","relationships"})
        people=snapshot["people"]
        if not isinstance(people,list) or len(people)>64:raise ValueError("family person bound")
        parties=[]
        for pair in people:
            exact(pair,{"person","party"});exact(pair["person"],PERSON)
            child=deepcopy(request);child["domain_operation"]="READ_CASE_IDENTITY"
            child["payload"]["subject_id"]=pair["party"]["subject_id"]
            validate_result({**result,"domain_operation":"READ_CASE_IDENTITY","items":[pair["person"]]},child)
            if pair["party"]["subject_type"]!="PERSON":raise ValueError("family person type")
            parties.append(pair["party"])
        for operation,children in (("LIST_PARTIES",parties),("LIST_RELATIONSHIPS",snapshot["relationships"])):
            child=deepcopy(request);child["domain_operation"]=operation
            validate_result({**result,"domain_operation":operation,"items":children},child)
    elif operation=="READ_CASE_IDENTITY":
        if len(items)!=1:raise ValueError("identity cardinality")
        item=items[0];fields=PERSON if "person_id" in item else ENTITY;exact(item,fields)
        key="person_id" if "person_id" in item else "entity_id"
        if item[key]!=request["payload"]["subject_id"] or item["status"]!="ACTIVE":raise ValueError("identity subject")
        text(item["preferred_display_name"],True)
        if not isinstance(item["lookup_attributes"],list) or len(item["lookup_attributes"])>64:raise ValueError("lookup bounds")
        for pair in item["lookup_attributes"]:
            if not isinstance(pair,list) or len(pair)!=2:raise ValueError("lookup pair")
            for value in pair:text(value)
        timestamp(item["created_at"]);timestamp(item["updated_at"])
        if not re.fullmatch(r"[1-9][0-9]{0,19}",item["schema_version"]):raise ValueError("schema version")
    elif operation=="LIST_RELATIONSHIPS":
        keys=[]
        fields=set("relationship_id case_id relationship_type subject_a_id subject_b_id valid_from valid_to_exclusive evidence_ref authorization_ref revision".split())
        for item in items:
            exact(item,fields)
            for name in fields:text(item[name],name=="valid_to_exclusive")
            if item["case_id"]!=request["case_id"] or item["relationship_type"]!="MARRIAGE" or item["subject_a_id"]>=item["subject_b_id"]:raise ValueError("relationship scope/type")
            digest(item["evidence_ref"]);digest(item["authorization_ref"])
            if not re.fullmatch(r"[1-9][0-9]{0,19}",item["revision"]):raise ValueError("relationship revision")
            as_of=date.fromisoformat(request["payload"]["as_of_date"])
            if date.fromisoformat(item["valid_from"])>as_of or item["valid_to_exclusive"] and as_of>=date.fromisoformat(item["valid_to_exclusive"]):raise ValueError("relationship interval")
            keys.append(item["relationship_id"])
        if keys!=sorted(set(keys)):raise ValueError("relationship order")
    else:
        fields=PARTY if operation in {"LIST_PARTIES","LIST_RELATIONSHIPS","READ_FAMILY"} else FACT
        keys=[]
        for item in items:
            exact(item,fields)
            if item["case_id"]!=request["case_id"]:raise ValueError("item case")
            for name in fields-{"audit_lineage"}:text(item[name],name=="valid_to_exclusive")
            if item["subject_type"] not in {"PERSON","ENTITY"}:raise ValueError("subject type")
            if operation in {"LIST_PARTIES","LIST_RELATIONSHIPS","READ_FAMILY"}:
                if item["role"] not in PARTY_ROLES:raise ValueError("role")
                digest(item["evidence_ref"]);digest(item["authorization_ref"])
                keys.append(item["binding_id"])
                as_of=date.fromisoformat(request["payload"]["as_of_date"])
                if date.fromisoformat(item["valid_from"])>as_of or item["valid_to_exclusive"] and as_of>=date.fromisoformat(item["valid_to_exclusive"]):raise ValueError("role interval coverage")
            else:
                if item["subject_id"]!=request["payload"]["subject_id"] or item["tax_year"]!=request["tax_year"]:raise ValueError("fact subject/year")
                for name in ("fact_artifact_ref","declaration_artifact_ref","confirmation_ref","authorization_ref"):digest(item[name])
                if not isinstance(item["audit_lineage"],list) or len(item["audit_lineage"])>64:raise ValueError("lineage bounds")
                for reference in item["audit_lineage"]:digest(reference)
                if not re.fullmatch(r"[1-9][0-9]{0,19}",item["revision"]):raise ValueError("revision")
                keys.append(item["request_id"])
            start=date.fromisoformat(item["valid_from"]);end=date.fromisoformat(item["valid_to_exclusive"]) if item["valid_to_exclusive"] else None
            if start.isoformat()!=item["valid_from"] or end is not None and end.isoformat()!=item["valid_to_exclusive"]:raise ValueError("noncanonical date")
            if end is not None and start>=end:raise ValueError("interval")
            if operation=="READ_FACTS" and (end is None or not date(int(request["tax_year"]),1,1)<=start<end<=date(int(request["tax_year"])+1,1,1)):raise ValueError("fact year interval")
        if keys!=sorted(set(keys)):raise ValueError("result order")

CONTROL_OUTCOMES = {
    "FINALIZE_MUTATION": {"COMMITTED_FINAL", "NOT_FINALIZABLE"},
    "GET_TRANSACTION": {"PREPARED", "IDENTITY_COMMITTED", "COMMITTED_FINAL", "ABORTED", "NOT_FINALIZABLE"},
    "ABORT_PREPARED": {"ABORTED", "NOT_FINALIZABLE"},
}
RECEIPT_FIELDS = ("staged_receipt_digest", "witness_preimage_digest", "signed_record_digest")
CONTROL_SCOPE = set("deployment_id transaction_id scope_kind case_id tax_year run_id task_id manifest_id actor_instance_id role_id capability domain_operation".split())
SNAPSHOT_FIELDS = {"outcome", "identity_epoch", "identity_head", "identity_audit_count", "identity_audit_head", *RECEIPT_FIELDS}
FINALIZE_FIELDS = set("staged_receipt_digest witness_object_key witness_generation witness_preimage_digest signed_record_digest custodian_verification_digest custodian_nonce".split())


def _validate_control_success(value, request, checkpoint):
    """Bind a positive response to independently verified durable stage evidence."""
    exact(checkpoint, {"scope", "prepare_digest", "snapshot", "finalize_payload"})
    exact(checkpoint["scope"], CONTROL_SCOPE)
    if checkpoint["scope"] != {name: request[name] for name in CONTROL_SCOPE}:
        raise ValueError("transaction checkpoint scope")
    digest(checkpoint["prepare_digest"])
    snapshot = checkpoint["snapshot"]
    exact(snapshot, SNAPSHOT_FIELDS)
    if snapshot != {name: value[name] for name in SNAPSHOT_FIELDS}:
        raise ValueError("transaction checkpoint response mismatch")

    message = request["message_type"]
    if message != "FINALIZE_MUTATION":
        exact(request["payload"], {"original_request_digest"})
        if request["payload"]["original_request_digest"] != checkpoint["prepare_digest"]:
            raise ValueError("original PREPARE correlation")

    finalization = checkpoint["finalize_payload"]
    if value["outcome"] != "COMMITTED_FINAL":
        if finalization is not None:
            raise ValueError("unexpected finality evidence")
        return
    exact(finalization, FINALIZE_FIELDS)
    for name in (*RECEIPT_FIELDS, "custodian_verification_digest"):
        digest(finalization[name])
    text(finalization["witness_object_key"])
    generation = finalization["witness_generation"]
    if not isinstance(generation, str) or not re.fullmatch(r"[1-9][0-9]{0,19}", generation):
        raise ValueError("invalid Witness generation")
    if not isinstance(finalization["custodian_nonce"], str) or not re.fullmatch(r"[0-9a-f]{64}", finalization["custodian_nonce"]):
        raise ValueError("invalid Custodian nonce")
    if any(value[name] != finalization[name] for name in RECEIPT_FIELDS):
        raise ValueError("Witness and Commit receipt correlation")
    if message == "FINALIZE_MUTATION" and request["payload"] != finalization:
        raise ValueError("FINALIZE evidence substitution")


def validate_response(value,request,*,transaction_checkpoint=None,mutation_material_context=None):
    """Validate bytes and correlation, never grant authority or prove finality.

    For IPC 1.1 control successes, transaction_checkpoint must come from
    authenticated durable state and verified receipts, never from the peer's
    proposed response. Existing request admission remains read-only.
    """
    version11=request["contract"]=="oi0002.kernel-identity-c09/1.1"
    if request["message_type"]=="GET_ENROLLMENT_STATUS" and not version11:raise ValueError("bootstrap requires 1.1")
    exact(value,RESP|{"identity_audit_count","identity_audit_head"} if version11 else RESP)
    for name in ("contract","message_type","transaction_id","request_digest"):
        if value[name]!=request[name]:raise ValueError("response correlation")
    body=deepcopy(value);body.pop("response_digest");digest(value["response_digest"])
    if canonical_sha256(body)!=value["response_digest"]:raise ValueError("response digest")
    outcomes={"PREPARE_MUTATION":{"PREPARED","DENIED","CONFLICT"},"COMMIT_MUTATION":{"IDENTITY_COMMITTED","DENIED","CONFLICT","NOT_FINALIZABLE"},"READ_IDENTITY_STATE":{"READ_OK","DENIED","CONFLICT"},"GET_ENROLLMENT_STATUS":{"ENROLLMENT_READY","DENIED","CONFLICT"}}
    control = version11 and request["message_type"] in CONTROL_OUTCOMES
    if control:
        operation = request["domain_operation"]
        if operation not in MUTATION_OPERATIONS or request["capability"] != OPERATION_CAPABILITIES[operation]:
            raise ValueError("control operation capability")
        outcomes[request["message_type"]] = CONTROL_OUTCOMES[request["message_type"]] | {"DENIED", "CONFLICT"}
    if value["outcome"] not in outcomes.get(request["message_type"],set()):raise ValueError("response outcome")
    withheld = version11 and value["outcome"] == "NOT_FINALIZABLE"
    if withheld and value["denial_code"] not in {"RECONCILIATION_REQUIRED", "TEMPORARY_FAILURE"}:
        raise ValueError("indeterminate outcome requires a recovery denial")
    if withheld or value["outcome"] in {"DENIED","CONFLICT"}:
        if value["denial_code"] not in (DENIALS|{"RECONCILIATION_REQUIRED"} if version11 else DENIALS) or any(value[k]!="" for k in ("identity_epoch","identity_head","staged_receipt_digest","witness_preimage_digest","signed_record_digest","result")):raise ValueError("denial disclosure")
        if version11 and (value["identity_audit_count"]!="" or value["identity_audit_head"]!=""):raise ValueError("denial audit disclosure")
    else:
        if value["denial_code"]!="" or not NUM.fullmatch(value["identity_epoch"]):raise ValueError("outcome metadata")
        digest(value["identity_head"])
        if version11:
            if not isinstance(value["identity_audit_count"],str) or not NUM.fullmatch(value["identity_audit_count"]):raise ValueError("audit count")
            digest(value["identity_audit_head"])
            if value["outcome"] in {"READ_OK","ENROLLMENT_READY"} and (value["identity_epoch"],value["identity_head"])!=(request["expected_epoch"],request["expected_head"]):raise ValueError("read logical head changed")
        if value["outcome"]=="ENROLLMENT_READY":
            exact(value["result"],set("enrollment_id store_id owner_authorization_digest domain_snapshot_digest genesis_head".split()))
            if value["result"]["enrollment_id"]!=request["payload"]["enrollment_id"] or value["result"]["owner_authorization_digest"]!=request["payload"]["owner_authorization_digest"] or value["result"]["genesis_head"]!=value["identity_head"]:raise ValueError("bootstrap result binding")
            text(value["result"]["store_id"]);digest(value["result"]["domain_snapshot_digest"])
        elif value["outcome"]=="READ_OK":validate_result(value["result"],request)
        elif mutation_material_context is not None and value["outcome"]=="IDENTITY_COMMITTED" and version11:
            from agent_lab.f07_commit_witness import validate_commit_material
            exact(mutation_material_context, {"original_commit", "store_id", "backup_generation"})
            original = mutation_material_context["original_commit"]
            if (request["message_type"] not in {"COMMIT_MUTATION", "GET_TRANSACTION"}
                    or any(request[name] != original[name] for name in CONTROL_SCOPE)):
                raise ValueError("Commit material request scope")
            if request["message_type"] == "COMMIT_MUTATION":
                old = original["kernel_proof"]["kernel_projection"]
                current = request["kernel_proof"]["kernel_projection"]
                if (request["prepared_request_digest"] != original["prepared_request_digest"]
                        or any(current[k] != old[k] for k in ("mutation_witness_slot", "stage_content_digest",
                            "kernel_pending_head", "projected_head", "projected_epoch"))):
                    raise ValueError("Commit material request substitution")
            elif request["payload"]["original_request_digest"] != original["prepared_request_digest"]:
                raise ValueError("Commit material PREPARE mismatch")
            validate_commit_material(value["result"], response=value, **mutation_material_context)
        elif value["result"]!="":raise ValueError("nonread result")
        if value["outcome"] in {"READ_OK","PREPARED","ENROLLMENT_READY"} and any(value[k]!="" for k in ("staged_receipt_digest","witness_preimage_digest","signed_record_digest")):raise ValueError("unexpected receipt")
        if control:
            _validate_control_success(value, request, transaction_checkpoint)
            if value["outcome"] == "ABORTED" and any(value[name] != "" for name in RECEIPT_FIELDS):
                raise ValueError("abort cannot carry a Commit receipt")
        if value["outcome"]=="IDENTITY_COMMITTED":
            digest(value["staged_receipt_digest"]);digest(value["witness_preimage_digest"])
            if value["signed_record_digest"]!="":raise ValueError("premature final receipt")
    decode_frame(encode_frame(value))

def read_projection(request):
    fields="contract deployment_id transaction_id task_id manifest_id actor_instance_id role_id case_id tax_year run_id domain_operation capability expected_epoch expected_head authorization_references prepared_request_digest".split()
    value={field:deepcopy(request[field]) for field in fields}
    content=deepcopy(request);content.pop("request_digest");content.pop("kernel_proof")
    stable=deepcopy(content);stable.pop("expires_at")
    value.update(authorization_state_version=request["kernel_proof"]["authorization_state_version"],projected_epoch=request["expected_epoch"],projected_head=request["expected_head"],kernel_pending_head="",request_content_digest=canonical_sha256(content),stage_content_digest=canonical_sha256(stable))
    if request["contract"]=="oi0002.kernel-identity-c09/1.1":
        supplied=request["kernel_proof"]["kernel_projection"]
        count=supplied["witnessed_audit_count"];head=supplied["witnessed_audit_head"];recovery=supplied["recovery_request_digest"]
        if not isinstance(count,str) or not NUM.fullmatch(count):raise ValueError("witnessed audit count")
        digest(head)
        if recovery!="":digest(recovery)
        value.update(witnessed_audit_count=count,witnessed_audit_head=head,recovery_request_digest=recovery)
    return value
