"""T1-T7: canonical temporary SQLite and synthetic Drive only; no app startup."""
import ast
from copy import deepcopy
import json
from pathlib import Path
from threading import RLock
from types import ModuleType,SimpleNamespace
from unittest.mock import Mock
import sys

import pytest
from agent_lab.case_persistence import SQLiteCasePersistence,CasePersistenceError
from agent_lab.case_document_registry import read_registry,reconcile,LEGACY_COLUMNS,EXTENSIONS
from test_case_persistence import KEY,_case

CASE='CASE-2025-0001';OTHER='CASE-2025-0002';OWNER='PERSON-A'
MIME='application/vnd.google-apps.folder'


@pytest.fixture
def host_module(monkeypatch):
    # Execute the actual implementation while excluding only module-level ASGI
    # startup, which would otherwise open the Owner's real DB/OAuth at import.
    path=Path(__file__).parents[2]/'src/agent_lab/local_case_host.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    tree.body=[node for node in tree.body if not (isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='app' for t in node.targets))]
    module=ModuleType('agent_lab._document_registry_test_host');module.__file__=str(path)
    monkeypatch.setitem(sys.modules,module.__name__,module)
    exec(compile(tree,str(path),'exec'),module.__dict__)
    monkeypatch.setattr(module,'get_drive_credentials',lambda:object())
    return module


class Drive:
    def __init__(self):
        self.items={};self.data={};self.writes=[];self.failure=None
        for case in (CASE,OTHER):
            root='ROOT-'+case;self.folder(root,case,'system')
            for name in ('Documents','Tax_Categories','Evidence','Audit','Calculations','Reports'):
                self.folder(case+'-'+name,name,root)
    def folder(self,id,name,parent):self.items[id]={'id':id,'name':name,'parents':[parent],'trashed':False,'mimeType':MIME}
    def document(self,id='f1',case=CASE,location='Documents',content=b'SYNTHETIC-PDF'):
        self.items[id]={'id':id,'name':id+'.pdf','parents':[case+'-'+location],'trashed':False,'mimeType':'application/pdf','size':str(len(content))};self.data[id]=content
    def files(self):return self
    def get(self,fileId,fields):return SimpleNamespace(execute=lambda:deepcopy(self.items[fileId]))
    def list(self,**kwargs):
        parent=kwargs['q'].split("'")[1]
        def execute():
            if self.failure==parent:raise RuntimeError('synthetic listing failure')
            return {'files':[deepcopy(v) for v in self.items.values() if v['parents']==[parent] and not v['trashed']]}
        return SimpleNamespace(execute=execute)
    def create(self,body,media_body,fields):
        def execute():
            self.writes.append('create');id='uploaded'
            self.items[id]={'id':id,**body,'trashed':False,'mimeType':media_body.mimetype(),'size':str(media_body.size())}
            self.data[id]=media_body.getbytes(0,media_body.size());return deepcopy(self.items[id])
        return SimpleNamespace(execute=execute)
    def update(self,fileId,body,fields):
        def execute():self.writes.append('update');self.items[fileId].update(body);return deepcopy(self.items[fileId])
        return SimpleNamespace(execute=execute)
    def get_media(self,fileId):return SimpleNamespace(content=self.data[fileId])


@pytest.fixture
def setup(host_module,monkeypatch,tmp_path):
    p=SQLiteCasePersistence(tmp_path/'case.sqlite',integrity_key=KEY)
    from agent_lab.storage_provisioning import DurableStorageProvisioningAdapter
    from agent_lab.case_registry import StorageScopeReference,TaxPeriod
    creator=SimpleNamespace(create_case_scope=lambda period,case:StorageScopeReference('google_drive','ROOT-'+case))
    for case in (CASE,OTHER):
        DurableStorageProvisioningAdapter(p,creator).provision_case_scope(owner_id=OWNER,tax_period=TaxPeriod('CALENDAR_YEAR',2025),case_id=case,request_id='CREATE-'+case)
        p.register_case(*_case(case,OWNER,2025),ui_owner_id=OWNER)
    host=host_module.LocalCaseHost.__new__(host_module.LocalCaseHost)
    host._lock=RLock();host.persistence=p;host.owner_id=OWNER;host.root=tmp_path;host._reload=lambda:None
    drive=Drive();monkeypatch.setattr(host_module,'build',lambda *args,**kwargs:drive)
    yield host,drive,p
    p.close()


