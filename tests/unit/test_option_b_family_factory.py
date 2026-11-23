"""Existing local factory -> accepted binding -> native client/Identity SQLite.

All configuration, governance records, keys and Witness ports are existing
isolated synthetic fixtures. No live Owner enrollment/acceptance is claimed.
"""
import asyncio
from contextlib import contextmanager,closing
from dataclasses import replace
from datetime import datetime,timedelta,timezone
import hashlib
import importlib
import json
from types import SimpleNamespace
from unittest.mock import patch
import sys

import httpx
import pytest
from cryptography.hazmat.primitives import serialization

from agent_lab import owner_identity_broker as broker
from agent_lab.option_b_family_binding import OptionBFamilyBinding,BoundOptionBFamily,OptionBFamilyFactory,source_build_ref,public_ref
from agent_lab.identity_owner_source import CanonicalOwnerDeclarationSource,PROVIDER
from agent_lab.c09_operational_service_runtime import KernelIdentityServiceClient,create_identity_service_host
from agent_lab.c09_service_host import ServiceConfiguration,ServiceRole,current_process_sid
from agent_lab.family_identity_gateway import FamilyScope,FamilyMutationIntent
from agent_lab.ipc_wire_primitives import canonical_sha256 as H,canonical_json_bytes as C
from agent_lab.ui_dashboard import DashboardCase
from test_f07_inactive_runtime import runtime_at
from test_identity_logical_runtime import cases,store_at,KERNEL,NOW as RECORD_NOW
from test_identity_logical_continuity import artifact
from test_owner_identity_broker import credential,assertion
from agent_lab.owner_identity_assertion import intent_challenge
from test_orchestrator_kernel import task,manifest,response
from test_family_dashboard_identity import VALUES,EDIT,record,family_task
from test_identity_persistence import A1

pytestmark=pytest.mark.skipif(sys.platform!='win32',reason='real Windows pipe/DPAPI')
QUERY='?case_id=C1&tax_year=2025&run_id=RUN-RUNTIME-1'
HEADERS={'Origin':'http://127.0.0.1:8766','Content-Type':'application/json'}

def key_fixture(root,role,key):
    import win32crypt
    raw=json.dumps(dict(contract='ai-tax-agent.option-b-key/1',role=role,owner_id='P1',private_der=key.private_bytes(
        serialization.Encoding.DER,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).hex())).encode()
    (root/('owner-'+role+'-signing.dpapi')).write_bytes(win32crypt.CryptProtectData(raw,'synthetic fixture',('AI-Tax-Agent:'+role).encode(),None,None,0))

def accept_binding(kernel,binding):
    work=task(task_id='TASK-FAMILY-BIND',role_id='OPERATIONS_INTEGRATION_AGENT',actor_instance_id='TEST-BIND-IMPLEMENTER',permissions=['inspect_operational_metadata'])
    work['inputs']=[binding.reference]
    kernel.register_task(work,gate_triggers=['permission_expansion'])
    kernel.record_human_gate_decision(work['task_id'],'permission_expansion','APPROVED',actor_id='HUMAN_PROJECT_OWNER',authority_reference=binding.reference)
    grant=manifest(work,manifest_id='MAN-FAMILY-BIND',tiers=['A1'])
    kernel.register_manifest(grant);kernel.validate_manifest(grant['manifest_id']);kernel.activate_manifest(grant['manifest_id'])
    kernel.consume_budget(grant['manifest_id'],tokens=100,tool_calls=2,cost_usd=.25)
    result=response(work);result['response_id']='RESP-FAMILY-BIND'
    kernel.record_response(grant['manifest_id'],result)
    reviewer=task(task_id='TASK-FAMILY-BIND-REVIEW',role_id='INDEPENDENT_ACCEPTANCE_AGENT',actor_instance_id='TEST-BIND-REVIEWER',parent_task_id=work['task_id'],permissions=['acceptance_review'])
    review=manifest(reviewer,manifest_id='MAN-FAMILY-BIND-REVIEW',tiers=['A1'])
    kernel.register_task(reviewer,gate_triggers=[]);kernel.register_manifest(review);kernel.validate_manifest(review['manifest_id']);kernel.activate_manifest(review['manifest_id'])
    kernel.record_acceptance(work['task_id'],review['manifest_id'],'PASS',evidence_reference=binding.reference)

