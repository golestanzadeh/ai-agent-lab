"""Identity-owned atomic mutation metadata and crash-safe anchor coupling."""
from copy import deepcopy
from dataclasses import asdict
from datetime import date, datetime, timezone
import hmac
import json
import time
from datetime import timedelta

from agent_lab.identity_logical_continuity import H, domain_snapshot, domain_result, successor_preimage
from agent_lab.ipc_operational_read import CONTROL_SCOPE, SNAPSHOT_FIELDS, validate_request, validate_response, read_projection
from agent_lab.f07_commit_witness import commit_witness_material
from agent_lab.c09_custodian_operational import pack
from agent_lab.ipc_wire_primitives import canonical_json_bytes as C
from agent_lab.identity_mutation_source import resolve


def load(owner, key):
    row = owner._db.execute("SELECT payload_json,digest FROM identity_mutation_record WHERE key=?", (key,)).fetchone()
    if row is None:
        return None
    payload = json.loads(row[0])
    if not hmac.compare_digest(owner._mac(payload), row[1]):
        raise ValueError("mutation row integrity failure")
    return payload


def save(owner, key, payload, *, audit=True):
    digest = owner._mac(payload)
    owner._db.execute("INSERT INTO identity_mutation_record VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET payload_json=excluded.payload_json,digest=excluded.digest",
                      (key, json.dumps(payload, sort_keys=True, separators=(",", ":")), digest))
    if audit:
        owner._append_audit("IDENTITY_MUTATION_RECORD", None, key, {"key": key, "payload_digest": digest})


def verify(owner):
    expected = {}
    for row in owner._db.execute("SELECT event_payload FROM identity_audit ORDER BY event_id"):
        event = json.loads(row[0])
        if event["action"] == "IDENTITY_MUTATION_RECORD":
            expected[event["subject_id"]] = event["details_digest"]
    actual = {}
    for row in owner._db.execute("SELECT key FROM identity_mutation_record"):
        key = row[0]
        payload = load(owner, key)
        if key != "ANCHOR":
            actual[key] = owner._mac({"key": key, "payload_digest": owner._mac(payload)})
    if expected != actual:
        raise ValueError("mutation metadata deletion or substitution")
    for key in actual:
        if not key.startswith(("TX:","AUTH:","AUTHREF:","NONCE:")):
            raise ValueError("unknown mutation metadata")
        record = load(owner,key)
        if not key.startswith("TX:") and load(owner,"TX:"+record["transaction_id"]) is None:
            raise ValueError("orphan mutation metadata")
        if key.startswith("NONCE:"):
            request=record["request"]
            if key != "NONCE:"+request["kernel_proof"]["nonce"] or request["transaction_id"] != record["transaction_id"]:
                raise ValueError("mutation proof index substitution")
            reply=record["response"]
            if reply["request_digest"]!=request["request_digest"] or H({k:v for k,v in reply.items() if k!="response_digest"})!=reply["response_digest"]:
                raise ValueError("stored mutation response corruption")
        if key.startswith("TX:"):
            tx = load(owner, key)
            auth = load(owner, "AUTH:" + tx["authorization_event_id"])
            binding = load(owner,"AUTHREF:"+tx["prepare_request"]["authorization_references"][0])
            if binding != dict(transaction_id=tx["transaction_id"],authorization_event_id=tx["authorization_event_id"]):
                raise ValueError("authorization reference lineage missing")
            if auth is None or auth["transaction_id"] != tx["transaction_id"]:
                raise ValueError("mutation authorization missing")
            if tx["state"] in ("IDENTITY_COMMITTED", "COMMITTED_FINAL"):
                if auth["state"] != "CONSUMED":
                    raise ValueError("committed authorization not consumed")
                response = tx["commit_response"]
                from agent_lab.f07_commit_witness import validate_commit_material
                validate_commit_material(response["result"], original_commit=tx["commit_request"],
                                         response=response, store_id=tx["store_id"],
                                         backup_generation=tx["backup_generation"])
            elif auth["state"] != ("RELEASED" if tx["state"] == "ABORTED" else "RESERVED"):
                raise ValueError("reservation state mismatch")


def recover_anchor(owner, old_anchor):
    pending = load(owner, "ANCHOR")
    if pending is None or pending["previous"] != old_anchor:
        return False
    count, head = owner._audit_head()
    if pending["next"] != owner._anchor_payload(count, head):
        return False
    owner._verify_data_integrity()
    owner._verify_logical_integrity()
    verify(owner)
    owner._write_anchor(count, head)
    return True