def rows(host):return host.list_case_document_registry(CASE,2025)['documents']


def test_t1_t2_t4_move_preserves_identity_history_and_pending_count(setup):
    h,d,p=setup;d.document()
    assert len(h.list_case_documents(CASE,2025)['files'])==1
    original=dict(rows(h)[0]);d.items['f1']['parents']=[CASE+'-Tax_Categories']
    assert h.list_case_documents(CASE,2025)['files']==[]
    current=rows(h)[0]
    assert current['drive_file_id']==original['drive_file_id']=='f1'
    assert current['case_id']==CASE and current['tax_year']==2025
    assert current['registry_state']=='ACTIVE_ANALYZED'
    old_history=json.loads(original['history_json']);history=json.loads(current['history_json'])
    assert history[:len(old_history)]==old_history and len(history)==len(old_history)+1
    assert d.writes==[]


def test_t3_inactive_is_retained_but_not_active(setup):
    h,d,p=setup;d.document(location='Tax_Categories');h.list_case_documents(CASE,2025)
    d.folder(CASE+'-Deleted_Documents','Deleted_Documents','ROOT-'+CASE)
    d.items['f1']['parents']=[CASE+'-Deleted_Documents']
    view=h.list_case_document_registry(CASE,2025)
    assert len(view['documents'])==1 and view['documents'][0]['registry_state']=='DELETED_ANALYZED'
    assert view['active_documents']==() and len(view['inactive_documents'])==1
    assert h.list_case_documents(CASE,2025)['files']==[] and d.writes==[]


def test_t5_wrong_year_owner_and_cross_case_reassignment_denied(setup):
    h,d,p=setup;d.document();h.list_case_documents(CASE,2025)
    with pytest.raises(PermissionError):h.list_case_documents(CASE,2024)
    with pytest.raises(PermissionError):read_registry(p,owner_id='WRONG',case_id=CASE,tax_year=2025)
    d.items['f1']['parents']=[OTHER+'-Documents']
    with pytest.raises(PermissionError):h.list_case_documents(OTHER,2025)
    assert p._db.execute('SELECT count(*) FROM case_document_index WHERE case_id=?',(OTHER,)).fetchone()[0]==0
    assert p._db.execute('SELECT case_id FROM case_document_index WHERE drive_file_id=?',('f1',)).fetchone()[0]==CASE


def test_t6_upload_preview_and_explicit_pending_trash(setup,monkeypatch):
    h,d,p=setup
    class Download:
        def __init__(self,buffer,request):self.buffer=buffer;self.request=request
        def next_chunk(self):self.buffer.write(self.request.content);return None,True
    monkeypatch.setattr('googleapiclient.http.MediaIoBaseDownload',Download)
    result=h.upload_case_document(CASE,2025,'new.pdf',b'SYNTHETIC-ONLY')
    assert result['document_id']=='uploaded'
    metadata,content=h.get_case_document(CASE,2025,'uploaded')
    assert content==b'SYNTHETIC-ONLY' and metadata['id']=='uploaded'
    assert h.trash_case_document(CASE,2025,'uploaded')['deleted']
    assert h.list_case_documents(CASE,2025)['files']==[] and rows(h)==()
    assert p._db.execute("SELECT COUNT(*) FROM case_audit WHERE action='PENDING_DOCUMENT_TRASHED'").fetchone()[0]==1