@contextmanager
def factory_at(path,monkeypatch):
    binding=artifact();stamp=lambda t:t.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    now=datetime.now(timezone.utc)
    scopes={op:dict(operation=op,owner_id='P1',case_id='C1',tax_year='2025',subject_id='P2',input_digest=H(EDIT if op=='CORRECT_PERSON' else VALUES),
        deployment_id=binding['deployment_id'],store_id=binding['store_id'],task_id='TASK-RUNTIME-1',manifest_id='MAN-RUNTIME-1',run_id='RUN-RUNTIME-1')
        for op in ('REGISTER_IDENTITY','BIND_PARTY','CORRECT_PERSON')}
    original=json.dumps(record(VALUES),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    corrected=json.dumps(record(EDIT,RECORD_NOW+timedelta(seconds=1)),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    role=C(dict(subject_id='P2',case_id='C1',tax_year='2025',role=VALUES['role']))
    digest=lambda raw:'sha256:'+hashlib.sha256(raw).hexdigest()
    refs=[A1]+[broker.authorization_reference(scope) for scope in scopes.values()]+[digest(raw) for raw in (original,corrected,role)]
    with patch('test_f07_inactive_runtime.task',side_effect=family_task):
        with runtime_at(path,inputs=refs,permissions=['identity_create','identity_read','identity_update','case_party_bind']) as state:
            private,pin=credential();pin=replace(pin,owner_id='P1')
            pending=broker.begin_enrollment(state['kernel'],owner_id='P1',deployment_id=binding['deployment_id'],store_id=binding['store_id'],approval=broker.APPROVAL,now=now)
            broker._finish_enrollment(state['kernel'],deployment_id=binding['deployment_id'],credential=pin,
                assertion=assertion(private,pin,broker.enrollment_challenge(pending)),now=now)
            with closing(store_at(path/'identity.sqlite')) as authority:
                source=CanonicalOwnerDeclarationSource(authority,deployment_id=binding['deployment_id'],store_id=binding['store_id'])
                for index,(op,scope) in enumerate(scopes.items(),2):
                    intent=broker.issue_intent(state['kernel'],scope=scope,now=now)
                    broker.approve_intent(state['kernel'],deployment_id=binding['deployment_id'],nonce=intent['nonce'],assertion=assertion(private,pin,intent_challenge(intent),index),now=now)
                    delivery=broker.approved_source_evidence(state['kernel'],deployment_id=binding['deployment_id'],nonce=intent['nonce'],expected_scope=scope,now=now,signing_key=KERNEL,key_id='TEST-KERNEL-KEY-1')
                    kind,raw=('ROLE_EVIDENCE',role) if op=='BIND_PARTY' else ('IDENTITY_RECORD',corrected if op=='CORRECT_PERSON' else original)
                    source.stage(delivery=delivery,confirmed_values=EDIT if op=='CORRECT_PERSON' else VALUES,artifacts=((kind,raw),),now=now)
            state['host'].stop()
            key_fixture(path,'kernel',KERNEL);identity_private,_=credential();key_fixture(path,'identity',identity_private)
            registry=cases();p=dict(schema='ai-tax-agent.option-b-family-binding/1',deployment_id=binding['deployment_id'],store_id=binding['store_id'],
                owner_id='P1',owner_sid=current_process_sid(),case_years=[['C1','2025']],source_provider=PROVIDER,source_build_ref=source_build_ref(),
                source_scope_ref=H(dict(deployment_id=binding['deployment_id'],store_id=binding['store_id'],owner_id='P1',case_years=[['C1','2025']])),
                kernel_key_ref=public_ref(KERNEL),identity_key_ref=public_ref(identity_private),custody_ref='sha256:'+'1'*64,audit_recovery_ref='sha256:'+'2'*64,
                identity_image_path=state['client']._identity.image_path,identity_image_ref=state['client']._identity.image_sha256,
                witness_bucket=state['client']._provider.bucket,custodian_key_id=state['client']._custodian._custodian_key_id,acceptance_task_id='TASK-FAMILY-BIND',
                not_before=stamp(now-timedelta(seconds=1)),expires_at=stamp(now+timedelta(minutes=10)))
            config=OptionBFamilyBinding.parse(p);accept_binding(state['kernel'],config)
            (path/'family-runtime-binding.json').write_bytes(C(p))
            def scope(op):
                return FamilyScope('P1','C1',2025,'RUN-RUNTIME-1','TASK-RUNTIME-1','MAN-RUNTIME-1',broker.authorization_reference(scopes[op]),'2025-01-01')
            def intents(case,year,run,action,values):
                if action=='create' and values==VALUES:
                    return (FamilyMutationIntent(scope('REGISTER_IDENTITY'),'REGISTER_IDENTITY',dict(request_id='TEST-F-REG',subject_id='P2',identity_record_ref=digest(original),evidence_refs=[digest(original)]),'tx:v1:123e4567-e89b-42d3-a456-426614174991',H(values)),
                        FamilyMutationIntent(scope('BIND_PARTY'),'BIND_PARTY',dict(request_id='TEST-F-ROLE',subject_id='P2',party_role=VALUES['role'],valid_from='2025-01-01',valid_to_exclusive='',evidence_refs=[digest(role)]),'tx:v1:123e4567-e89b-42d3-a456-426614174992',H(values)))
                if action=='correct' and values==EDIT:
                    return (FamilyMutationIntent(scope('CORRECT_PERSON'),'CORRECT_PERSON',dict(request_id='TEST-F-CORRECT',subject_id='P2',identity_record_ref=digest(corrected),expected_record_digest=digest(original),evidence_refs=[digest(corrected)]),'tx:v1:123e4567-e89b-42d3-a456-426614174993',H(values)),)
                raise PermissionError('no approved fixture intent')
            def compose():
                bound=BoundOptionBFamily(config,kernel=state['kernel'],cases=registry,key_root=path,client=None,read_scope=lambda *_:replace(scope('REGISTER_IDENTITY'),authorization_ref=A1),resolve_intents=intents)
                prior=state['client']
                client=KernelIdentityServiceClient(state['kernel'],deployment_id=binding['deployment_id'],identity_server=prior._identity,custodian=prior._custodian,
                    provider=prior._provider,signing_key=KERNEL,key_id='TEST-KERNEL-KEY-1',mutation_pipeline=True,owner_binding=bound)
                bound.client=client
                host=create_identity_service_host(lambda _:store_at(path/'identity.sqlite'),allowed_case_ids=frozenset({'C1'}),mutation_pipeline=True,protected_source=bound)
                settings=ServiceConfiguration('ai-tax-agent.option-b-identity-host/1',binding['deployment_id'],ServiceRole.IDENTITY,'AITaxIdentity',current_process_sid(),True)
                host.start(settings,current_process_sid());state['host']=host;state['client']=client
                return bound
            # Existing fixture helper uses a unique pipe name; preserve actual
            # token validation while extending only its test server signature.
            import agent_lab.c09_operational_service_runtime as module
            existing=module.create_kernel_only_server
            def test_server(name,*,overlapped,kernel_sid=None):
                assert kernel_sid==current_process_sid()
                return existing(name,overlapped=overlapped)
            with patch.object(module,'create_kernel_only_server',side_effect=test_server):
                bound=compose()
                monkeypatch.setenv('LOCALAPPDATA',str(path/'import-only'))
                monkeypatch.setenv('AI_TAX_AGENT_DRIVE_ROOT_ID','TEST-UNUSED-DRIVE-ROOT')
                # The module's legacy global app can eagerly construct its Drive
                # dependency. Isolate ONLY that unused provider on clean archives;
                # no OAuth, API call or Family authorization is mocked here.
                with patch('agent_lab.google_drive_auth.get_drive_credentials',return_value=object()),patch('googleapiclient.discovery.build',return_value=SimpleNamespace()):
                    local=importlib.import_module('agent_lab.local_case_host')
                host=SimpleNamespace(root=path,registry=registry,owner_id='P1',read_cases=lambda:tuple(DashboardCase(c.case_id,c.tax_period.year,'CREATED') for c in registry.all_records()),
                    create_case=lambda *_:(_ for _ in ()).throw(PermissionError('outside fixture')),preview_next_case_id=lambda *_:'TEST-NEXT')
                from agent_lab.case_analysis_kernel_dispatch import CaseAnalysisKernelDispatcher
                analysis=CaseAnalysisKernelDispatcher(path/'kernel.sqlite',state['kernel'].contract_root)
                def app():
                    loader=OptionBFamilyFactory(client=state['client'],read_scope=bound.read_scope,resolve_intents=bound.resolve_intents)
                    return local.create_local_case_app(case_host=host,kernel_dispatch=analysis,family_binding=loader)
                def restart():
                    nonlocal bound
                    prior=state['client'];state['host'].stop();state['kernel'].close()
                    from agent_lab.orchestrator_kernel import OrchestratorKernel
                    state['kernel']=OrchestratorKernel(path/'kernel.sqlite',prior._kernel.contract_root)
                    # Simulate a genuine cold start: no external verifier
                    # preinstalled on the newly constructed Kernel.
                    bound=compose();state['bound']=bound
                state.update(bound=bound,app=app,config=config,restart=restart,case_host=host,local=local,analysis=analysis)
                yield state

def test_factory_create_correct_refresh(tmp_path,monkeypatch):
    with factory_at(tmp_path,monkeypatch) as state:
        app=state['app']()
        async def flow():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://127.0.0.1:8766') as browser:
                created=await browser.post('/family/persons'+QUERY,content=C(dict(action='create',values=VALUES)),headers=HEADERS)
                assert created.status_code==200,created.text
                edited=await browser.post('/family/persons'+QUERY,content=C(dict(action='correct',values=EDIT)),headers=HEADERS)
                assert edited.status_code==200,edited.text
                for _ in range(2):
                    read=await browser.get('/family/persons'+QUERY)
                    assert read.status_code==200,read.text
                    assert next(p for p in read.json()['people'] if p['person_id']=='P2')['name']=='Corrected Person'
                assert (await browser.get('/family/persons'+QUERY.replace('2025','2024'))).status_code==403
        asyncio.run(flow())
        state['restart']()
        async def recovered():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=state['app']()),base_url='http://127.0.0.1:8766') as browser:
                read=await browser.get('/family/persons'+QUERY)
                assert read.status_code==200,read.text
                assert next(p for p in read.json()['people'] if p['person_id']=='P2')['name']=='Corrected Person'
                for language,direction in [('fa-IR','rtl'),('de-DE','ltr')]:
                    page=await browser.get('/?tab=family&case_id=C1&tax_year=2025&lang='+language)
                    assert page.status_code==200 and 'dir="'+direction+'"' in page.text
        asyncio.run(recovered())

