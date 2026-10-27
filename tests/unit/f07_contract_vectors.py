"""Offline operational-contract vectors. No service, authorization or I/O."""
from copy import deepcopy
from datetime import datetime,date
import base64
import re

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec,utils
from agent_lab.ipc_wire_primitives import canonical_json_bytes,canonical_sha256,encode_frame,decode_frame
from agent_lab.ipc_envelope import OPERATION_CAPABILITIES,MUTATION_OPERATIONS,READ_OPERATIONS
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


def stable_content_digest(request):
    """Stable stage identity excludes only cryptographic attempt material."""
    value=deepcopy(request)
    for name in ("request_digest","kernel_proof","expires_at"):value.pop(name,None)
    return canonical_sha256(value)

def pending_projection(request):
    fields="contract deployment_id transaction_id task_id manifest_id actor_instance_id role_id case_id tax_year run_id domain_operation capability expected_epoch expected_head authorization_references prepared_request_digest".split()
    value={field:deepcopy(request[field]) for field in fields}
    content=deepcopy(request);content.pop("request_digest",None);content.pop("kernel_proof",None)
    value.update(authorization_state_version=request["kernel_proof"]["authorization_state_version"],
        projected_epoch=request["expected_epoch"],projected_head=request["expected_head"],
        kernel_pending_head="sha256:"+"d"*64 if request["message_type"]=="COMMIT_MUTATION" else "",
        request_content_digest=canonical_sha256(content),stage_content_digest=stable_content_digest(request))
    return value

def sign(request,key):
    value=deepcopy(request)
    value["kernel_proof"]["kernel_projection"]=pending_projection(value)
    value["kernel_proof"]["pending_row_digest"]=canonical_sha256(value["kernel_proof"]["kernel_projection"])
    return seal(value,key)


def seal(request,key):
    value=deepcopy(request)
    value["request_digest"]=canonical_sha256(unsigned(value,True))
    signature=key.sign(signing_bytes(value),ec.ECDSA(hashes.SHA256(),deterministic_signing=True))
    r,s=utils.decode_dss_signature(signature)
    s=min(s,P256_ORDER-s)
    value["kernel_proof"]["signature"]=base64.urlsafe_b64encode(r.to_bytes(32,"big")+s.to_bytes(32,"big")).rstrip(b"=").decode()
    return value

def validate_request(value,public_key,*,expected_scope,now,expected_key_id="TEST-KERNEL-KEY-1"):
    exact(value,FIELDS)
    if value["contract"]!=CONTRACT or not UUID.fullmatch(value["transaction_id"]):raise ValueError("contract or transaction")
    for name in FIELDS-{"payload","kernel_proof","authorization_references"}:text(value[name],name=="prepared_request_digest")
    digest(value["request_digest"]);digest(value["expected_head"])
    if not NUM.fullmatch(value["expected_epoch"]):raise ValueError("epoch")
    if value["scope_kind"]!="CASE_YEAR" or not re.fullmatch(r"\d{4}",value["tax_year"]) or not 1900<=int(value["tax_year"])<=9998:raise ValueError("scope")
    if {k:value[k] for k in expected_scope}!=expected_scope:raise ValueError("cross scope")
    operation=value["domain_operation"];message=value["message_type"]
    if operation not in OPERATION_CAPABILITIES or value["capability"]!=OPERATION_CAPABILITIES[operation]:raise ValueError("capability")
    reads=operation in READ_OPERATIONS
    if reads and message!="READ_IDENTITY_STATE" or not reads and message not in {"PREPARE_MUTATION","COMMIT_MUTATION","FINALIZE_MUTATION","GET_TRANSACTION","ABORT_PREPARED"}:raise ValueError("message mapping")
    if message=="COMMIT_MUTATION":digest(value["prepared_request_digest"])
    elif value["prepared_request_digest"]!="":raise ValueError("unexpected prepared digest")
    payload=value["payload"]
    if reads:
        exact(payload,{"subject_id","as_of_date"});text(payload["subject_id"],operation=="LIST_PARTIES")
        if operation=="LIST_PARTIES" and payload["subject_id"]!="":raise ValueError("list subject must be empty")
        if operation=="READ_FACTS" and payload["as_of_date"]!="":raise ValueError("facts use tax year")
        if operation!="READ_FACTS":
            parsed=date.fromisoformat(payload["as_of_date"])
            if parsed.isoformat()!=payload["as_of_date"] or parsed.year!=int(value["tax_year"]):raise ValueError("as-of date")
    elif message in {"GET_TRANSACTION","ABORT_PREPARED"}:
        exact(payload,{"original_request_digest"});digest(payload["original_request_digest"])
    elif message=="FINALIZE_MUTATION":
        exact(payload,set("staged_receipt_digest witness_object_key witness_generation witness_preimage_digest signed_record_digest custodian_verification_digest custodian_nonce".split()))
    else:
        exact(payload,PAYLOADS[operation])
        for k,v in payload.items():
            if k=="evidence_refs":refs(v,1)
            else:text(v,k=="valid_to_exclusive")
    proof=value["kernel_proof"];exact(proof,PROOF)
    if proof["proof_version"]!="1" or proof["algorithm"]!="ECDSA-P256-SHA256" or proof["key_id"]!=expected_key_id:raise ValueError("proof identity")
    digest(proof["pending_row_digest"])
    projection=proof["kernel_projection"];expected=pending_projection(value);exact(projection,set(expected))
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

