"""Versioned implementation of the existing Custodian role; no key provisioning.

The HMAC key stays in this role. Kernel/GCS receive authenticated bytes only.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import sqlite3
from datetime import datetime,timezone
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec,utils
from agent_lab.ipc_wire_primitives import canonical_json_bytes as C,canonical_sha256 as H
from agent_lab.ipc_operational_read import unsigned,signing_bytes
from agent_lab.identity_logical_continuity import ORDER,checkpoint_identifiers,witness_commitment
from agent_lab.c09_witness_protocol import WitnessRecord,canonical_bytes,digest,_FIELDS,_reject_duplicate_pairs

CONTRACT="ai-tax-agent.c09-custodian/1.1"
BASE=set("contract operation deployment_id transaction_id request_digest nonce issued_at expires_at kernel_proof".split())
AUTH=BASE|set("unsigned_record_bytes unsigned_record_digest staged_receipt_bytes staged_receipt_digest identity_request_digest expected_epoch expected_sequence previous_commitment kernel_pending_head identity_new_head backup_generation witness_object_key".split())
VERIFY=BASE|set("authenticated_record_bytes witness_object_key witness_generation expected_record_digest expected_preimage_digest expected_previous_commitment".split())
REPLY=set("contract operation deployment_id transaction_id request_digest nonce outcome key_id algorithm authenticated_record_bytes signed_record_digest denial_code".split())
RECEIPT=set("profile deployment_id store_id checkpoint_id transaction_id request_digest response_digest stage_content_digest response_outcome logical_epoch logical_head audit_cut_count audit_cut_head backup_generation".split())


def pack(raw):return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def unpack(value,maximum=16384):
    if not isinstance(value,str) or len(value)>maximum*2 or not re.fullmatch(r"[A-Za-z0-9_-]+",value):raise ValueError("invalid canonical bytes encoding")
    raw=base64.urlsafe_b64decode(value+"="*((-len(value))%4))
    if len(raw)>maximum or pack(raw)!=value:raise ValueError("noncanonical bytes")
    return raw


def exact(value,fields):
    if not isinstance(value,dict) or set(value)!=fields:raise ValueError("closed Custodian fields mismatch")


def public_unsigned(raw):
    if not isinstance(raw,bytes) or len(raw)>4096:raise ValueError("unsigned witness bound")
    value=json.loads(raw.decode(),object_pairs_hook=_reject_duplicate_pairs)
    exact(value,_FIELDS-{"mac"})
    if canonical_bytes(value)!=raw:raise ValueError("noncanonical unsigned Witness bytes")
    record=WitnessRecord.from_public_bytes(canonical_bytes({**value,"mac":"hmac-sha256:"+"0"*64}))
    return record


class OperationalCustodianRuntime:
    def __init__(self,*,deployment_id,key_id,protected_key,kernel_key_id,kernel_public_key,replay_db_path):
        if not isinstance(protected_key,bytes) or len(protected_key)<32:raise ValueError("protected Custodian key unavailable")
        if not isinstance(kernel_public_key,ec.EllipticCurvePublicKey) or not isinstance(kernel_public_key.curve,ec.SECP256R1):raise ValueError("pinned Kernel key unavailable")
        for value in (deployment_id,key_id,kernel_key_id):
            if not isinstance(value,str) or not 1<=len(value.encode())<=256:raise ValueError("pinned Custodian metadata required")
        self._deployment=deployment_id;self._key_id=key_id;self._key=protected_key
        self._kernel_id=kernel_key_id;self._public=kernel_public_key;self._running=False
        path=Path(replay_db_path).resolve()
        if not path.is_file():raise ValueError("preprovisioned existing Custodian store required")
        self._anchor=path.with_suffix(path.suffix+".custodian11-anchor")
        self._db=sqlite3.connect(path,timeout=5)
        try:
            self._db.executescript("""CREATE TABLE IF NOT EXISTS custodian11_event(
                sequence INTEGER PRIMARY KEY,request_digest TEXT NOT NULL,nonce TEXT NOT NULL UNIQUE,
                payload_json TEXT NOT NULL,previous_mac TEXT NOT NULL,event_mac TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS custodian11_auth(
                deployment_id TEXT NOT NULL,transaction_id TEXT NOT NULL,payload_json TEXT NOT NULL,record_mac TEXT NOT NULL,
                PRIMARY KEY(deployment_id,transaction_id));""")
            self._db.execute("PRAGMA synchronous=FULL")
            if not self._anchor.exists() and not self._db.execute("SELECT 1 FROM custodian11_event").fetchone():self._write_anchor(0,"0"*64)
            self._verify_store()
        except BaseException:self._db.close();raise

    def _mac(self,value):return hmac.new(self._key,C(value),hashlib.sha256).hexdigest()

    def _write_anchor(self,count,head):
        body={"count":str(count),"head":head};raw=C({**body,"mac":self._mac(body)})
        tmp=self._anchor.with_suffix(self._anchor.suffix+".tmp")
        with open(tmp,"wb") as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,self._anchor)

    def _verify_store(self):
        previous="0"*64;count=0;expected_auth={}
        for row in self._db.execute("SELECT * FROM custodian11_event ORDER BY sequence"):
            count+=1;data=json.loads(row[3])
            body={"sequence":str(count),"request_digest":row[1],"nonce":row[2],"data":data,"previous_mac":previous}
            if row[0]!=count or row[4]!=previous or row[5]!=self._mac(body):raise ValueError("Custodian audit corruption")
            previous=row[5]
            if data["request"]["operation"]=="AUTHENTICATE_WITNESS":expected_auth[(self._deployment,data["request"]["transaction_id"])]=data["auth_record"]
        anchor=json.loads(self._anchor.read_text())
        if anchor!={"count":str(count),"head":previous,"mac":self._mac({"count":str(count),"head":previous})}:raise ValueError("Custodian anchor gap/deletion")
        observed={}
        for deployment,transaction,payload,mac in self._db.execute("SELECT * FROM custodian11_auth"):
            value=json.loads(payload)
            if mac!=self._mac(value):raise ValueError("Custodian AUTH integrity")
            observed[(deployment,transaction)]=value
        if expected_auth!=observed:raise ValueError("Custodian AUTH completeness")
        return count,previous

    def start(self):self._verify_store();self._running=True
    def stop(self):self._running=False
    def close(self):self._running=False;self._db.close()

    def handle(self,request):
        if not self._running:raise PermissionError("Custodian is stopped")
        operation=request.get("operation") if isinstance(request,dict) else None
        exact(request,AUTH if operation=="AUTHENTICATE_WITNESS" else VERIFY if operation=="VERIFY_WITNESS" else set())
        if request["contract"]!=CONTRACT or request["deployment_id"]!=self._deployment:raise PermissionError("Custodian version/deployment mismatch")
        proof=request["kernel_proof"];exact(proof,{"key_id","algorithm","signature"})
        if proof["key_id"]!=self._kernel_id or proof["algorithm"]!="ECDSA-P256-SHA256":raise PermissionError("unpinned Kernel")
        from agent_lab.identity_logical_continuity import utc
        now=datetime.now(timezone.utc);issued=utc(request["issued_at"]);expires=utc(request["expires_at"])
        if not issued<=now<expires or not 0<(expires-issued).total_seconds()<=5 or not re.fullmatch(r"[0-9a-f]{64}",request["nonce"]):raise PermissionError("expired Custodian lease")
        if H(unsigned(request,True))!=request["request_digest"]:raise ValueError("Custodian request digest")
        raw=unpack(proof["signature"],64)
        if len(raw)!=64:raise ValueError("Kernel signature width")
        r,s=int.from_bytes(raw[:32],"big"),int.from_bytes(raw[32:],"big")
        if not 1<=r<ORDER or not 1<=s<=ORDER//2:raise ValueError("noncanonical Kernel signature")
        self._public.verify(utils.encode_dss_signature(r,s),signing_bytes(request),ec.ECDSA(hashes.SHA256()))
        count,previous=self._verify_store()
        self._db.execute("BEGIN IMMEDIATE")
        try:
            old=self._db.execute("SELECT request_digest,payload_json FROM custodian11_event WHERE nonce=?",(request["nonce"],)).fetchone()
            if old:
                if old[0]!=request["request_digest"]:raise PermissionError("nonce substitution")
                self._db.rollback();return json.loads(old[1])["response"]
            auth_record=""
            if operation=="AUTHENTICATE_WITNESS":
                raw_unsigned=unpack(request["unsigned_record_bytes"],4096);record=public_unsigned(raw_unsigned)
                receipt_raw=unpack(request["staged_receipt_bytes"]);receipt=json.loads(receipt_raw.decode(),object_pairs_hook=_reject_duplicate_pairs);exact(receipt,RECEIPT)
                if C(receipt)!=receipt_raw or receipt["profile"]!="identity-audit-checkpoint/1" or digest(raw_unsigned)!=request["unsigned_record_digest"] or H(receipt)!=request["staged_receipt_digest"]:raise ValueError("receipt/preimage substitution")
                if receipt["deployment_id"]!=self._deployment or receipt["transaction_id"]!=request["transaction_id"] or receipt["request_digest"]!=request["identity_request_digest"]:raise PermissionError("receipt identity mismatch")
                cp,operation_id=checkpoint_identifiers(self._deployment,receipt["transaction_id"],receipt["request_digest"],receipt["response_digest"])
                composite=witness_commitment(deployment_id=self._deployment,logical_epoch=receipt["logical_epoch"],logical_head=receipt["logical_head"],audit_cut_count=receipt["audit_cut_count"],audit_cut_head=receipt["audit_cut_head"])
                if receipt["checkpoint_id"]!=cp or record.operation_id!=operation_id or record.identity_head!=H(composite):raise ValueError("checkpoint/composite mismatch")
                bindings=((record.deployment_id,self._deployment),(str(record.epoch),request["expected_epoch"]),(str(record.sequence),request["expected_sequence"]),(record.previous_record,request["previous_commitment"]),(record.kernel_head,request["kernel_pending_head"]),(record.identity_head,request["identity_new_head"]),(str(record.backup_generation),request["backup_generation"]),(record.object_key,request["witness_object_key"]),(str(record.backup_generation),receipt["backup_generation"]))
                if any(a!=b for a,b in bindings):raise ValueError("Witness/PENDING binding substitution")
                signed=record.signed(self._key);record_bytes=signed.to_bytes()
                auth_record={"unsigned_record_digest":request["unsigned_record_digest"],"receipt_digest":request["staged_receipt_digest"],"record_bytes":pack(record_bytes)}
                old_auth=self._db.execute("SELECT payload_json FROM custodian11_auth WHERE deployment_id=? AND transaction_id=?",(self._deployment,request["transaction_id"])).fetchone()
                if old_auth and json.loads(old_auth[0])!=auth_record:raise PermissionError("changed AUTH transaction")
                self._db.execute("INSERT OR IGNORE INTO custodian11_auth VALUES(?,?,?,?)",(self._deployment,request["transaction_id"],C(auth_record).decode(),self._mac(auth_record)))
            else:
                record_bytes=unpack(request["authenticated_record_bytes"],4096);signed=WitnessRecord.from_bytes(record_bytes,self._key)
                if (signed.deployment_id!=self._deployment or signed.object_key!=request["witness_object_key"] or not re.fullmatch(r"[1-9][0-9]*",request["witness_generation"]) or digest(record_bytes)!=request["expected_record_digest"] or digest(canonical_bytes(signed.unsigned()))!=request["expected_preimage_digest"] or signed.previous_record!=request["expected_previous_commitment"]):raise ValueError("Witness VERIFY substitution")
            response={field:request[field] for field in ("contract","operation","deployment_id","transaction_id","request_digest","nonce")}
            response.update(outcome="AUTHENTICATED" if operation=="AUTHENTICATE_WITNESS" else "VERIFIED",key_id=self._key_id,algorithm="HMAC-SHA-256",authenticated_record_bytes=pack(record_bytes),signed_record_digest=digest(record_bytes),denial_code="")
            data={"request":request,"response":response,"auth_record":auth_record}
            body={"sequence":str(count+1),"request_digest":request["request_digest"],"nonce":request["nonce"],"data":data,"previous_mac":previous}
            mac=self._mac(body)
            self._db.execute("INSERT INTO custodian11_event VALUES(?,?,?,?,?,?)",(count+1,request["request_digest"],request["nonce"],C(data).decode(),previous,mac))
            self._db.commit();self._write_anchor(count+1,mac)
            return response
        except BaseException:
            if self._db.in_transaction:self._db.rollback()
            raise


class CustodianServiceClient:
    """Concrete authenticated Named Pipe client; never receives a MAC key."""
    def __init__(self,*,deployment_id,pinned_server,custodian_key_id):
        from agent_lab.c09_named_pipe import PinnedProcess
        from agent_lab.c09_service_host import ROLE_BINDINGS,ServiceRole
        if not isinstance(pinned_server,PinnedProcess) or pinned_server.sid!=ROLE_BINDINGS[ServiceRole.KEY_CUSTODIAN][1]:raise PermissionError("frozen Custodian principal required")
        self.deployment_id=deployment_id;self._server=pinned_server;self._custodian_key_id=custodian_key_id

    def _exchange(self,body,signing_key,kernel_key_id,expected_outcome):
        import secrets
        from datetime import timedelta
        from agent_lab.identity_logical_continuity import sign_kernel_proof
        from agent_lab.c09_pipe_transport import exchange_custodian_control
        from agent_lab.ipc_wire_primitives import encode_frame,decode_frame
        now=datetime.now(timezone.utc);fmt=lambda value:value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request={"contract":CONTRACT,"deployment_id":self.deployment_id,"request_digest":"","nonce":secrets.token_hex(32),"issued_at":fmt(now),"expires_at":fmt(now+timedelta(seconds=5)),"kernel_proof":{"key_id":kernel_key_id,"algorithm":"ECDSA-P256-SHA256","signature":""},**body}
        request=sign_kernel_proof(request,signing_key)
        response=decode_frame(exchange_custodian_control(encode_frame(request),self._server))
        exact(response,REPLY)
        for name in ("contract","operation","deployment_id","transaction_id","request_digest","nonce"):
            if response[name]!=request[name]:raise PermissionError("Custodian response correlation mismatch")
        if response["outcome"]!=expected_outcome or response["key_id"]!=self._custodian_key_id or response["algorithm"]!="HMAC-SHA-256" or response["denial_code"]!="":raise PermissionError("Custodian refused authentication")
        raw=unpack(response["authenticated_record_bytes"],4096)
        if digest(raw)!=response["signed_record_digest"]:raise ValueError("Custodian record digest mismatch")
        WitnessRecord.from_public_bytes(raw)
        return raw

    def authenticate(self,pending,signing_key,kernel_key_id):
        receipt=pending["receipt"];record=public_unsigned(unpack(pending["unsigned_record_bytes"],4096))
        body={"operation":"AUTHENTICATE_WITNESS","transaction_id":receipt["transaction_id"],"unsigned_record_bytes":pending["unsigned_record_bytes"],"unsigned_record_digest":digest(canonical_bytes(record.unsigned())),"staged_receipt_bytes":pack(C(receipt)),"staged_receipt_digest":H(receipt),"identity_request_digest":receipt["request_digest"],"expected_epoch":str(record.epoch),"expected_sequence":str(record.sequence),"previous_commitment":record.previous_record,"kernel_pending_head":record.kernel_head,"identity_new_head":record.identity_head,"backup_generation":str(record.backup_generation),"witness_object_key":record.object_key}
        raw=self._exchange(body,signing_key,kernel_key_id,"AUTHENTICATED")
        if WitnessRecord.from_public_bytes(raw).unsigned()!=record.unsigned():raise ValueError("Custodian changed unsigned record")
        return raw

    def verify(self,raw,generation,transaction_id,signing_key,kernel_key_id):
        record=WitnessRecord.from_public_bytes(raw)
        body={"operation":"VERIFY_WITNESS","transaction_id":transaction_id,"authenticated_record_bytes":pack(raw),"witness_object_key":record.object_key,"witness_generation":generation,"expected_record_digest":digest(raw),"expected_preimage_digest":digest(canonical_bytes(record.unsigned())),"expected_previous_commitment":record.previous_record}
        observed=self._exchange(body,signing_key,kernel_key_id,"VERIFIED")
        if observed!=raw:raise ValueError("Custodian substituted readback")
        return record