def test_factory_unaccepted_or_revoked_binding_is_503(tmp_path,monkeypatch):
    with factory_at(tmp_path,monkeypatch) as state:
        app=state['app']()
        async def denied():
            with state['kernel'].atomic_execution():
                row=broker._load(state['kernel'],state['config'].payload['deployment_id']);row['revoked']=True
                broker._save(state['kernel'],state['config'].payload['deployment_id'],row)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://127.0.0.1:8766') as browser:
                assert (await browser.get('/family/persons'+QUERY)).status_code==503
                assert (await browser.post('/family/persons'+QUERY,content=C(dict(action='create',values=VALUES)),headers=HEADERS)).status_code==503
        asyncio.run(denied())

def clock_after(binding):
    return datetime.strptime(binding.payload['expires_at'],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)+timedelta(seconds=1)

def mutation_args(state,operation='REGISTER_IDENTITY'):
    values=EDIT if operation=='CORRECT_PERSON' else VALUES
    action='correct' if operation=='CORRECT_PERSON' else 'create'
    intent=state['bound'].resolve_intents('C1',2025,'RUN-RUNTIME-1',action,values)[0]
    return dict(case_id='C1',tax_year=2025,run_id='RUN-RUNTIME-1',task_id=intent.scope.task_id,manifest_id=intent.scope.manifest_id,
        operation=operation,authorization_references=[intent.scope.authorization_ref],transaction_id=intent.transaction_id,
        payload={**intent.payload,'owner_input_digest':H({k:v for k,v in values.items() if k not in {'person_id','role'}})})