def stage_anchor(owner, old_anchor):
    count, head = owner._audit_head()
    save(owner, "ANCHOR", {"previous": old_anchor, "next": owner._anchor_payload(count, head)}, audit=False)


def stable(request):
    value = deepcopy(request)
    for key in ("message_type", "request_digest", "kernel_proof", "expires_at", "prepared_request_digest"):
        value.pop(key)
    return H(value)


def scope(request):
    return {key: request[key] for key in CONTROL_SCOPE}


def response(request, state, epoch, head, count, audit_head):
    reply = {key: request[key] for key in ("contract", "message_type", "transaction_id", "request_digest")}
    reply.update(outcome=state, identity_epoch=str(epoch), identity_head=head,
                 identity_audit_count=str(count), identity_audit_head="sha256:"+audit_head,
                 staged_receipt_digest="", witness_preimage_digest="", signed_record_digest="",
                 denial_code="", result="")
    return reply


def protected_json(raw):
    from agent_lab.c09_witness_protocol import _reject_duplicate_pairs
    from agent_lab.identity_persistence import _canonical
    from agent_lab.c09_witness_protocol import WitnessError
    try:
        value=json.loads(raw,object_pairs_hook=_reject_duplicate_pairs)
    except WitnessError as exc:
        raise ValueError("duplicate protected domain field") from exc
    if _canonical(value).encode("utf-8")!=raw:
        raise ValueError("noncanonical protected domain DTO")
    return value


def decode_record(data):
    from agent_lab.person_entity_registry import PersonRecord, EntityRecord, RegistryStatus, PersonEntityRegistry
    names = {"identity_id","record_type","status","name","created_at","updated_at","lookup_attributes","record_schema_version"}
    if set(data) != names:
        raise ValueError("closed protected Identity record required")
    if (type(data["record_schema_version"]) is not int or data["record_schema_version"]!=2
            or type(data["lookup_attributes"]) is not list or len(data["lookup_attributes"])>64
            or any(type(pair) is not list or len(pair)!=2 or any(type(value) is not str or len(value.encode())>256 for value in pair) for pair in data["lookup_attributes"])
            or data["name"] is not None and (type(data["name"]) is not str or len(data["name"].encode())>256)):
        raise ValueError("invalid protected record types")
    from agent_lab.ipc_operational_read import text
    for key in ("identity_id","record_type","status","created_at","updated_at"):
        text(data[key])
    cls = PersonRecord if data["record_type"] == "PERSON" else EntityRecord if data["record_type"] == "ENTITY" else None
    if cls is None:
        raise ValueError("unknown record type")
    record = cls(data["identity_id"], RegistryStatus(data["status"]), data["name"],
                 datetime.fromisoformat(data["created_at"]), datetime.fromisoformat(data["updated_at"]),
                 int(data["record_schema_version"]), tuple(tuple(v) for v in data["lookup_attributes"]))
    registry = PersonEntityRegistry()
    (registry.register_person if cls is PersonRecord else registry.register_entity)(record)
    return record


def role_reference(refs, evidence_refs):
    candidates=[reference for reference in evidence_refs if refs[reference].kind=="ROLE_EVIDENCE"]
    if len(candidates)!=1:
        raise PermissionError("one exact role evidence reference required")
    return candidates[0]