def validate_prepare_commit(prepare,commit):
    if prepare["message_type"]!="PREPARE_MUTATION" or commit["message_type"]!="COMMIT_MUTATION" or commit["prepared_request_digest"]!=prepare["request_digest"]:raise ValueError("prepare linkage")
    for field in ("transaction_id","deployment_id","case_id","tax_year","run_id","task_id","manifest_id","actor_instance_id","role_id","domain_operation","capability","payload","expected_epoch","expected_head","authorization_references"):
        if prepare[field]!=commit[field]:raise ValueError("prepare content mismatch")


def validate_renewed_attempt(previous,current,consumed_nonces):
    """Offline retry relationship only; runtime uses its existing durable rows."""
    if stable_content_digest(previous)!=stable_content_digest(current):raise ValueError("changed stage content")
    if current["kernel_proof"]["nonce"] in consumed_nonces:raise ValueError("consumed proof")
    if timestamp(current["kernel_proof"]["issued_at"])<=timestamp(previous["kernel_proof"]["issued_at"]):raise ValueError("not renewed")

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
    if operation=="READ_CASE_IDENTITY":
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
    else:
        fields=PARTY if operation=="LIST_PARTIES" else FACT
        keys=[]
        for item in items:
            exact(item,fields)
            if item["case_id"]!=request["case_id"]:raise ValueError("item case")
            for name in fields-{"audit_lineage"}:text(item[name],name=="valid_to_exclusive")
            if item["subject_type"] not in {"PERSON","ENTITY"}:raise ValueError("subject type")
            if operation=="LIST_PARTIES":
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
            if end is not None and start>=end:raise ValueError("interval")
            if operation=="READ_FACTS" and (end is None or not date(int(request["tax_year"]),1,1)<=start<end<=date(int(request["tax_year"])+1,1,1)):raise ValueError("fact year interval")
        if keys!=sorted(set(keys)):raise ValueError("result order")

def validate_response(value,request):
    exact(value,RESP)
    for name in ("contract","message_type","transaction_id","request_digest"):
        if value[name]!=request[name]:raise ValueError("response correlation")
    body=deepcopy(value);body.pop("response_digest");digest(value["response_digest"])
    if canonical_sha256(body)!=value["response_digest"]:raise ValueError("response digest")
    outcomes={"PREPARE_MUTATION":{"PREPARED","DENIED","CONFLICT"},"COMMIT_MUTATION":{"IDENTITY_COMMITTED","DENIED","CONFLICT","NOT_FINALIZABLE"},"READ_IDENTITY_STATE":{"READ_OK","DENIED","CONFLICT"}}
    if value["outcome"] not in outcomes.get(request["message_type"],set()):raise ValueError("response outcome")
    if value["outcome"] in {"DENIED","CONFLICT"}:
        if value["denial_code"] not in DENIALS or any(value[k]!="" for k in ("identity_epoch","identity_head","staged_receipt_digest","witness_preimage_digest","signed_record_digest","result")):raise ValueError("denial disclosure")
    else:
        if value["denial_code"]!="" or not NUM.fullmatch(value["identity_epoch"]):raise ValueError("outcome metadata")
        digest(value["identity_head"])
        if value["outcome"]=="READ_OK":validate_result(value["result"],request)
        elif value["result"]!="":raise ValueError("nonread result")
        if value["outcome"] in {"READ_OK","PREPARED"} and any(value[k]!="" for k in ("staged_receipt_digest","witness_preimage_digest","signed_record_digest")):raise ValueError("unexpected receipt")
        if value["outcome"]=="IDENTITY_COMMITTED":
            digest(value["staged_receipt_digest"]);digest(value["witness_preimage_digest"])
            if value["signed_record_digest"]!="":raise ValueError("premature final receipt")
    decode_frame(encode_frame(value))


