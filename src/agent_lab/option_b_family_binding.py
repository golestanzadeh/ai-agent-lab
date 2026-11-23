"""Accepted Option B dependency binding; no enrollment, keys or authority issuer.

Configuration is metadata, never proof. Existing Kernel Human Gate, independent
acceptance, canonical enrollment, Owner Broker, protected keys and concrete
Custodian/Witness ports must all verify before the existing Family adapter binds.
"""
from dataclasses import dataclass
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from agent_lab import owner_identity_broker as broker
from agent_lab.family_identity_gateway import FamilyIdentityGateway,FamilyUnavailable
from agent_lab.identity_owner_source import CanonicalOwnerDeclarationSource,PROVIDER
from agent_lab.ipc_wire_primitives import canonical_sha256 as H

SCHEMA='ai-tax-agent.option-b-family-binding/1'
FIELDS={'schema','deployment_id','store_id','owner_id','owner_sid','case_years','source_provider',
        'source_build_ref','source_scope_ref','kernel_key_ref','identity_key_ref','custody_ref',
        'audit_recovery_ref','witness_bucket','custodian_key_id','acceptance_task_id','not_before','expires_at'}
FIELDS|={'identity_image_path','identity_image_ref'}

def public_ref(key):
    public=key.public_key() if hasattr(key,'private_bytes') else key
    return 'sha256:'+hashlib.sha256(public.public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)).hexdigest()

def source_build_ref():
    return H(build_manifest())