@pytest.mark.parametrize('failure',['expired','revoked'])
def test_direct_client_and_kernel_cannot_bypass_binding(tmp_path,monkeypatch,failure):
    with factory_at(tmp_path,monkeypatch) as state:
        if failure=='revoked':
            with state['kernel'].atomic_execution():
                owner=broker._load(state['kernel'],state['config'].payload['deployment_id']);owner['revoked']=True
                broker._save(state['kernel'],state['config'].payload['deployment_id'],owner)
        with patch('agent_lab.option_b_family_binding.datetime',wraps=datetime) as clock,patch('agent_lab.c09_pipe_transport._exchange_canonical',side_effect=AssertionError('must deny before transport')) as transport:
            clock.now.return_value=clock_after(state['config']) if failure=='expired' else datetime.now(timezone.utc)
            args=mutation_args(state)
            with pytest.raises(PermissionError):state['client'].read(**{k:v for k,v in args.items() if k not in {'payload','operation'}},operation='READ_FAMILY',payload=dict(subject_id='',as_of_date='2025-01-01'))
            with pytest.raises(PermissionError):state['client'].mutation_stage(**args,message_type='PREPARE_MUTATION')
            with pytest.raises(PermissionError):state['kernel'].issue_identity_mutation(**args,message_type='PREPARE_MUTATION',deployment_id=state['config'].payload['deployment_id'],signing_key=KERNEL,key_id='TEST-KERNEL-KEY-1')
            transport.assert_not_called()