def negative_vectors(vectors,commit):
    """Frozen hostile frames; semantic mutations are re-signed where appropriate."""
    import struct
    key=ec.derive_private_key(1,ec.SECP256R1())
    output=[]
    def add(name,value,kind="request",base=0,resign=False):
        if resign:value=sign(value,key)
        if kind=="response":
            body=deepcopy(value);body.pop("response_digest");value["response_digest"]=canonical_sha256(body)
        output.append({"name":name,"kind":kind,"base":str(base),"frame_hex":encode_frame(value).hex()})
    for name,action,resign in (
        ("missing-proof",lambda r:r.pop("kernel_proof"),False),
        ("misplaced-proof",lambda r:r["payload"].update(kernel_proof=r.pop("kernel_proof")),False),
        ("missing-prepared",lambda r:r.pop("prepared_request_digest"),False),
        ("misplaced-prepared",lambda r:r["payload"].update(prepared_request_digest=r.pop("prepared_request_digest")),False),
        ("unknown-field",lambda r:r.update(extra="forbidden"),False),
        ("circular-digest",lambda r:r.update(request_digest=canonical_sha256(r)),False),
        ("invalid-signature",lambda r:r["kernel_proof"].update(signature="A"*86),False),
        ("modified-signed-field",lambda r:r.update(task_id="TEST-ALTERED"),False),
        ("wrong-message",lambda r:r.update(message_type="READ_IDENTITY_STATE"),True),
        ("wrong-capability",lambda r:r.update(capability="identity_read"),True),
        ("cross-case",lambda r:r.update(case_id="TEST-OTHER"),True),
        ("cross-year",lambda r:r.update(tax_year="2025"),True),
        ("cross-run",lambda r:r.update(run_id="TEST-OTHER"),True),
        ("oversize-field",lambda r:r.update(task_id="x"*257),True),
        ("unknown-version",lambda r:r.update(contract="oi0002.kernel-identity-c09/2.0"),True),
        ("unknown-operation",lambda r:r.update(domain_operation="EXECUTE_ANYTHING"),True),
        ("expired-proof",lambda r:r["kernel_proof"].update(not_after="2026-01-01T00:00:00.500000Z"),True),
        ("wrong-proof-key",lambda r:r["kernel_proof"].update(key_id="TEST-OTHER"),True),
    ):
        r=deepcopy(vectors[0]["request"]);action(r);add(name,r,resign=resign)
    r=deepcopy(commit);r["prepared_request_digest"]="";add("empty-commit-link",r,resign=True)
    for name,action in (
        ("arbitrary-projection-digest",lambda r:r["kernel_proof"].update(pending_row_digest="sha256:"+"0"*64)),
        ("substituted-projection-scope",lambda r:r["kernel_proof"]["kernel_projection"].update(case_id="TEST-OTHER")),
        ("missing-projection",lambda r:r["kernel_proof"].pop("kernel_projection")),
    ):
        r=deepcopy(vectors[0]["request"]);action(r)
        if name=="substituted-projection-scope":r["kernel_proof"]["pending_row_digest"]=canonical_sha256(r["kernel_proof"]["kernel_projection"])
        add(name,seal(r,key))
    r=deepcopy(vectors[0]["request"]);raw=base64.urlsafe_b64decode(r["kernel_proof"]["signature"]+"==");s=int.from_bytes(raw[32:],"big")
    r["kernel_proof"]["signature"]=base64.urlsafe_b64encode(raw[:32]+(P256_ORDER-s).to_bytes(32,"big")).rstrip(b"=").decode();add("high-s-twin",r)
    for base,field,value,name in ((1,"subject_id","","empty-identity-subject"),(2,"subject_id","TEST-PERSON","nonempty-list-subject"),(3,"as_of_date","2024-01-01","facts-asof-forbidden"),(1,"as_of_date","2025-01-01","read-crossyear-date")):
        r=deepcopy(vectors[base]["request"]);r["payload"][field]=value;add(name,r,base=base,resign=True)
    for name,action in (
        ("response-correlation",lambda r:r.update(transaction_id="tx:v1:123e4567-e89b-42d3-a456-426614174099")),
        ("unknown-outcome",lambda r:r.update(outcome="SUCCESS")),
        ("malformed-read-items",lambda r:r["result"].update(items="invalid")),
        ("unknown-read-field",lambda r:r["result"].update(extra="invalid")),
        ("read-crosscase",lambda r:r["result"].update(case_id="TEST-OTHER")),
        ("inactive-subject",lambda r:r["result"]["items"][0].update(status="INACTIVE")),
        ("empty-identity-result",lambda r:r["result"].update(items=[])),
        ("oversize-result",lambda r:r["result"].update(items=r["result"]["items"]*65)),
    ):
        r=deepcopy(vectors[1]["response"]);action(r);add(name,r,"response",1)
    for name,raw in (("noncanonical",b" "+canonical_json_bytes(vectors[0]["request"])),("duplicate-field",b'{"contract":"x",'+canonical_json_bytes(vectors[0]["request"])[1:])):
        output.append({"name":name,"kind":"wire","base":"0","frame_hex":(struct.pack("<I",len(raw))+raw).hex()})
    # Oversize boundary is encoded as a deterministic repeated-byte recipe.
    output.append({"name":"oversize-frame","kind":"wire-repeat","base":"0","header_hex":struct.pack("<I",65533).hex(),"byte_hex":"20","count":"65533"})
    return output