def build_manifest(root=None):
    root=Path(root) if root is not None else Path(__file__).resolve().parents[2]
    package=root/'src'/'agent_lab'
    # Pin the complete shipped application code and UI, not a hand-maintained
    # list of authority modules that can silently omit a newly imported module.
    suffixes={'.py','.js','.css','.html','.json'}
    files=[p for p in package.rglob('*') if p.is_file() and p.suffix.lower() in suffixes
           and not any(part.startswith('.') or part=='__pycache__' for part in p.relative_to(package).parts)]
    for directory in ('ui_static','ui_templates'):
        files.extend(p for p in (root/directory).rglob('*') if p.is_file() and p.suffix.lower() in suffixes)
    files.extend(p for p in (root/'contracts').rglob('*') if p.is_file() and p.suffix.lower() in {'.json','.yaml','.yml'})
    files.extend(p for name in ('requirements.txt','requirements-hg01-build.txt') if (p:=root/name).is_file())
    files=sorted(set(files))
    return dict(schema='ai-tax-agent.family-build-manifest/1',files=[[p.relative_to(root).as_posix(),'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()] for p in sorted(files)])

def _time(value):
    if type(value) is not str:raise FamilyUnavailable('FAMILY_BINDING_TIME_INVALID')
    try:result=datetime.strptime(value,'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
    except ValueError:raise FamilyUnavailable('FAMILY_BINDING_TIME_INVALID') from None
    return result

@dataclass(frozen=True)
class OptionBFamilyBinding:
    payload: dict
    reference: str

    @classmethod
    def parse(cls,payload):
        import re
        if type(payload) is not dict or set(payload)!=FIELDS or payload['schema']!=SCHEMA:
            raise FamilyUnavailable('FAMILY_BINDING_SCHEMA_INVALID')
        if any(type(payload[k]) is not str or not 1<=len(payload[k].encode())<=256 for k in FIELDS-{'case_years'}):
            raise FamilyUnavailable('FAMILY_BINDING_FIELD_INVALID')
        scopes=payload['case_years']
        if type(scopes) is not list or not 1<=len(scopes)<=128 or any(type(s) is not list or len(s)!=2 or any(type(v) is not str for v in s) for s in scopes):
            raise FamilyUnavailable('FAMILY_BINDING_SCOPE_INVALID')
        if len({s[0] for s in scopes})!=len(scopes) or any(not s[0] or len(s[0])>128 or not re.fullmatch(r'[0-9]{4}',s[1]) or not 1900<=int(s[1])<=9998 for s in scopes):
            raise FamilyUnavailable('FAMILY_BINDING_SCOPE_INVALID')
        if payload['source_provider']!=PROVIDER or not re.fullmatch(r'S-1-5(?:-[0-9]+){1,15}',payload['owner_sid']):
            raise FamilyUnavailable('FAMILY_BINDING_OWNER_SOURCE_INVALID')
        for k in ('source_build_ref','source_scope_ref','kernel_key_ref','identity_key_ref','custody_ref','audit_recovery_ref','identity_image_ref'):
            if not re.fullmatch(r'sha256:[0-9a-f]{64}',payload[k]):raise FamilyUnavailable('FAMILY_BINDING_REFERENCE_INVALID')
        if not Path(payload['identity_image_path']).is_absolute():raise FamilyUnavailable('FAMILY_IDENTITY_IMAGE_INVALID')
        if _time(payload['not_before'])>=_time(payload['expires_at']):raise FamilyUnavailable('FAMILY_BINDING_LEASE_INVALID')
        # Detach nested mutable request/configuration data.
        frozen_copy=json.loads(json.dumps(payload))
        return cls(frozen_copy,H(frozen_copy))

    @classmethod
    def load(cls,path):
        from agent_lab.identity_atomic_mutation import protected_json
        raw=Path(path).read_bytes()
        if len(raw)>32768:raise FamilyUnavailable('FAMILY_BINDING_TOO_LARGE')
        return cls.parse(protected_json(raw))


class BoundOptionBFamily:
    """Borrow existing authorities/ports. Never construct replacement stores."""
    def __init__(self,binding,*,kernel,cases,key_root,client,read_scope,resolve_intents=None):
        from agent_lab.orchestrator_kernel import OrchestratorKernel
        from agent_lab.case_registry import CaseRegistry
        from agent_lab.c09_operational_service_runtime import KernelIdentityServiceClient
        if not isinstance(binding,OptionBFamilyBinding) or not isinstance(kernel,OrchestratorKernel) or not isinstance(cases,CaseRegistry):
            raise FamilyUnavailable('FAMILY_CANONICAL_DEPENDENCIES_REQUIRED')
        if client is not None and (not isinstance(client,KernelIdentityServiceClient) or client._kernel is not kernel):
            raise FamilyUnavailable('FAMILY_CANONICAL_CLIENT_REQUIRED')
        self.binding=binding;self.kernel=kernel;self.cases=cases;self.key_root=Path(key_root)
        self.client=client;self.read_scope=read_scope;self.resolve_intents=resolve_intents

    def ensure_ready(self,*,require_client=True,recovery=False):
        from agent_lab.c09_service_host import current_process_sid
        from agent_lab.owner_identity_keys import load_key
        p=self.binding.payload
        if H(p)!=self.binding.reference:raise FamilyUnavailable('FAMILY_BINDING_CHANGED')
        if not recovery and not _time(p['not_before'])<=datetime.now(timezone.utc)<_time(p['expires_at']):raise FamilyUnavailable('FAMILY_BINDING_EXPIRED')
        if current_process_sid()!=p['owner_sid']:raise FamilyUnavailable('FAMILY_OWNER_TOKEN_MISMATCH')
        k=self.kernel;k._verify_identity_protocol_state()
        if k.database_path.resolve().parent!=self.key_root.resolve() or not (self.key_root/'identity.sqlite').is_file():
            raise FamilyUnavailable('FAMILY_CANONICAL_STORAGE_ROOT_MISMATCH')
        if k.kill_switch_state()!='RUNNING':raise FamilyUnavailable('FAMILY_KERNEL_HALTED')
        accepted=broker.canonical_enrollment_binding(k)
        if accepted!=dict(deployment_id=p['deployment_id'],store_id=p['store_id']):raise FamilyUnavailable('FAMILY_ENROLLMENT_MISMATCH')
        owner=broker._load(k,p['deployment_id'])
        if not recovery:broker._credential(owner)
        if (owner['owner_id'],owner['store_id'])!=(p['owner_id'],p['store_id']):raise FamilyUnavailable('FAMILY_OWNER_ENROLLMENT_MISMATCH')
        task=k._connection.execute('SELECT * FROM tasks WHERE task_id=?',(p['acceptance_task_id'],)).fetchone()
        gate=k._connection.execute("SELECT * FROM task_human_gates WHERE task_id=? AND trigger='permission_expansion'",(p['acceptance_task_id'],)).fetchone()
        review=k._connection.execute('SELECT * FROM acceptance_records WHERE task_id=? ORDER BY acceptance_id DESC LIMIT 1',(p['acceptance_task_id'],)).fetchone()
        if recovery:review=k._connection.execute("SELECT * FROM acceptance_records WHERE task_id=? AND decision='PASS' AND evidence_reference=? ORDER BY acceptance_id DESC LIMIT 1",(p['acceptance_task_id'],self.binding.reference)).fetchone()
        if (task is None or task['role_id']!='OPERATIONS_INTEGRATION_AGENT' or (not recovery and task['status']!='COMPLETED') or
            self.binding.reference not in json.loads(task['payload_json'])['inputs'] or gate is None or (not recovery and gate['status']!='APPROVED') or
            (not recovery and gate['authority_reference']!=self.binding.reference) or review is None or review['decision']!='PASS' or
            review['evidence_reference']!=self.binding.reference or review['reviewer_instance_id']==task['actor_instance_id']):
            raise FamilyUnavailable('FAMILY_OPERATIONAL_BINDING_NOT_ACCEPTED')
        reviewer=k._connection.execute('SELECT * FROM manifests WHERE manifest_id=?',(review['reviewer_manifest_id'],)).fetchone()
        child=k._connection.execute('SELECT * FROM tasks WHERE task_id=?',(reviewer['task_id'],)).fetchone() if reviewer else None
        events=k._connection.execute("SELECT event_id,event_type,actor_id,payload_json FROM audit_events WHERE entity_id=? AND event_type IN ('HUMAN_GATE_DECIDED','INDEPENDENT_ACCEPTANCE_RECORDED') ORDER BY event_id",(p['acceptance_task_id'],)).fetchall()
        gates=[e for e in events if e['event_type']=='HUMAN_GATE_DECIDED' and json.loads(e['payload_json']).get('trigger')=='permission_expansion']
        reviews=[e for e in events if e['event_type']=='INDEPENDENT_ACCEPTANCE_RECORDED']
        if recovery:
            gates=[e for e in gates if json.loads(e['payload_json'])==dict(trigger='permission_expansion',decision='APPROVED',authority_reference=self.binding.reference)]
            reviews=[e for e in reviews if json.loads(e['payload_json'])==dict(decision='PASS',evidence_reference=self.binding.reference,reviewer_manifest_id=review['reviewer_manifest_id'])]
        if (reviewer is None or reviewer['role_id']!='INDEPENDENT_ACCEPTANCE_AGENT' or child is None or child['parent_task_id']!=task['task_id'] or
            reviewer['actor_instance_id']!=review['reviewer_instance_id'] or not gates or not reviews or gates[-1]['actor_id']!='HUMAN_PROJECT_OWNER' or
            json.loads(gates[-1]['payload_json'])!=dict(trigger='permission_expansion',decision='APPROVED',authority_reference=self.binding.reference) or
            reviews[-1]['actor_id']!=review['reviewer_instance_id'] or json.loads(reviews[-1]['payload_json'])!=dict(decision='PASS',evidence_reference=self.binding.reference,reviewer_manifest_id=review['reviewer_manifest_id'])):
            raise FamilyUnavailable('FAMILY_BINDING_ACCEPTANCE_LINEAGE_INVALID')
        self._authority_events=(str(gates[-1]['event_id']),str(reviews[-1]['event_id']))
        if p['source_build_ref']!=source_build_ref() or p['source_scope_ref']!=H(dict(deployment_id=p['deployment_id'],store_id=p['store_id'],owner_id=p['owner_id'],case_years=p['case_years'])):
            raise FamilyUnavailable('FAMILY_SOURCE_BINDING_MISMATCH')
        for case_id,year in p['case_years']:
            case=self.cases.get(case_id)
            if case is None or case.owner_id!=p['owner_id'] or str(case.tax_period.year)!=year:raise FamilyUnavailable('FAMILY_CASE_BINDING_MISMATCH')
        kernel_key=load_key(self.key_root,role='kernel',owner_id=p['owner_id'])
        identity_key=load_key(self.key_root,role='identity',owner_id=p['owner_id'])
        if public_ref(kernel_key)!=p['kernel_key_ref'] or public_ref(identity_key)!=p['identity_key_ref']:
            raise FamilyUnavailable('FAMILY_KEY_BINDING_MISMATCH')
        if require_client:
            from agent_lab.c09_custodian_operational import CustodianServiceClient
            from agent_lab.c09_gcs_witness_adapter import GCSWitnessAdapter
            c=self.client
            if (c is None or c._deployment!=p['deployment_id'] or not c._mutation_pipeline or c._identity.sid!=p['owner_sid'] or
                c._owner_binding is None or c._owner_binding.binding.reference!=self.binding.reference or
                getattr(k,'_family_runtime_binding',None) is None or k._family_runtime_binding.binding.reference!=self.binding.reference or
                str(Path(c._identity.image_path)).casefold()!=str(Path(p['identity_image_path'])).casefold() or c._identity.image_sha256!=p['identity_image_ref'] or
                public_ref(c._signer)!=p['kernel_key_ref'] or not isinstance(c._custodian,CustodianServiceClient) or
                c._custodian.deployment_id!=p['deployment_id'] or c._custodian._custodian_key_id!=p['custodian_key_id'] or
                not isinstance(c._provider,GCSWitnessAdapter) or c._provider.bucket!=p['witness_bucket']):
                raise FamilyUnavailable('FAMILY_CLIENT_WITNESS_BINDING_MISMATCH')

    def recovery_ready(self,*,require_client=True):
        self.ensure_ready(require_client=require_client,recovery=True)
        state=self.kernel._identity_payload('identity_kernel_state','deployment_id',self.binding.payload['deployment_id'])
        if not any(self._bound_transaction(tx) for tx in state.get('mutations',{}).values()):
            raise FamilyUnavailable('FAMILY_BOUND_RECOVERY_UNAVAILABLE')

    def _bound_transaction(self,tx):
        request=tx['prepare_request']
        issued=self.kernel._identity_payload('identity_kernel_request','nonce',request['kernel_proof']['nonce'])
        if issued is None or issued.get('family_binding_ref')!=self.binding.reference:return False
        for field,kind in (('family_binding_gate_event','HUMAN_GATE_DECIDED'),('family_binding_review_event','INDEPENDENT_ACCEPTANCE_RECORDED')):
            event=self.kernel._connection.execute('SELECT * FROM audit_events WHERE event_id=?',(issued.get(field),)).fetchone()
            if event is None or event['event_type']!=kind or event['entity_id']!=self.binding.payload['acceptance_task_id']:return False
            payload=json.loads(event['payload_json'])
            if kind=='HUMAN_GATE_DECIDED' and (event['actor_id']!='HUMAN_PROJECT_OWNER' or payload!=dict(trigger='permission_expansion',decision='APPROVED',authority_reference=self.binding.reference)):return False
            if kind=='INDEPENDENT_ACCEPTANCE_RECORDED' and (payload.get('decision')!='PASS' or payload.get('evidence_reference')!=self.binding.reference):return False
        return True

    def authorize_request(self,*,message_type,transaction_id,case_id,tax_year,**unused):
        self.scope_allowed(case_id,tax_year)
        if message_type in {'GET_TRANSACTION','FINALIZE_MUTATION','ABORT_PREPARED'}:
            self.ensure_ready(require_client=False,recovery=True)
            state=self.kernel._identity_payload('identity_kernel_state','deployment_id',self.binding.payload['deployment_id'])
            tx=state.get('mutations',{}).get(transaction_id)
            if tx is None or not self._bound_transaction(tx):raise FamilyUnavailable('FAMILY_EXACT_BOUND_RECOVERY_REQUIRED')
        else:self.ensure_ready(require_client=False)

    def constructor_ready(self):
        try:self.ensure_ready(require_client=False)
        except Exception:self.recovery_ready(require_client=False)

    def bind_authority(self,authority,config):
        # Executed on the Identity SQLite owner thread. Kernel state was checked
        # before host start; never share its SQLite connection across threads.
        p=self.binding.payload
        from agent_lab.c09_service_host import current_process_sid
        if H(p)!=self.binding.reference or current_process_sid()!=p['owner_sid']:
            raise FamilyUnavailable('FAMILY_SOURCE_BINDING_INVALID')
        if (config.deployment_id,config.principal_sid)!=(p['deployment_id'],p['owner_sid']):raise FamilyUnavailable('FAMILY_SOURCE_HOST_MISMATCH')
        if authority._path!=(self.key_root/'identity.sqlite').resolve():raise FamilyUnavailable('FAMILY_CANONICAL_IDENTITY_PATH_MISMATCH')
        if public_ref(authority._continuity_keys.kernel_public_key)!=p['kernel_key_ref']:
            raise FamilyUnavailable('FAMILY_SOURCE_KERNEL_PIN_MISMATCH')
        authority._mutation_source=CanonicalOwnerDeclarationSource(authority,deployment_id=p['deployment_id'],store_id=p['store_id'])
        source=authority._mutation_source
        original=authority._resolve_evidence
        def evidence(*args):
            current=source.existing_role_evidence(*args)
            return current if current is not None else original(*args)
        authority._resolve_evidence=evidence

    def scope_allowed(self,case_id,tax_year):
        if [case_id,str(tax_year)] not in self.binding.payload['case_years']:raise FamilyUnavailable('FAMILY_SCOPE_DENIED')

    def gateway(self):
        # Reverify independent Witness via existing concrete ports, not a config
        # digest/boolean. This issues no Identity mutation or new enrollment.
        c=self.client
        bound=self
        def read_scope(case,year,run):
            bound.scope_allowed(case,year)
            return bound.read_scope(case,year,run)
        def resolve(case,year,run,action,values):
            bound.scope_allowed(case,year)
            intents=bound.resolve_intents(case,year,run,action,values)
            owner=broker._load(bound.kernel,bound.binding.payload['deployment_id']);broker._credential(owner)
            for intent in intents:
                matched=[item for item in owner['intents'].values() if item['status']=='APPROVED' and
                    broker.authorization_reference({key:item['intent'][key] for key in broker.SCOPE})==intent.scope.authorization_ref]
                if len(matched)!=1 or matched[0]['intent']['input_digest']!=H(values):raise FamilyUnavailable('FAMILY_APPROVED_INTENT_REQUIRED')
            return intents
        return BoundFamilyIdentityGateway(binding=bound,cases=self.cases,owner_id=self.binding.payload['owner_id'],client=c,read_scope=read_scope,
            resolve_intents=resolve if self.resolve_intents is not None else None)

class BoundFamilyIdentityGateway(FamilyIdentityGateway):
    def __init__(self,*,binding,**kwargs):
        if not isinstance(binding,BoundOptionBFamily):raise FamilyUnavailable('FAMILY_ACCEPTED_BINDING_REQUIRED')
        if kwargs.get('client') is not binding.client or kwargs.get('cases') is not binding.cases or kwargs.get('owner_id')!=binding.binding.payload['owner_id']:
            raise FamilyUnavailable('FAMILY_GATEWAY_DEPENDENCIES_MISMATCH')
        # Reconstruct externally verified freshness on every cold factory
        # composition. A new Kernel process has no in-memory verified head.
        # Do not treat an accepted binding digest as a substitute for Witness.
        try:binding.ensure_ready(require_client=False)
        except Exception:binding.recovery_ready(require_client=False)
        c=binding.client
        binding.kernel.verify_identity_witness_state(c._deployment,custodian=c._custodian,provider=c._provider,signing_key=c._signer,kernel_key_id=c._key_id)
        try:binding.ensure_ready()
        except Exception:binding.recovery_ready()
        self._binding=binding
        super().__init__(**kwargs)
    def ensure_ready(self,*,recovery=False):
        if recovery:self._binding.recovery_ready()
        else:self._binding.ensure_ready()

class OptionBFamilyFactory:
    """Metadata loader for the existing local app; borrows its existing client."""
    def __init__(self,*,client,read_scope,resolve_intents=None):
        self.client=client;self.read_scope=read_scope;self.resolve_intents=resolve_intents

    def load(self,host):
        binding=OptionBFamilyBinding.load(Path(host.root)/'family-runtime-binding.json')
        return BoundOptionBFamily(binding,kernel=self.client._kernel,cases=host.registry,key_root=host.root,
            client=self.client,read_scope=self.read_scope,resolve_intents=self.resolve_intents)

def compose_family_gateway(host,bound=None):
    """Actual local factory hook. Missing/unaccepted composition stays disabled."""
    if bound is None:return None
    try:
        if isinstance(bound,OptionBFamilyFactory):bound=bound.load(host)
        if not isinstance(bound,BoundOptionBFamily) or bound.cases is not host.registry or bound.binding.payload['owner_id']!=host.owner_id:
            raise FamilyUnavailable('FAMILY_HOST_BINDING_MISMATCH')
        return bound.gateway()
    except Exception:
        return None