def apply_domain(owner, request, refs):
    """Only the existing accepted domain APIs may change Identity rows."""
    from agent_lab.identity_persistence import CasePartyRole
    from agent_lab.person_entity_registry import RegistryStatus
    p = request["payload"]
    op = request["domain_operation"]
    auth = request["authorization_references"][0]
    case = request["case_id"]
    if "owner_input_digest" in p:
        if op in {"REGISTER_IDENTITY","CORRECT_PERSON"}:
            raw_record=protected_json(refs[p["identity_record_ref"]].observed.content)
            attributes=dict(raw_record["lookup_attributes"])
            allowed={"first_name","last_name","birth_date","tax_id"}
            if (len(attributes)!=len(raw_record["lookup_attributes"]) or set(attributes)-allowed or
                    not {"first_name","last_name","birth_date"}<=set(attributes) or
                    raw_record["name"]!=attributes["first_name"]+" "+attributes["last_name"] or
                    H(attributes)!=p["owner_input_digest"]):
                raise PermissionError("protected person differs from confirmed UI input")
        elif op=="BIND_PARTY" and H({"role":p["party_role"]})!=p["owner_input_digest"]:
            raise PermissionError("protected role differs from confirmed UI input")
    if op == "REGISTER_IDENTITY":
        raw = refs[p["identity_record_ref"]].observed.content
        record = decode_record(protected_json(raw))
        if owner._identity_payload(record)["identity_id"] != p["subject_id"]:
            raise PermissionError("protected subject mismatch")
        owner.register_identity(case_id=case, record=record, authorization_ref=auth)
        return p["subject_id"]
    if op == "CORRECT_PERSON":
        record=decode_record(protected_json(refs[p["identity_record_ref"]].observed.content))
        if record.person_id!=p["subject_id"]:raise PermissionError("correction subject mismatch")
        owner.correct_person(case_id=case,record=record,expected_record_digest=p["expected_record_digest"],
                             evidence_ref=p["identity_record_ref"],authorization_ref=auth)
        return p["subject_id"]
    if op == "UPDATE_IDENTITY_STATUS":
        current = owner._load_identity(p["subject_id"])
        if current is None or current.status.value != p["from_status"]:
            raise ValueError("status predecessor mismatch")
        date.fromisoformat(p["effective_date"])
        owner.update_identity_status(case_id=case,identity_id=p["subject_id"],status=RegistryStatus(p["to_status"]),authorization_ref=auth)
        return p["subject_id"]
    if op == "BIND_PARTY":
        record = owner._load_identity(p["subject_id"], require_active=True)
        if record is None:
            raise PermissionError("subject unavailable")
        binding = CasePartyRole(p["request_id"],case,record.record_type.value,p["subject_id"],p["party_role"],
                                date.fromisoformat(p["valid_from"]),
                                date.fromisoformat(p["valid_to_exclusive"]) if p["valid_to_exclusive"] else None,
                                role_reference(refs,p["evidence_refs"]),auth)
        owner.bind_party(binding)
        return p["request_id"]
    if op == "CORRECT_PARTY_ROLE":
        replacement = protected_json(refs[p["replacement_binding_ref"]].observed.content)
        prior = protected_json(refs[p["prior_binding_ref"]].observed.content)
        row = owner._db.execute("SELECT * FROM case_party_role WHERE binding_id=?",(prior["binding_id"],)).fetchone()
        fields={"binding_id","case_id","subject_type","subject_id","role","valid_from","valid_to_exclusive","evidence_ref","authorization_ref"}
        if set(prior)!=fields or set(replacement)!=fields or row is None or prior!={key:row[key] for key in fields}:
            raise PermissionError("prior role scope mismatch")
        expected={**prior,"valid_to_exclusive":p["effective_date"],"evidence_ref":p["replacement_binding_ref"],"authorization_ref":auth}
        # The protected replacement DTO cannot contain a hash of itself.
        # Its evidence_ref retains the prior reference; the signed outer
        # replacement_binding_ref is the exact correction source argument.
        expected["evidence_ref"]=prior["evidence_ref"]
        if replacement!=expected:
            raise PermissionError("replacement role scope mismatch")
        owner.correct_party_role(case_id=case,binding_id=prior["binding_id"],valid_to_exclusive=date.fromisoformat(p["effective_date"]),
                                 correction_evidence_ref=p["replacement_binding_ref"],authorization_ref=auth)
        return prior["binding_id"]
    if op == "BIND_FACT":
        body = protected_json(refs[p["fact_envelope_ref"]].observed.content)
        if set(body)!={"fact_payload","declaration_artifact_ref","confirmation_ref"}:
            raise ValueError("closed protected fact arguments required")
        fact = owner._restore_fact(body["fact_payload"])
        if owner._fact_payload(fact)!=body["fact_payload"]:
            raise ValueError("closed protected fact payload required")
        semantic=refs[p["fact_envelope_ref"]].accepted.scope.semantic_key
        if semantic!=fact.semantic_key or any(artifact.accepted.scope.semantic_key!=semantic for artifact in refs.values() if artifact.kind!="ROLE_EVIDENCE"):
            raise PermissionError("fact semantic scope mismatch")
        owner.bind_fact(request_id=p["request_id"],case_id=case,tax_year=int(request["tax_year"]),subject_id=p["subject_id"],fact=fact,
                        declaration_artifact_ref=body["declaration_artifact_ref"],confirmation_ref=body["confirmation_ref"],
                        valid_from=date.fromisoformat(p["valid_from"]),valid_to_exclusive=date.fromisoformat(p["valid_to_exclusive"]),authorization_ref=auth)
        return p["request_id"]
    raise PermissionError("unsupported mutation operation")