def test_t7_absence_is_unresolved_not_deletion(setup):
    h,d,p=setup;d.document();h.list_case_documents(CASE,2025)
    old=json.loads(rows(h)[0]['history_json'])
    d.items['f1']['parents']=['outside-this-case']
    assert h.list_case_documents(CASE,2025)['files']==[]
    view=h.list_case_document_registry(CASE,2025);current=view['documents'][0]
    assert current['source_status']=='UNRESOLVED' and current['registry_state']=='PENDING'
    assert not view['registry_complete'] and view['active_documents']==()
    assert json.loads(current['history_json'])[:len(old)]==old


@pytest.mark.parametrize('failure',['duplicate-folder','duplicate-file','partial-list','wrong-parent','pending-only-sync','invalid-size'])
def test_t7_bad_inventory_rolls_back_without_loss(setup,failure):
    h,d,p=setup;d.document();h.list_case_documents(CASE,2025);before=dict(rows(h)[0])
    if failure=='duplicate-folder':d.folder('duplicate','Documents','ROOT-'+CASE)
    elif failure=='duplicate-file':
        original=d.list
        def duplicate(**kwargs):
            if kwargs['q'].split("'")[1]==CASE+'-Tax_Categories':return SimpleNamespace(execute=lambda:{'files':[deepcopy(d.items['f1'])]})
            return original(**kwargs)
        d.list=duplicate
    elif failure=='partial-list':d.failure=CASE+'-Tax_Categories'
    elif failure=='invalid-size':d.items['f1']['size']=True
    elif failure=='wrong-parent':
        original=d.list
        def wrong(**kwargs):
            if kwargs['q'].split("'")[1]==CASE+'-Documents':
                item=deepcopy(d.items['f1']);item['parents']=['ROOT-'+OTHER]
                return SimpleNamespace(execute=lambda:{'files':[item]})
            return original(**kwargs)
        d.list=wrong
    with pytest.raises((ValueError,RuntimeError)):
        if failure=='pending-only-sync':h._sync_document_index(CASE,2025,{'case_id':CASE,'tax_year':2025,'files':[]})
        else:h.list_case_documents(CASE,2025)
    assert dict(p._db.execute('SELECT * FROM case_document_index').fetchone())==before


def test_analyzed_history_cannot_be_trashed_after_unapproved_return_to_pending(setup):
    h,d,p=setup;d.document(location='Tax_Categories');h.list_case_documents(CASE,2025)
    d.items['f1']['parents']=[CASE+'-Documents']
    with pytest.raises(PermissionError):h.trash_case_document(CASE,2025,'f1')
    assert d.writes==[] and d.items['f1']['trashed'] is False


def test_legacy_migration_restart_and_unchanged_read_are_safe(setup,tmp_path):
    h,d,p=setup
    p._db.execute('CREATE TABLE case_document_index(case_id TEXT,tax_year INTEGER,drive_file_id TEXT,name TEXT,mime_type TEXT,size INTEGER,indexed_at TEXT,PRIMARY KEY(case_id,drive_file_id))')
    p._db.execute('INSERT INTO case_document_index VALUES(?,?,?,?,?,?,?)',(CASE,2025,'f1','old.pdf','application/pdf',1,'2020-01-01T00:00:00Z'));p._db.commit()
    d.document();h.list_case_documents(CASE,2025);record=dict(rows(h)[0])
    assert json.loads(record['history_json'])[0]['before']['indexed_at']=='2020-01-01T00:00:00Z'
    count=p._db.execute('SELECT count(*) FROM case_audit').fetchone()[0]
    h.list_case_documents(CASE,2025)
    assert p._db.execute('SELECT count(*) FROM case_audit').fetchone()[0]==count
    reopened=SQLiteCasePersistence(p.path,integrity_key=KEY)
    try:assert dict(read_registry(reopened,owner_id=OWNER,case_id=CASE,tax_year=2025)[0])==record
    finally:reopened.close()