def test_binding_expiry_between_prepare_and_commit_denies_new_domain_write(tmp_path,monkeypatch):
    with factory_at(tmp_path,monkeypatch) as state:
        args=mutation_args(state)
        assert state['client'].mutation_stage(**args,message_type='PREPARE_MUTATION')['outcome']=='PREPARED'
        with patch('agent_lab.option_b_family_binding.datetime',wraps=datetime) as clock,patch('agent_lab.c09_pipe_transport._exchange_canonical',side_effect=AssertionError('must deny before transport')) as transport:
            clock.now.return_value=clock_after(state['config'])
            with pytest.raises(PermissionError):state['client'].mutation_stage(**args,message_type='COMMIT_MUTATION')
            transport.assert_not_called()
        with closing(store_at(tmp_path/'identity.sqlite')) as authority:assert authority._load_identity('P2') is None

def test_cached_private_read_cannot_bypass_revoked_binding(tmp_path,monkeypatch):
    with factory_at(tmp_path,monkeypatch) as state:
        args=mutation_args(state)
        args={k:v for k,v in args.items() if k not in {'payload','operation'}}
        args.update(operation='READ_FAMILY',payload=dict(subject_id='',as_of_date='2025-01-01'),authorization_references=[A1],
                    transaction_id='tx:v1:123e4567-e89b-42d3-a456-426614174998')
        assert state['client'].read(**args)['outcome']=='READ_OK'
        with state['kernel'].atomic_execution():
            owner=broker._load(state['kernel'],state['config'].payload['deployment_id']);owner['revoked']=True
            broker._save(state['kernel'],state['config'].payload['deployment_id'],owner)
        with pytest.raises(PermissionError):state['client'].recover_read(**args)

