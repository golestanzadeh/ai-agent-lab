"""Canonical Option A values used inside existing Kernel/Identity authorities.

No database ownership, orchestration, credentials, enrollment or I/O activation.
"""
from copy import deepcopy
from dataclasses import asdict,fields,dataclass
from datetime import datetime,timezone
from enum import Enum
import base64
import re

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec,utils
from agent_lab.case_registry import CaseRecord
from agent_lab.ipc_wire_primitives import canonical_json_bytes as C,canonical_sha256 as H

ORDER=0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
SHA=re.compile(r"sha256:[0-9a-f]{64}\Z")
DECIMAL=re.compile(r"0|[1-9][0-9]{0,19}\Z")
DOMAIN=b"AI-TAX-AGENT\0OWNER-IDENTITY-ENROLLMENT\0"
SCHEMA={
 "case_party_role":"authorization_ref binding_id case_id digest evidence_ref revision role schema_version subject_id subject_type valid_from valid_to_exclusive",
 "case_party_role_history":"binding_id correction_evidence_ref digest payload revision",
 "identity_history":"digest identity_id payload revision",
 "identity_record":"digest identity_id payload record_type revision schema_version",
 "legacy_identity_reference":"authorization_ref case_id created_at digest evidence_ref legacy_reference mapped_subject_id status",
 "relationship_fact_binding":"audit_lineage authorization_ref case_id confirmation_ref declaration_artifact_ref digest fact_artifact_ref fact_payload relationship_id request_id revision semantic_key tax_year valid_from valid_to_exclusive",
 "subject_fact_binding":"audit_lineage authorization_ref case_id confirmation_ref declaration_artifact_ref digest fact_artifact_ref fact_payload request_id revision schema_version semantic_key subject_id subject_type tax_year valid_from valid_to_exclusive",
 "subject_relationship":"authorization_ref case_id digest evidence_ref relationship_id relationship_type revision subject_a_id subject_b_id valid_from valid_to_exclusive",
 "successor_identity_allocation":"authorization_ref case_id created_at declaration_ref digest person_id request_id",
}
REGISTRY_FIELDS=set("case_id owner_type owner_id tax_period case_type assessment_mode lifecycle_status storage_scope_reference schema_version created_at updated_at last_run_id".split())
ENROLLMENT_FIELDS=set("contract deployment_id store_id enrollment_id schema_version domain_snapshot_digest enrollment_audit_count enrollment_audit_head case_manifest_digest backup_generation nonce issued_at not_before expires_at key_id algorithm signature bootstrap_task_id bootstrap_manifest_id bootstrap_run_id bootstrap_actor_instance_id bootstrap_role_id".split())


@dataclass(frozen=True)
class ContinuityKeys:
    owner_key_id: str
    owner_public_key: object
    kernel_key_id: str
    kernel_public_key: object

    def __post_init__(self):
        for key in (self.owner_public_key,self.kernel_public_key):
            if not isinstance(key,ec.EllipticCurvePublicKey) or not isinstance(key.curve,ec.SECP256R1):raise ValueError("pinned P-256 verification keys required")
        for name in (self.owner_key_id,self.kernel_key_id):text(name)


def exact(value,names):
    if not isinstance(value,dict) or set(value)!=set(names):raise ValueError("closed continuity fields mismatch")


def digest(value):
    if not isinstance(value,str) or not SHA.fullmatch(value):raise ValueError("invalid continuity digest")


def number(value):
    if not isinstance(value,str) or not DECIMAL.fullmatch(value):raise ValueError("invalid continuity decimal")
    return int(value)


def text(value):
    if not isinstance(value,str) or not 1<=len(value.encode())<=256:raise ValueError("invalid continuity identifier")