def build_vectors():
    key=ec.derive_private_key(1,ec.SECP256R1()) # PUBLIC synthetic scalar; never a production key.
    from cryptography.hazmat.primitives import serialization
    vectors=[]
    for index,operation in enumerate(("REGISTER_IDENTITY","READ_CASE_IDENTITY","LIST_PARTIES","READ_FACTS")):
        request={"contract":CONTRACT,"message_type":"PREPARE_MUTATION" if index==0 else "READ_IDENTITY_STATE","transaction_id":f"tx:v1:123e4567-e89b-42d3-a456-42661417400{index}","request_digest":"", "deployment_id":"TEST-DEPLOYMENT","scope_kind":"CASE_YEAR","case_id":"TEST-CASE","tax_year":"2024","run_id":"TEST-RUN","task_id":"TEST-TASK","manifest_id":"TEST-MANIFEST","actor_instance_id":"TEST-ACTOR","role_id":"IDENTITY_ADMINISTRATION_AGENT","capability":OPERATION_CAPABILITIES[operation],"domain_operation":operation,"expected_epoch":"0","expected_head":"sha256:"+"0"*64,"authorization_references":["sha256:"+"a"*64],"expires_at":"2026-01-01T00:00:05.000000Z","prepared_request_digest":"","payload":{"request_id":"TEST-REGISTER","subject_id":"TEST-PERSON","identity_record_ref":"sha256:"+"b"*64,"evidence_refs":["sha256:"+"a"*64]} if index==0 else {"subject_id":"" if index==2 else "TEST-PERSON","as_of_date":"" if index==3 else "2024-06-01"},"kernel_proof":{"proof_version":"1","key_id":"TEST-KERNEL-KEY-1","algorithm":"ECDSA-P256-SHA256","pending_row_digest":"sha256:"+"c"*64,"authorization_state_version":"1","nonce":f"{index+1:064x}","issued_at":"2026-01-01T00:00:00.000000Z","not_after":"2026-01-01T00:00:05.000000Z","signature":""}}
        request=sign(request,key)
        items=[]
        if index==1:items=[{"person_id":"TEST-PERSON","status":"ACTIVE","preferred_display_name":"Synthetic Person","created_at":"2024-01-01T00:00:00.000000Z","updated_at":"2024-01-01T00:00:00.000000Z","schema_version":"1","lookup_attributes":[]}]
        if index==2:items=[{"binding_id":"TEST-PARTY","case_id":"TEST-CASE","subject_type":"PERSON","subject_id":"TEST-PERSON","role":"OTHER_DEPENDENT_OR_RELEVANT_PERSON","valid_from":"2024-01-01","valid_to_exclusive":"","evidence_ref":"sha256:"+"a"*64,"authorization_ref":"sha256:"+"a"*64}]
        if index==3:items=[{"request_id":"TEST-FACT","case_id":"TEST-CASE","tax_year":"2024","subject_type":"PERSON","subject_id":"TEST-PERSON","semantic_key":"synthetic.fact","fact_artifact_ref":"sha256:"+"b"*64,"declaration_artifact_ref":"sha256:"+"a"*64,"confirmation_ref":"sha256:"+"a"*64,"authorization_ref":"sha256:"+"a"*64,"valid_from":"2024-01-01","valid_to_exclusive":"2025-01-01","audit_lineage":["sha256:"+"a"*64],"revision":"1"}]
        result="" if index==0 else {k:request[k] for k in ("case_id","tax_year","run_id","domain_operation")}|{"items":items}
        response={"contract":CONTRACT,"message_type":request["message_type"],"transaction_id":request["transaction_id"],"request_digest":request["request_digest"],"outcome":"PREPARED" if index==0 else "READ_OK","response_digest":"","identity_epoch":"0","identity_head":"sha256:"+"0"*64,"staged_receipt_digest":"","witness_preimage_digest":"","signed_record_digest":"","denial_code":"","result":result}
        body=deepcopy(response);body.pop("response_digest");response["response_digest"]=canonical_sha256(body)
        vectors.append({"name":operation,"request":request,"pending_projection":pending_projection(request),"request_bytes_hex":canonical_json_bytes(request).hex(),"frame_hex":encode_frame(request).hex(),"request_preimage_hex":canonical_json_bytes(unsigned(request,True)).hex(),"signature_preimage_hex":signing_bytes(request).hex(),"response":response,"response_bytes_hex":canonical_json_bytes(response).hex(),"response_frame_hex":encode_frame(response).hex()})
    for source,label in ((1,"ENTITY"),(2,"EMPTY_PARTIES"),(3,"EMPTY_FACTS")):
        variant=deepcopy(vectors[source]);variant["name"]=label
        if source==1:
            item=variant["response"]["result"]["items"][0];item["entity_id"]=item.pop("person_id")
        else:variant["response"]["result"]["items"]=[]
        body=deepcopy(variant["response"]);body.pop("response_digest");variant["response"]["response_digest"]=canonical_sha256(body)
        variant["response_bytes_hex"]=canonical_json_bytes(variant["response"]).hex();variant["response_frame_hex"]=encode_frame(variant["response"]).hex()
        vectors.append(variant)
    commit=deepcopy(vectors[0]["request"]);commit["message_type"]="COMMIT_MUTATION";commit["prepared_request_digest"]=vectors[0]["request"]["request_digest"];commit["kernel_proof"]["nonce"]="f"*64;commit=sign(commit,key)
    commit_response=deepcopy(vectors[0]["response"]);commit_response.update(message_type="COMMIT_MUTATION",request_digest=commit["request_digest"],outcome="IDENTITY_COMMITTED",identity_epoch="1",identity_head="sha256:"+"1"*64,staged_receipt_digest="sha256:"+"2"*64,witness_preimage_digest="sha256:"+"3"*64)
    body=deepcopy(commit_response);body.pop("response_digest");commit_response["response_digest"]=canonical_sha256(body)
    renewed=deepcopy(vectors[0]["request"]);renewed["expires_at"]="2026-01-01T00:00:11.000000Z"
    renewed["kernel_proof"].update(issued_at="2026-01-01T00:00:06.000000Z",not_after=renewed["expires_at"],nonce="e"*64,authorization_state_version="2");renewed=sign(renewed,key)
    return {"vector_version":"F07-CONTRACT-1","test_private_scalar_hex":"0"*63+"1","public_key_pem":key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode(),"vectors":vectors,"negative_vectors":negative_vectors(vectors,commit),"commit":commit,"commit_pending_projection":pending_projection(commit),"commit_frame_hex":encode_frame(commit).hex(),"commit_signature_preimage_hex":signing_bytes(commit).hex(),"commit_response":commit_response,"commit_response_frame_hex":encode_frame(commit_response).hex(),"renewed_prepare":renewed,"renewed_prepare_frame_hex":encode_frame(renewed).hex()}