def material_identity(owner, bundle):
    values = []
    for artifact in bundle.artifacts:
        values.append(dict(reference=artifact.reference, kind=artifact.kind,
                           revision=asdict(artifact.accepted.revision), digest=artifact.accepted.content_digest,
                           scope={key:str(value) for key,value in asdict(artifact.accepted.scope).items()}))
    return H(dict(subject=bundle.subject_id, authorization=bundle.authorization_event_id,
                           artifacts=sorted(values,key=lambda value:value["reference"])))


def evidence_check(refs, kind, reference, case, year, subject, start, end):
    artifact = refs.get(reference)
    if artifact is None or artifact.kind != kind:
        raise PermissionError("protected evidence kind mismatch")
    scope = artifact.accepted.scope
    if ((scope.case_id,scope.tax_year,scope.subject_id) != (case,year,subject)
            or scope.valid_from > start or scope.valid_to_exclusive < end):
        raise PermissionError("protected evidence scope mismatch")


def preview(owner, request, refs, mutation_time):
    previous_resolver = owner._resolve_evidence
    owner._resolve_evidence = lambda *args:evidence_check(refs,*args)
    owner._protocol_transaction = True
    owner._protocol_context = request
    owner._mutation_time = mutation_time
    try:
        object_id = apply_domain(owner,request,refs)
        result = domain_result(owner._db,request["domain_operation"],request["case_id"],request["tax_year"],object_id)
        return object_id,H(result)
    finally:
        owner._resolve_evidence = previous_resolver
        owner._protocol_transaction = False
        owner._protocol_context = None
        owner._mutation_time = None


def checkpoint(tx, reply):
    return dict(scope=tx["scope"],prepare_digest=tx["prepare_digest"],
                snapshot={key:reply[key] for key in SNAPSHOT_FIELDS},
                finalize_payload=tx.get("finalize_payload"))