def utc(value):
    if not isinstance(value,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z",value):raise ValueError("invalid UTC timestamp")
    return datetime.strptime(value,"%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)


def cell(value):
    if value is None:return {"type":"null","value":""}
    if type(value) is int:return {"type":"integer","value":str(value)}
    if isinstance(value,str):return {"type":"text","value":value}
    if isinstance(value,bytes):return {"type":"blob","value":value.hex()}
    raise ValueError("unsupported snapshot cell")


def domain_snapshot(connection):
    tables=[]
    for table,names in sorted(SCHEMA.items()):
        columns=names.split()
        actual=sorted(row[1] for row in connection.execute("PRAGMA table_info("+table+")"))
        if actual!=columns:raise ValueError("unsupported domain snapshot schema")
        rows=[[cell(value) for value in row] for row in connection.execute("SELECT "+",".join(columns)+" FROM "+table)]
        rows.sort(key=lambda row:C({"row":row}))
        tables.append({"name":table,"columns":columns,"rows":rows})
    return {"profile":"identity-domain-snapshot/1","schema_version":"4","tables":tables}


def _registry_value(value):
    if isinstance(value,Enum):return value.value
    if isinstance(value,datetime):
        if value.tzinfo is None:raise ValueError("registry timestamp must be timezone aware")
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if value is None:return ""
    if type(value) is int:return str(value)
    if isinstance(value,str):return value
    if isinstance(value,dict):return {name:_registry_value(item) for name,item in value.items()}
    raise ValueError("unsupported registry value")


def case_manifest(records):
    if {f.name for f in fields(CaseRecord)}!=REGISTRY_FIELDS:raise ValueError("unsupported CaseRecord schema")
    result=[]
    for record in records:
        if not isinstance(record,CaseRecord):raise ValueError("authoritative CaseRecord required")
        result.append(_registry_value(asdict(record)))
    result.sort(key=lambda record:record["case_id"].encode("utf-16-be"))
    if len({record["case_id"] for record in result})!=len(result):raise ValueError("duplicate case identity")
    return {"profile":"identity-case-manifest/1","records":result}


def enrollment_preimage(artifact):
    exact(artifact,ENROLLMENT_FIELDS)
    unsigned=deepcopy(artifact);unsigned.pop("signature")
    return DOMAIN+C(unsigned)


def verify_enrollment(artifact,public_key,key_id,now):
    exact(artifact,ENROLLMENT_FIELDS)
    for value in artifact.values():text(value)
    if artifact["contract"]!="ai-tax-agent.identity-enrollment/1.0" or artifact["schema_version"]!="4" or artifact["key_id"]!=key_id or artifact["algorithm"]!="ECDSA-P256-SHA256":raise ValueError("enrollment authority/profile mismatch")
    if artifact["bootstrap_role_id"]!="OPERATIONS_INTEGRATION_AGENT":raise ValueError("invalid enrollment broker role")
    for name in ("domain_snapshot_digest","enrollment_audit_head","case_manifest_digest"):digest(artifact[name])
    number(artifact["enrollment_audit_count"]);number(artifact["backup_generation"])
    if not re.fullmatch(r"[0-9a-f]{64}",artifact["nonce"]):raise ValueError("invalid enrollment nonce")
    issued=utc(artifact["issued_at"]);start=utc(artifact["not_before"]);end=utc(artifact["expires_at"])
    if now.tzinfo is None or not issued<=start<=now<end or not 0<(end-issued).total_seconds()<=900:raise ValueError("enrollment expired/not effective")
    signature=artifact["signature"]
    if not re.fullmatch(r"[A-Za-z0-9_-]{86}",signature):raise ValueError("invalid enrollment signature encoding")
    raw=base64.urlsafe_b64decode(signature+"==")
    if base64.urlsafe_b64encode(raw).rstrip(b"=").decode()!=signature:raise ValueError("noncanonical enrollment signature")
    r,s=int.from_bytes(raw[:32],"big"),int.from_bytes(raw[32:],"big")
    if not 1<=r<ORDER or not 1<=s<=ORDER//2 or not isinstance(public_key.curve,ec.SECP256R1):raise ValueError("invalid enrollment signature range/key")
    public_key.verify(utils.encode_dss_signature(r,s),enrollment_preimage(artifact),ec.ECDSA(hashes.SHA256()))
    return H(artifact)


def genesis_preimage(artifact):
    exact(artifact,ENROLLMENT_FIELDS)
    return {"profile":"identity-genesis/1",**{name:artifact[name] for name in ("deployment_id","store_id","schema_version","enrollment_id","domain_snapshot_digest","enrollment_audit_count","enrollment_audit_head","case_manifest_digest","backup_generation")},"owner_authorization_digest":H(artifact)}


def successor_preimage(*,deployment_id,prior_epoch,prior_head,case_id,tax_year,transaction_id,domain_operation,mutation_content_digest,domain_result_digest):
    epoch=number(prior_epoch)
    if epoch>=10**20-1:raise ValueError("logical epoch exhausted")
    for value in (prior_head,mutation_content_digest,domain_result_digest):digest(value)
    for value in (deployment_id,case_id,transaction_id,domain_operation):text(value)
    number(tax_year)
    return {"profile":"identity-successor/1","deployment_id":deployment_id,"prior_epoch":prior_epoch,"prior_head":prior_head,"next_epoch":str(epoch+1),"case_id":case_id,"tax_year":tax_year,"transaction_id":transaction_id,"domain_operation":domain_operation,"mutation_content_digest":mutation_content_digest,"domain_result_digest":domain_result_digest}


def witness_commitment(*,deployment_id,logical_epoch,logical_head,audit_cut_count,audit_cut_head):
    text(deployment_id);number(logical_epoch);number(audit_cut_count);digest(logical_head);digest(audit_cut_head)
    return {"profile":"identity-witness-commitment/1","deployment_id":deployment_id,"logical_epoch":logical_epoch,"logical_head":logical_head,"audit_cut_count":audit_cut_count,"audit_cut_head":audit_cut_head}


def witness_slot(epoch,sequence,previous_record,*,restore=False):
    digest(previous_record)
    if epoch==sequence==0:
        if previous_record!="sha256:"+"0"*64 or restore:raise ValueError("invalid initial witness slot")
        return 1,1
    if type(epoch) is not int or type(sequence) is not int or epoch<1 or sequence<1:raise ValueError("invalid witness predecessor")
    if restore:
        if epoch>=10**20-1:raise ValueError("witness epoch exhausted")
        return epoch+1,1
    if sequence>=10**20-1:raise ValueError("witness sequence exhausted")
    return epoch,sequence+1


def checkpoint_identifiers(deployment_id,transaction_id,request_digest,response_digest):
    text(deployment_id);text(transaction_id);digest(request_digest);digest(response_digest)
    suffix=H({"deployment_id":deployment_id,"transaction_id":transaction_id,"request_digest":request_digest,"response_digest":response_digest})[7:]
    return "CP:"+suffix,"AUDIT:"+suffix.upper()


def domain_result(connection,operation,case_id,tax_year,object_id):
    """Exact committed-row projection; caller retains all authority checks."""
    number(tax_year);text(case_id);text(object_id)
    selected=[]
    def add(table,keys):
        columns=SCHEMA[table].split()
        pk=sorted((row[5],row[1]) for row in connection.execute("PRAGMA table_info("+table+")") if row[5])
        names=[name for _,name in pk]
        if set(keys)!=set(names):raise ValueError("invalid result primary key")
        row=connection.execute("SELECT "+",".join(columns)+" FROM "+table+" WHERE "+" AND ".join(name+"=?" for name in names),[keys[name] for name in names]).fetchone()
        if row is None:raise ValueError("committed result row unavailable")
        values=dict(zip(columns,row))
        if "case_id" in values and values["case_id"]!=case_id:raise ValueError("result case mismatch")
        if "tax_year" in values and str(values["tax_year"])!=tax_year:raise ValueError("result year mismatch")
        projection={"profile":"identity-domain-row/1","table":table,"columns":columns,"cells":[cell(value) for value in row]}
        selected.append({"table":table,"primary_key":[cell(keys[name]) for name in names],"row_digest":H(projection)})
        return values
    if operation in {"REGISTER_IDENTITY","UPDATE_IDENTITY_STATUS"}:
        row=add("identity_record",{"identity_id":object_id});add("identity_history",{"identity_id":object_id,"revision":row["revision"]})
    elif operation in {"BIND_PARTY","CORRECT_PARTY_ROLE"}:
        row=add("case_party_role",{"binding_id":object_id})
        if operation=="CORRECT_PARTY_ROLE":
            if row["revision"]<2:raise ValueError("missing correction revision")
            for revision in (row["revision"]-1,row["revision"]):add("case_party_role_history",{"binding_id":object_id,"revision":revision})
    elif operation=="BIND_FACT":add("subject_fact_binding",{"request_id":object_id})
    else:raise ValueError("unsupported mutation result operation")
    selected.sort(key=lambda row:(row["table"].encode("utf-16-be"),C({"key":row["primary_key"]})))
    return {"profile":"identity-domain-result/1","case_id":case_id,"tax_year":tax_year,"domain_operation":operation,"rows":selected}