@pytest.mark.parametrize('attack',['state','history','row-delete'])
def test_tampering_fails_closed(setup,attack):
    h,d,p=setup;d.document();h.list_case_documents(CASE,2025)
    if attack=='state':p._db.execute("UPDATE case_document_index SET registry_state='ACTIVE_ANALYZED'")
    elif attack=='history':p._db.execute("UPDATE case_document_index SET history_json='[]'")
    else:p._db.execute('DELETE FROM case_document_index')
    p._db.commit()
    with pytest.raises(ValueError,match='integrity|completeness'):h.list_case_documents(CASE,2025)


@pytest.mark.parametrize('legacy',[True,False])
def test_existing_case_snapshot_restore_accepts_legacy_and_current_rows(setup,legacy):
    from agent_lab.case_backup_sqlite import export_case_state
    from agent_lab.case_backup_restore import import_snapshot
    h,d,p=setup;d.document()
    if legacy:
        p._db.execute('CREATE TABLE case_document_index(case_id TEXT,tax_year INTEGER,drive_file_id TEXT,name TEXT,mime_type TEXT,size INTEGER,indexed_at TEXT,PRIMARY KEY(case_id,drive_file_id))')
        p._db.execute('INSERT INTO case_document_index VALUES(?,?,?,?,?,?,?)',(CASE,2025,'f1','f1.pdf','application/pdf',13,'2020-01-01T00:00:00Z'));p._db.commit()
    else:h.list_case_documents(CASE,2025)
    blob,_=export_case_state(p,OWNER,CASE,2025)
    state=json.loads(blob)
    before=[dict(r) for r in p._db.execute('SELECT * FROM case_document_index')]
    bundle={'state':state,'manifest':{'documents':[{'id':'f1'}]},'record':{'backup_id':'SYNTHETIC-BACKUP','manifest_digest':'synthetic-only'}}
    import_snapshot(h,bundle,storage_root_id=state['storage_root_id']+'-RESTORED',document_ids={'f1':'restored-file-id'},dry_run=True)
    assert [dict(r) for r in p._db.execute('SELECT * FROM case_document_index')]==before
    p._verify_all();p._verify_anchor()


def test_unresolved_and_lifecycle_records_block_incomplete_backup_and_empty_delete(setup):
    from agent_lab.case_backup_preflight import verify_case_backup_source
    from agent_lab.empty_case_preflight import inspect_empty_case,EmptyCaseBlocked
    h,d,p=setup;d.document(location='Tax_Categories')
    with pytest.raises(ValueError,match='extended backup'):verify_case_backup_source(h,CASE,2025)
    d.items['f1']['parents']=['outside'];h.list_case_documents(CASE,2025)
    with pytest.raises(EmptyCaseBlocked,match='registered or unresolved'):
        inspect_empty_case(p,d,owner_id=OWNER,case_id=CASE,tax_year=2025)
    with pytest.raises(CasePersistenceError,match='registered or unresolved'):
        p.delete_verified_empty_case(owner_id=OWNER,case_id=CASE,tax_year=2025,storage_root_id='ROOT-'+CASE)


def test_registry_update_failure_rolls_back_metadata_history_and_audit(setup,monkeypatch):
    h,d,p=setup;d.document();h.list_case_documents(CASE,2025);before=dict(rows(h)[0])
    count=p._db.execute('SELECT count(*) FROM case_audit').fetchone()[0]
    d.items['f1']['parents']=[CASE+'-Tax_Categories']
    monkeypatch.setattr(p,'_audit',Mock(side_effect=RuntimeError('injected audit failure')))
    with pytest.raises(RuntimeError,match='audit failure'):h.list_case_documents(CASE,2025)
    assert dict(p._db.execute('SELECT * FROM case_document_index').fetchone())==before
    assert p._db.execute('SELECT count(*) FROM case_audit').fetchone()[0]==count
    p._verify_all();p._verify_anchor()