def execute(owner, request, *, allowed_case_ids, now=None):
    """Inactive explicit entry point, serialized by the Identity authority lock."""
    started=time.monotonic()
    now = now or datetime.now(timezone.utc)
    if now.utcoffset() is None or owner._continuity_keys is None:
        raise PermissionError("pinned Kernel authority and aware time required")
    keys = owner._continuity_keys
    local = owner._logical_row()
    if local is None:
        raise PermissionError("accepted Identity enrollment required")
    names = "deployment_id case_id tax_year run_id task_id manifest_id actor_instance_id role_id".split()
    validate_request(request,keys.kernel_public_key,expected_scope={key:request[key] for key in names},
                     now=now.astimezone(timezone.utc).replace(tzinfo=None),expected_key_id=keys.kernel_key_id,
                     expected_contract="oi0002.kernel-identity-c09/1.1",mutation_runtime=True)
    case = owner._cases.get(request["case_id"])
    if (type(allowed_case_ids) is not frozenset or request["case_id"] not in allowed_case_ids
            or case is None or str(case.tax_period.year) != request["tax_year"]
            or local["deployment_id"] != request["deployment_id"] or len(request["authorization_references"]) != 1):
        raise PermissionError("configured exact case/year scope required")
    owner._verify_audit_continuity()
    owner._verify_data_integrity()
    owner._verify_logical_integrity()
    message = request["message_type"]
    bundle = refs = None
    if message in {"PREPARE_MUTATION","COMMIT_MUTATION"}:
        existing = load(owner,"TX:"+request["transaction_id"])
        if existing is None or existing["state"] == "PREPARED":
            bundle,refs = resolve(owner._mutation_source,request,case,now)
    old_anchor = owner._anchor_payload(*owner._audit_head())
    owner._db.execute("BEGIN IMMEDIATE")
    try:
        current_time=now+timedelta(seconds=time.monotonic()-started)
        from agent_lab.identity_logical_continuity import utc
        if current_time>=utc(request["kernel_proof"]["not_after"]):
            raise PermissionError("proof expired during protected resolution")
        if refs is not None:
            for artifact in refs.values():
                if artifact.accepted.expires_at<=current_time or artifact.accepted.revoked_at is not None:
                    raise PermissionError("evidence lease expired before transaction")
        local = owner._logical_row()
        tx = load(owner,"TX:"+request["transaction_id"])
        if owner._db.execute("SELECT 1 FROM identity_protocol_attempt WHERE transaction_id=?",(request["transaction_id"],)).fetchone():
            raise PermissionError("read/mutation transaction namespace conflict")
        nonce_key = "NONCE:"+request["kernel_proof"]["nonce"]
        prior_nonce = load(owner,nonce_key)
        if prior_nonce is not None or owner._db.execute("SELECT 1 FROM identity_protocol_attempt WHERE nonce=?",(request["kernel_proof"]["nonce"],)).fetchone():
            raise PermissionError("proof nonce already consumed")
        projection = request["kernel_proof"]["kernel_projection"]
        count = int(projection["witnessed_audit_count"])
        prefix = owner._db.execute("SELECT event_mac FROM identity_audit WHERE event_id=?",(count,)).fetchone()
        if (count and prefix is None) or projection["witnessed_audit_head"] != "sha256:"+(prefix[0] if prefix else "0"*64):
            raise PermissionError("unverified Witness audit prefix")
        if tx is not None and tx["scope"] != scope(request):
            raise PermissionError("transaction scope substitution")
        if message == "PREPARE_MUTATION":
            if tx is not None:
                if tx["stable_digest"] != stable(request) or tx["material_identity"] != material_identity(owner,bundle):
                    raise PermissionError("PREPARE content substitution")
                if tx["state"] != "PREPARED":
                    raise PermissionError("prepared transaction already completed")
                reply = deepcopy(tx["prepare_response"])
                reply.update(request_digest=request["request_digest"])
                reply.pop("response_digest",None)
                reply["response_digest"] = H(reply)
                save(owner,nonce_key,dict(transaction_id=request["transaction_id"],request=request,response=reply))
                stage_anchor(owner,old_anchor)
                owner._db.commit()
                owner._sync_anchor()
                return reply
            if (request["expected_epoch"],request["expected_head"]) != (str(local["epoch"]),local["head"]):
                raise PermissionError("stale logical continuity")
            auth_key = "AUTH:"+bundle.authorization_event_id
            if load(owner,auth_key) is not None or load(owner,"AUTHREF:"+request["authorization_references"][0]) is not None:
                raise PermissionError("authorization already reserved or consumed")
            # The dry-run uses the very same domain APIs and rolls back every
            # domain/audit effect before persisting the reservation.
            owner._db.execute("SAVEPOINT mutation_preview")
            try:
                object_id,result_digest = preview(owner,request,refs,now)
            finally:
                owner._db.execute("ROLLBACK TO mutation_preview")
                owner._db.execute("RELEASE mutation_preview")
            tx = dict(state="PREPARED",transaction_id=request["transaction_id"],scope=scope(request),
                      prepare_digest=request["request_digest"],prepare_request=request,stable_digest=stable(request),
                      material_identity=material_identity(owner,bundle),authorization_event_id=bundle.authorization_event_id,
                      mutation_time=now.isoformat(),object_id=object_id,domain_result_digest=result_digest,
                      store_id=local["store_id"],backup_generation=local["backup_generation"])
            tx["resolved_plan"]=dict(profile="identity-resolved-plan/1",deployment_id=request["deployment_id"],
                store_id=local["store_id"],transaction_id=request["transaction_id"],prepared_request_digest=request["request_digest"],
                stage_content_digest=projection["stage_content_digest"],case_id=request["case_id"],tax_year=request["tax_year"],
                subject_id=bundle.subject_id,operation=request["domain_operation"],source_bindings=sorted(refs),
                authorization_event_id=bundle.authorization_event_id,domain_arguments_digest=tx["material_identity"])
            tx["source_provenance"]=[dict(reference=artifact.reference,kind=artifact.kind,
                revision=asdict(artifact.accepted.revision),content_digest=artifact.accepted.content_digest,
                scope={key:str(value) for key,value in asdict(artifact.accepted.scope).items()},
                expires_at=artifact.accepted.expires_at.isoformat()) for artifact in bundle.artifacts]
            save(owner,auth_key,dict(transaction_id=request["transaction_id"],state="RESERVED"))
            save(owner,"AUTHREF:"+request["authorization_references"][0],dict(transaction_id=request["transaction_id"],authorization_event_id=bundle.authorization_event_id))
        elif tx is None:
            raise PermissionError("unknown transaction")
        elif message == "COMMIT_MUTATION":
            if tx["state"] in {"IDENTITY_COMMITTED","COMMITTED_FINAL"}:
                original = tx["commit_request"]
                before = original["kernel_proof"]["kernel_projection"]
                if (stable(request) != tx["stable_digest"] or request["prepared_request_digest"] != tx["prepare_digest"]
                        or any(projection[key] != before[key] for key in ("mutation_witness_slot","kernel_pending_head","projected_epoch","projected_head","stage_content_digest"))):
                    raise PermissionError("completed COMMIT substitution")
                reply = deepcopy(tx["commit_response"])
                reply.update(request_digest=request["request_digest"])
                reply.pop("response_digest",None)
                reply["response_digest"] = H(reply)
                validate_response(reply,request,mutation_material_context=dict(original_commit=original,store_id=tx["store_id"],backup_generation=tx["backup_generation"]))
                save(owner,nonce_key,dict(transaction_id=request["transaction_id"],request=request,response=reply))
                stage_anchor(owner,old_anchor)
                owner._db.commit()
                owner._sync_anchor()
                return reply
            if tx["state"] != "PREPARED":
                raise PermissionError("aborted transaction cannot commit")
            if (request["prepared_request_digest"] != tx["prepare_digest"] or stable(request) != tx["stable_digest"]
                    or material_identity(owner,bundle) != tx["material_identity"]
                    or bundle.authorization_event_id != tx["authorization_event_id"]):
                raise PermissionError("prepared mutation substitution")
            if (request["expected_epoch"],request["expected_head"]) != (str(local["epoch"]),local["head"]):
                raise PermissionError("stale logical continuity")
            auth = load(owner,"AUTH:"+tx["authorization_event_id"])
            if auth != dict(transaction_id=request["transaction_id"],state="RESERVED"):
                raise PermissionError("authorization reservation unavailable")
            object_id,result_digest = preview(owner,request,refs,datetime.fromisoformat(tx["mutation_time"]))
            if (object_id,result_digest) != (tx["object_id"],tx["domain_result_digest"]):
                raise PermissionError("prepared domain result conflict")
            successor = successor_preimage(deployment_id=request["deployment_id"],prior_epoch=request["expected_epoch"],
                prior_head=request["expected_head"],case_id=request["case_id"],tax_year=request["tax_year"],
                transaction_id=request["transaction_id"],domain_operation=request["domain_operation"],
                mutation_content_digest=tx["stable_digest"],domain_result_digest=result_digest)
            if (projection["projected_epoch"],projection["projected_head"]) != (successor["next_epoch"],H(successor)):
                raise PermissionError("Kernel successor substitution")
            local.update(epoch=int(successor["next_epoch"]),head=H(successor),domain_snapshot_digest=H(domain_snapshot(owner._db)))
            owner._db.execute("UPDATE identity_logical_state SET epoch=?,head=?,payload_json=?,digest=? WHERE singleton=1",
                              (local["epoch"],local["head"],json.dumps(local,sort_keys=True,separators=(",",":")),owner._mac(local)))
            save(owner,"AUTH:"+tx["authorization_event_id"],dict(transaction_id=request["transaction_id"],state="CONSUMED"))
            tx.update(state="IDENTITY_COMMITTED",commit_request=request)
        elif message == "ABORT_PREPARED":
            if tx["state"] == "PREPARED":
                tx["state"] = "ABORTED"
                save(owner,"AUTH:"+tx["authorization_event_id"],dict(transaction_id=request["transaction_id"],state="RELEASED"))
            elif tx["state"] != "ABORTED":
                raise PermissionError("committed transaction cannot abort")
        elif message == "FINALIZE_MUTATION":
            if tx["state"] not in {"IDENTITY_COMMITTED","COMMITTED_FINAL"}:
                raise PermissionError("transaction not committed")
            p = request["payload"]
            receipt = tx["commit_response"]["result"]["receipt"]
            if (p["staged_receipt_digest"] != H(receipt) or p["witness_preimage_digest"] != receipt["witness_preimage_digest"]
                    or p["witness_object_key"] != receipt["witness_slot"]["object_key"]):
                raise PermissionError("finality receipt substitution")
            if tx["state"] == "COMMITTED_FINAL" and tx["finalize_payload"] != p:
                raise PermissionError("finality evidence substitution")
            tx.update(state="COMMITTED_FINAL",finalize_payload=p,finalize_request=request)
        if message in {"GET_TRANSACTION","ABORT_PREPARED"} and request["payload"]["original_request_digest"] != tx["prepare_digest"]:
            raise PermissionError("original PREPARE mismatch")
        # Audit the stage before capturing the receipt cut. The receipt cannot
        # include its own digest in that cut.
        owner._append_audit("IDENTITY_MUTATION_STAGE",request["case_id"],"REDACTED",
                            dict(transaction_id=request["transaction_id"],request_digest=request["request_digest"],state=tx["state"]))
        count,head = owner._audit_head()
        reply = response(request,tx["state"],local["epoch"],local["head"],count,head)
        if message == "GET_TRANSACTION" and tx["state"] in {"PREPARED","ABORTED"}:
            saved=tx["prepare_response"] if tx["state"]=="PREPARED" else tx["abort_response"]
            for key in SNAPSHOT_FIELDS:
                reply[key]=saved[key]
        if tx["state"] == "PREPARED":
            original = tx["prepare_request"]
            successor = successor_preimage(deployment_id=original["deployment_id"],prior_epoch=original["expected_epoch"],prior_head=original["expected_head"],
                case_id=original["case_id"],tax_year=original["tax_year"],transaction_id=original["transaction_id"],domain_operation=original["domain_operation"],
                mutation_content_digest=tx["stable_digest"],domain_result_digest=tx["domain_result_digest"])
            reply.update(identity_epoch=successor["next_epoch"],identity_head=H(successor))
            if message == "PREPARE_MUTATION":
                tx["prepare_response"] = deepcopy(reply)
        if message == "COMMIT_MUTATION":
            receipt,unsigned = commit_witness_material(request,store_id=local["store_id"],backup_generation=local["backup_generation"],
                audit_count=str(count),audit_head="sha256:"+head,result_digest=tx["domain_result_digest"])
            reply.update(staged_receipt_digest=H(receipt),witness_preimage_digest=receipt["witness_preimage_digest"],
                         result=dict(profile="identity-mutation-commit-material/1",receipt=receipt,unsigned_record_bytes=pack(unsigned)))
            tx["commit_response"] = deepcopy(reply)
        elif tx["state"] in {"IDENTITY_COMMITTED","COMMITTED_FINAL"}:
            saved = tx["commit_response"]
            for key in SNAPSHOT_FIELDS-{"outcome","signed_record_digest"}:
                reply[key] = saved[key]
            if tx["state"] == "IDENTITY_COMMITTED":
                reply["result"] = saved["result"]
            else:
                reply["signed_record_digest"] = tx["finalize_payload"]["signed_record_digest"]
        reply["response_digest"] = H(reply)
        if message == "ABORT_PREPARED" and "abort_response" not in tx:
            tx["abort_response"] = deepcopy(reply)
        context = dict(original_commit=tx["commit_request"],store_id=tx["store_id"],backup_generation=tx["backup_generation"]) if tx.get("commit_request") else None
        validate_response(reply,request,transaction_checkpoint=checkpoint(tx,reply) if message in {"FINALIZE_MUTATION","GET_TRANSACTION","ABORT_PREPARED"} else None,
                          mutation_material_context=context if reply["outcome"] == "IDENTITY_COMMITTED" else None)
        save(owner,"TX:"+request["transaction_id"],tx)
        save(owner,nonce_key,dict(transaction_id=request["transaction_id"],request=request,response=reply))
        stage_anchor(owner,old_anchor)
        if owner._fault:owner._fault("IDENTITY_MUTATION:BEFORE_COMMIT")
        owner._db.commit()
        if owner._fault:owner._fault("IDENTITY_MUTATION:AFTER_COMMIT")
        owner._sync_anchor()
        if owner._fault:owner._fault("IDENTITY_MUTATION:AFTER_ANCHOR")
        return reply
    except BaseException:
        if owner._db.in_transaction:owner._db.rollback()
        raise