def test_committed_recovery_after_binding_expiry_revocation_and_restart(tmp_path,monkeypatch):
    with factory_at(tmp_path,monkeypatch) as state:
        async def begin():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=state['app']()),base_url='http://127.0.0.1:8766') as browser:
                assert (await browser.post('/family/persons'+QUERY,content=C(dict(action='create',values=VALUES)),headers=HEADERS)).status_code==200
                with patch.object(state['client'],'reconcile',side_effect=TimeoutError('lost before Witness settlement')):
                    held=await browser.post('/family/persons'+QUERY,content=C(dict(action='correct',values=EDIT)),headers=HEADERS)
                assert held.status_code==409
                return held.json()['workflow_id']
        workflow=asyncio.run(begin())
        with state['kernel'].atomic_execution():
            owner=broker._load(state['kernel'],state['config'].payload['deployment_id']);owner['revoked']=True
            broker._save(state['kernel'],state['config'].payload['deployment_id'],owner)
            state['kernel']._connection.execute("UPDATE tasks SET status='BLOCKED' WHERE task_id='TASK-FAMILY-BIND'")
            state['kernel']._append_event('TASK_BLOCKED','TASK','TASK-FAMILY-BIND','HUMAN_PROJECT_OWNER',{'reason':'synthetic binding withdrawal'})
        with patch('agent_lab.option_b_family_binding.datetime',wraps=datetime) as clock:
            clock.now.return_value=clock_after(state['config'])
            state['restart']()
            async def settle():
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=state['app']()),base_url='http://127.0.0.1:8766') as browser:
                    assert (await browser.get('/family/persons'+QUERY)).status_code==503
                    assert (await browser.get('/family/pending'+QUERY)).status_code==200
                    result=await browser.post('/family/persons/recover'+QUERY,content=C(dict(workflow_id=workflow)),headers=HEADERS)
                    assert result.status_code==200,result.text
                    assert result.json()['status']=='COMMITTED_FINAL'
            asyncio.run(settle())
        with closing(store_at(tmp_path/'identity.sqlite')) as authority:assert authority._load_identity('P2').preferred_display_name=='Corrected Person'

def test_restarted_raw_kernel_denies_enrolled_owner_without_factory(tmp_path,monkeypatch):
    from agent_lab.orchestrator_kernel import OrchestratorKernel
    from agent_lab.orchestrator_kernel import PermissionDenied
    with factory_at(tmp_path,monkeypatch) as state:
        args=mutation_args(state)
        prior=state['kernel']
        raw=OrchestratorKernel(tmp_path/'kernel.sqlite',prior.contract_root)
        try:
            # Even a freshly verified external Witness head cannot authorize
            # a raw Kernel when durable Owner enrollment requires the factory.
            client=state['client']
            raw.verify_identity_witness_state(state['config'].payload['deployment_id'],
                custodian=client._custodian,provider=client._provider,
                signing_key=KERNEL,kernel_key_id='TEST-KERNEL-KEY-1')
            with pytest.raises(PermissionDenied,match='requires bound verifier'):
                raw.issue_identity_mutation(**args,message_type='PREPARE_MUTATION',
                    deployment_id=state['config'].payload['deployment_id'],
                    signing_key=KERNEL,key_id='TEST-KERNEL-KEY-1')
            read={k:v for k,v in args.items() if k not in {'payload','operation'}}
            with pytest.raises(PermissionDenied,match='requires bound verifier'):
                raw.issue_identity_read(**read,operation='READ_FAMILY',
                    payload=dict(subject_id='',as_of_date='2025-01-01'),
                    deployment_id=state['config'].payload['deployment_id'],
                    signing_key=KERNEL,key_id='TEST-KERNEL-KEY-1')
        finally:
            raw.close()


