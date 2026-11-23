"""Versioned Option B Owner source in the canonical Identity database only.

Explicit role-private staging verifies a scoped Owner assertion before storing
immutable bytes. It never creates a person or an authorization decision. Existing
Identity mutation owns single-use consumption, logical continuity and Witness.
"""
import base64
from dataclasses import asdict
from datetime import date,datetime,timezone
import hashlib
import hmac
import json
from agent_lab.identity_mutation_source import ProtectedMutationSource,MaterializedMutation,EvidenceArtifact
from agent_lab.identity_evidence_authority import EvidenceScope
from agent_lab.identity_protected_revision import ProtectedRevision,ProtectedReference,MaterializedRevision
from agent_lab.owner_identity_assertion import SCOPE,EnrolledOwnerCredential,verify_owner_assertion,OwnerAssertionError
from agent_lab.owner_identity_broker import authorization_reference
from agent_lab.ipc_wire_primitives import canonical_sha256 as H
from cryptography.hazmat.primitives import serialization
from agent_lab.owner_identity_delivery import verify as verify_delivery,digest as delivery_digest

TABLE='identity_owner_declaration_v1'
PROVIDER='identity-owner-declaration-v1'
ACTION='OWNER_DECLARATION_REVISION_V1'

def _json(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def _content_digest(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()

def verify_storage(owner):
    expected={}
    for row in owner._db.execute('SELECT event_payload FROM identity_audit ORDER BY event_id'):
        event=json.loads(row[0])
        if event['action']==ACTION:expected[event['subject_id']]=event['details_digest']
    exists=owner._db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(TABLE,)).fetchone()
    if exists is None:
        if expected:raise OwnerAssertionError('Owner evidence table deleted')
        return
    actual={}
    for row in owner._db.execute('SELECT * FROM '+TABLE):
        payload=json.loads(row['payload_json'])
        if not hmac.compare_digest(row['row_mac'],owner._mac(payload)):raise OwnerAssertionError('Owner evidence integrity failure')
        actual[row['reference']]=owner._mac(dict(reference=row['reference'],row_mac=row['row_mac']))
    if expected!=actual:raise OwnerAssertionError('Owner evidence deletion/substitution')

def _write(owner,reference,payload):
    mac=owner._mac(payload)
    owner._db.execute('INSERT INTO '+TABLE+' VALUES(?,?,?) ON CONFLICT(reference) DO UPDATE SET payload_json=excluded.payload_json,row_mac=excluded.row_mac',
                      (reference,_json(payload),mac))
    owner._append_audit(ACTION,payload['intent']['case_id'],reference,dict(reference=reference,row_mac=mac))

class CanonicalOwnerDeclarationSource(ProtectedMutationSource):
    def __init__(self,owner,*,deployment_id,store_id):
        # Pinned configuration comes from accepted native enrollment/startup,
        # never a request/public-key field or an environment authorization flag.
        self.owner=owner;self.deployment_id=deployment_id;self.root_id=store_id
        logical=owner._logical_row()
        if logical is None or (logical['deployment_id'],logical['store_id'])!=(deployment_id,store_id):
            raise OwnerAssertionError('accepted exact Identity enrollment required')
        if owner._continuity_keys is None:raise OwnerAssertionError('accepted canonical Kernel key required')

    def _approval(self,delivery,now):
        keys=self.owner._continuity_keys
        payload=verify_delivery(delivery,kernel_public_key=keys.kernel_public_key,key_id=keys.kernel_key_id,
            deployment_id=self.deployment_id,store_id=self.root_id)
        credential=payload['owner_credential']
        if type(credential) is not dict or set(credential)!={'owner_id','credential_id','public_key_der','enrollment_proof_digest','revoked'} or credential['revoked'] is not False:
            raise OwnerAssertionError('accepted nonrevoked native Owner pin required')
        pin=EnrolledOwnerCredential(credential['owner_id'],base64.b64decode(credential['credential_id'],validate=True),
            base64.b64decode(credential['public_key_der'],validate=True),0)
        intent=payload['intent'];scope={k:intent[k] for k in SCOPE}
        assertion={k:base64.b64decode(v,validate=True) for k,v in payload['assertion'].items()}
        proof=verify_owner_assertion(intent=intent,expected_scope=scope,enrollment=pin,now=now,**assertion)
        expected=dict(contract='ai-tax-agent.owner-approval/1',intent_digest=proof.intent_digest,proof_digest=proof.proof_digest,
            scope=scope,nonce=intent['nonce'],issued_at=intent['issued_at'],expires_at=intent['expires_at'],
            execution_authorization_reference=authorization_reference(scope))
        expected['authority_reference']=delivery_digest(expected)
        if payload['approval']!=expected:raise OwnerAssertionError('committed Kernel approval/intent/proof substitution')
        if (scope['owner_id'],scope['deployment_id'],scope['store_id'])!=(pin.owner_id,self.deployment_id,self.root_id):
            raise OwnerAssertionError('Kernel-delivered native pin scope mismatch')
        return intent,scope,proof

    def stage(self,*,delivery,confirmed_values,artifacts,now):
        """Identity role-private evidence write; actual verified content only.

        Caller already holds the Identity serialization lock. This is not a
        dashboard/IPC bypass for person writes: no domain rows change here.
        """
        intent,scope,proof=self._approval(delivery,now)
        if (H(confirmed_values)!=scope['input_digest'] or scope['operation'] not in {'REGISTER_IDENTITY','CORRECT_PERSON','BIND_PARTY'}):
            raise OwnerAssertionError('Owner source operation/input mismatch')
        case=self.owner._cases.get(scope['case_id'])
        if case is None or case.owner_id!=scope['owner_id'] or str(case.tax_period.year)!=scope['tax_year']:
            raise OwnerAssertionError('Owner source case authorization mismatch')
        if type(artifacts) is not tuple or not 1<=len(artifacts)<=8:raise OwnerAssertionError('bounded Owner artifacts required')
        material=[]
        for kind,raw in artifacts:
            if type(raw) is not bytes or not 1<=len(raw)<=65536 or kind not in {'IDENTITY_RECORD','ROLE_EVIDENCE'}:
                raise OwnerAssertionError('bounded Owner source content required')
            from agent_lab.identity_atomic_mutation import protected_json
            value=protected_json(raw)
            if kind=='IDENTITY_RECORD':
                attrs=dict(value['lookup_attributes'])
                wanted={k:v for k,v in confirmed_values.items() if k in {'first_name','last_name','birth_date','tax_id'}}
                if (len(attrs)!=len(value['lookup_attributes']) or attrs!=wanted or value['identity_id']!=scope['subject_id'] or
                    value['name']!=wanted.get('first_name','')+' '+wanted.get('last_name','') or scope['operation']=='BIND_PARTY'):
                    raise OwnerAssertionError('record differs from Owner-confirmed values')
            elif value!={'subject_id':scope['subject_id'],'case_id':scope['case_id'],'tax_year':scope['tax_year'],'role':confirmed_values.get('role')} or scope['operation']!='BIND_PARTY':
                raise OwnerAssertionError('role evidence differs from confirmed scope')
            material.append(dict(reference=_content_digest(raw),kind=kind,content=base64.b64encode(raw).decode()))
        if len({item['reference'] for item in material})!=len(material):raise OwnerAssertionError('duplicate Owner artifacts')
        reference=authorization_reference(scope)
        stored=dict(contract='ai-tax-agent.identity-owner-source/1',intent=intent,delivery=delivery,
            approval_digest=delivery['approval']['authority_reference'],confirmed_values=confirmed_values,
            proof_digest=proof.proof_digest,artifacts=material,revoked=False)
        def write():
            verify_storage(self.owner)
            self.owner._db.execute('CREATE TABLE IF NOT EXISTS '+TABLE+'(reference TEXT PRIMARY KEY,payload_json TEXT NOT NULL,row_mac TEXT NOT NULL)')
            old=self.owner._db.execute('SELECT payload_json FROM '+TABLE+' WHERE reference=?',(reference,)).fetchone()
            if old:
                if json.loads(old[0])!=stored:raise OwnerAssertionError('immutable Owner evidence conflict')
                return
            _write(self.owner,reference,stored)
        self.owner._commit('OWNER_DECLARATION_STAGE_V1',write)
        return reference,tuple(item['reference'] for item in material)

    def _row(self,reference):
        verify_storage(self.owner)
        try:row=self.owner._db.execute('SELECT payload_json FROM '+TABLE+' WHERE reference=?',(reference,)).fetchone()
        except Exception:raise OwnerAssertionError('Owner evidence not enrolled') from None
        if row is None:raise OwnerAssertionError('Owner evidence unavailable')
        payload=json.loads(row[0])
        if payload['revoked'] is not False:raise OwnerAssertionError('Owner evidence revoked')
        return payload

    def _historical_role(self,reference,case_id,year,subject,kind='ROLE_EVIDENCE'):
        """Authentic prior fact, never a reusable authorization.

        Query scope is enforced by SQLite before protected bytes are loaded.
        Authentication lease is checked at original confirmation time; current
        access still requires the existing signed read/mutation authorization.
        Explicit declaration revocation remains effective.
        """
        verify_storage(self.owner)
        if not self.owner._db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(TABLE,)).fetchone():return None
        rows=self.owner._db.execute('SELECT reference,payload_json FROM '+TABLE+" WHERE json_extract(payload_json,'$.intent.case_id')=? AND json_extract(payload_json,'$.intent.tax_year')=? AND json_extract(payload_json,'$.intent.subject_id')=?",(case_id,str(year),subject)).fetchall()
        found=[]
        for row in rows:
            data=json.loads(row['payload_json'])
            entries=[a for a in data['artifacts'] if a['reference']==reference and a['kind']=='ROLE_EVIDENCE']
            if kind=='IDENTITY_AUTHORIZATION' and row['reference']==reference:
                entries=[dict(content=base64.b64encode(_json(dict(intent=data['intent'],proof_digest=data['proof_digest'])).encode()).decode())]
            if not entries:continue
            if data['revoked'] is not False:raise OwnerAssertionError('prior role declaration revoked')
            issued=datetime.strptime(data['intent']['issued_at'],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
            _,scope,proof=self._approval(data['delivery'],issued)
            if scope['operation']!='BIND_PARTY' or scope['owner_id']!=self.owner._cases.get(case_id).owner_id or proof.proof_digest!=data['proof_digest']:
                raise OwnerAssertionError('prior role provenance mismatch')
            for entry in entries:
                raw=base64.b64decode(entry['content'],validate=True)
                if kind=='ROLE_EVIDENCE' and _content_digest(raw)!=reference:raise OwnerAssertionError('prior role content mismatch')
                found.append(raw)
        if not found:return None
        if any(raw!=found[0] for raw in found):raise OwnerAssertionError('ambiguous prior role')
        return found[0]

    def existing_role_evidence(self,kind,reference,case_id,year,subject,start,end):
        if kind not in {'ROLE_EVIDENCE','IDENTITY_AUTHORIZATION'}:return None
        context=self.owner._protocol_context
        if context is None or (context['case_id'],context['tax_year'])!=(case_id,str(year)):
            raise OwnerAssertionError('current scoped Identity context required')
        if not date(year,1,1)<=start<end<=date(year+1,1,1):raise OwnerAssertionError('prior evidence interval mismatch')
        column='evidence_ref' if kind=='ROLE_EVIDENCE' else 'authorization_ref'
        if not self.owner._db.execute('SELECT 1 FROM case_party_role WHERE case_id=? AND subject_id=? AND '+column+'=?',(case_id,subject,reference)).fetchone():return None
        raw=self._historical_role(reference,case_id,year,subject,kind)
        if raw is None:return None
        # Return real verified content, never a synthetic success/authority flag.
        return MaterializedRevision(ProtectedRevision(PROVIDER,self.root_id,reference,'1'),raw)

    def resolve(self,request,case,now):
        if len(request['authorization_references'])!=1:raise OwnerAssertionError('one Owner declaration required')
        reference=request['authorization_references'][0];row=self._row(reference);intent=row['intent']
        delivered_intent,scope,proof=self._approval(row['delivery'],now)
        if delivered_intent!=intent or proof.proof_digest!=row['proof_digest'] or row['approval_digest']!=row['delivery']['approval']['authority_reference']:
            raise OwnerAssertionError('stored approval revision mismatch')
        expected=dict(operation=request['domain_operation'],case_id=request['case_id'],tax_year=request['tax_year'],
            subject_id=request['payload']['subject_id'],deployment_id=request['deployment_id'],task_id=request['task_id'],
            manifest_id=request['manifest_id'],run_id=request['run_id'],store_id=self.root_id,owner_id=case.owner_id,
            input_digest=H(row['confirmed_values']))
        if scope!=expected or reference!=authorization_reference(scope):raise OwnerAssertionError('Owner source execution substitution')
        year=int(scope['tax_year'])
        evidence_scope=EvidenceScope(case.case_id,year,scope['subject_id'],'owner.confirmed.person',request['actor_instance_id'],
            scope['run_id'],scope['task_id'],scope['manifest_id'],date(year,1,1),date(year+1,1,1))
        expiry=datetime.strptime(intent['expires_at'],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
        authorization=_json(dict(intent=intent,proof_digest=row['proof_digest'])).encode()
        entries=[dict(reference=reference,kind='IDENTITY_AUTHORIZATION',content=base64.b64encode(authorization).decode()),*row['artifacts']]
        if request['domain_operation']=='CORRECT_PERSON':
            prior=self.owner._db.execute('SELECT evidence_ref,authorization_ref FROM case_party_role WHERE case_id=? AND subject_id=?',
                (case.case_id,scope['subject_id'])).fetchall()
            for binding in prior:
                for column,kind in (('evidence_ref','ROLE_EVIDENCE'),('authorization_ref','IDENTITY_AUTHORIZATION')):
                    ref=binding[column]
                    raw=self._historical_role(ref,case.case_id,year,scope['subject_id'],kind)
                    if raw is not None and not any(e['reference']==ref for e in entries):
                        entries.append(dict(reference=ref,kind=kind,content=base64.b64encode(raw).decode()))
        artifacts=[]
        for entry in entries:
            raw=base64.b64decode(entry['content'],validate=True)
            revision=ProtectedRevision(PROVIDER,self.root_id,entry['reference'],'1')
            accepted=ProtectedReference(revision,evidence_scope,_content_digest(raw),expiry,None)
            artifacts.append(EvidenceArtifact(entry['reference'],entry['kind'],accepted,MaterializedRevision(revision,raw)))
        return MaterializedMutation(scope['subject_id'],'OWNER-NONCE:'+intent['nonce'],tuple(artifacts))

    def revalidate(self,request,case,now):
        # Re-read authoritative revocation/content inside the Identity writer
        # transaction, closing the pre-resolution-to-COMMIT race.
        return self.resolve(request,case,now)