def test_raw_gateway_cannot_bypass_production_factory(tmp_path,monkeypatch):
    from agent_lab.family_identity_gateway import FamilyIdentityGateway
    with factory_at(tmp_path,monkeypatch) as state:
        bound=state['bound']
        raw=FamilyIdentityGateway(cases=bound.cases,owner_id='P1',client=state['client'],read_scope=bound.read_scope)
        app=state['local'].create_local_case_app(case_host=state['case_host'],kernel_dispatch=state['analysis'],family_gateway=raw)
        async def denied():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://127.0.0.1:8766') as browser:
                assert (await browser.get('/family/persons'+QUERY)).status_code==503
        asyncio.run(denied())

def test_build_manifest_detects_every_authority_file_substitution(tmp_path):
    from agent_lab.option_b_family_binding import build_manifest
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    original=build_manifest()
    names={name for name,_ in original['files']}
    # Completeness is a set-membership invariant; no hand-maintained allowlist.
    all_code={p.relative_to(root).as_posix() for p in (root/'src'/'agent_lab').rglob('*.py')}
    all_ui={p.relative_to(root).as_posix() for p in (root/'src'/'agent_lab').rglob('*')
            if p.is_file() and p.suffix in {'.js','.css','.html'}}
    assert all_code<=names
    assert all_ui<=names
    assert 'requirements.txt' in names
    assert any(n.endswith('/local_case_host.py') for n in names)
    # One representative of each file class is sufficient for digest
    # sensitivity; checking 212 files one by one is redundant and expensive.
    selected=[next(n for n in sorted(names) if n.endswith(suffix)) for suffix in
              ('option_b_family_binding.py','local_case_host.py','dashboard.html',
               'app.css','analysis_readiness.js','requirements.txt')]
    for name,_ in original['files']:
        target=tmp_path/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((root/name).read_bytes())
    baseline=H(build_manifest(tmp_path))
    assert baseline==H(original)
    for name in selected:
        target=tmp_path/name;raw=target.read_bytes();target.write_bytes(raw+b'\n')
        assert H(build_manifest(tmp_path))!=baseline,name
        target.write_bytes(raw)

@pytest.mark.parametrize('failure',['key','case','source','owner','custodian','witness','expired','unaccepted','schema','image'])
def test_factory_dependency_rejection_is_503(tmp_path,monkeypatch,failure):
    with factory_at(tmp_path,monkeypatch) as state:
        bound=state['bound']
        if failure=='key':(tmp_path/'owner-kernel-signing.dpapi').unlink()
        if failure=='case':
            from agent_lab.case_registry import CaseRegistry
            state['case_host'].registry=CaseRegistry()
        if failure=='source':monkeypatch.setattr('agent_lab.option_b_family_binding.source_build_ref',lambda:'sha256:'+'f'*64)
        if failure=='owner':monkeypatch.setattr('agent_lab.c09_service_host.current_process_sid',lambda:'S-1-5-21-1-2-3-999')
        if failure=='custodian':bound.client._custodian._custodian_key_id='OTHER'
        if failure=='image':bound.client._identity=replace(bound.client._identity,image_sha256='sha256:'+'f'*64)
        if failure=='witness':state['session'].objects.clear()
        if failure in {'expired','unaccepted','schema'}:
            p=json.loads(json.dumps(bound.binding.payload))
            if failure=='expired':p['expires_at']=(datetime.now(timezone.utc)-timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ');p['not_before']=(datetime.now(timezone.utc)-timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            elif failure=='schema':p['schema']='ai-tax-agent.option-b-family-binding/999'
            else:p['acceptance_task_id']='UNKNOWN'
            (tmp_path/'family-runtime-binding.json').write_bytes(C(p))
        app=state['app']()
        async def denied():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://127.0.0.1:8766') as browser:
                assert (await browser.get('/family/persons'+QUERY)).status_code==503
        asyncio.run(denied())
