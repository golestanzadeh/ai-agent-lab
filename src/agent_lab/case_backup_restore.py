"""Selected-version Drive API restore using canonical case SQLite and provisioning.

No source documents, backup version or audit history are overwritten. Callers
must have explicit case-specific lifecycle authority; this module adds none.
"""
from copy import deepcopy
from hashlib import sha256
import json

from agent_lab.case_backup_registry import list_reserved_backups
from agent_lab.case_backup_sqlite import TABLES
from agent_lab.case_backup_drive_writer import _upload_verified
from agent_lab.case_registry import StorageScopeReference, TaxPeriod
from agent_lab.google_drive_provisioning import GoogleDriveStorageScopeCreator
from agent_lab.case_creation_workflow import InMemoryAuditSink


def _json(raw):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate backup JSON field')
            result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs)


def children(drive,parent):
    result=[];token=None;seen=set()
    while True:
        page=drive.files().list(q=f"'{parent}' in parents",fields='nextPageToken,files(id,name,mimeType,parents,trashed,size)',pageSize=1000,pageToken=token).execute()
        result.extend(page.get('files',[]));token=page.get('nextPageToken')
        if not token:return result
        if token in seen:raise ValueError('Repeated Drive page')
        seen.add(token)


def load_selected_snapshot(host,drive,*,case_id,tax_year,backup_id):
    """Read exact registered version and every byte; return protected RAM only."""
    rows=[r for r in list_reserved_backups(host.persistence,owner_id=host.owner_id,case_id=case_id) if r['backup_id']==backup_id]
    if len(rows)!=1:raise ValueError('Selected backup missing or ambiguous')
    record=rows[0]
    if record['tax_year']!=tax_year:raise ValueError('Backup year mismatch')
    import os
    root=os.environ['AI_TAX_AGENT_DRIVE_ROOT_ID']
    current=record['folder_id']
    for expected in (backup_id,record['identity'],'Case_Backups'):
        meta=drive.files().get(fileId=current,fields='id,name,mimeType,parents,trashed').execute()
        if meta['name']!=expected or meta['mimeType']!='application/vnd.google-apps.folder' or meta['trashed'] or len(meta.get('parents',[]))!=1:
            raise ValueError('Backup ancestry mismatch')
        current=meta['parents'][0]
    if current!=root:raise ValueError('Backup outside configured root')
    inventory=children(drive,record['folder_id'])
    manifests=[v for v in inventory if v['name']=='manifest.json' and not v['trashed']]
    if len(manifests)!=1:raise ValueError('Manifest missing or ambiguous')
    raw=drive.files().get_media(fileId=manifests[0]['id']).execute()
    if len(raw)>1024*1024 or sha256(raw).hexdigest()!=record['manifest_digest']:raise ValueError('Manifest integrity failure')
    manifest=_json(raw)
    if (manifest['schema']!='case-document-snapshot/1' or manifest['backup_id']!=backup_id or
        manifest['case_identity']!=record['identity'] or manifest['case_id']!=case_id or manifest['tax_year']!=tax_year):
        raise ValueError('Manifest scope mismatch')
    state_info=manifest['sqlite_snapshot']
    expected={manifests[0]['id'],state_info['drive_id'],*(d['backup_drive_id'] for d in manifest['documents'])}
    if len(expected)!=2+len(manifest['documents']) or {v['id'] for v in inventory}!=expected or any(v['trashed'] or v['parents']!=[record['folder_id']] for v in inventory):
        raise ValueError('Unexpected backup inventory')
    def content(info,file_id):
        if type(info['size']) is not int or not 0<info['size']<=25*1024*1024:raise ValueError('Backup size outside bound')
        raw=drive.files().get_media(fileId=file_id).execute()
        if len(raw)!=info['size'] or sha256(raw).hexdigest()!=info['sha256']:raise ValueError('Backup content integrity failure')
        return raw
    state=_json(content(state_info,state_info['drive_id']))
    if (state['schema']!='case-sqlite-snapshot/1' or state['case_id']!=case_id or state['tax_year']!=tax_year or
        state['owner_id']!=host.owner_id or state['storage_root_id']!=manifest['source_root_id'] or set(state['tables'])!=set(TABLES)):
        raise ValueError('SQLite snapshot scope mismatch')
    if any(len(state['tables'][t])!=1 for t in TABLES[:4]) or state['tables']['durable_run'] or state['tables']['mutation_request']:
        raise ValueError('Unsupported snapshot dependencies')
    for table,rows in state['tables'].items():
        if any(v.get('case_id')!=case_id for v in rows):raise ValueError('Cross-case backup row')
    indexed={v['drive_file_id']:v for v in state['tables']['case_document_index']}
    docs=manifest['documents']
    if set(indexed)!={d['id'] for d in docs} or len({d['name'] for d in docs})!=len(docs):raise ValueError('Snapshot document association mismatch')
    payloads={}
    for doc in docs:
        item=indexed[doc['id']]
        if item['name']!=doc['name'] or item['tax_year']!=tax_year or int(item['size'])!=doc['size']:raise ValueError('Snapshot document metadata mismatch')
        payloads[doc['id']]=content(doc,doc['backup_drive_id'])
    return {'record':record,'manifest':manifest,'state':state,'contents':payloads}


def import_snapshot(host,bundle,*,storage_root_id,document_ids,dry_run=False):
    """Atomic row restore with new Drive references; dry-run always rolls back."""
    p=host.persistence;s=bundle['state'];case=s['case_id'];tables=deepcopy(s['tables'])
    if s['owner_id']!=host.owner_id:raise PermissionError('Owner mismatch')
    if set(document_ids)!={d['id'] for d in bundle['manifest']['documents']} or len(set(document_ids.values()))!=len(document_ids):raise ValueError('Invalid document remapping')
    from agent_lab.case_document_registry import remap_backup_row,ensure_schema,LEGACY_COLUMNS,EXTENSIONS,seal_collection
    tables['case_document_index']=[remap_backup_row(p,row,document_ids[row['drive_file_id']]) for row in tables['case_document_index']]
    original_root=tables['case_record'][0]['storage_root_id']
    if storage_root_id!=original_root:
        row=tables['case_record'][0];row['storage_root_id']=storage_root_id
        row['digest']=p._mac(p._case_payload(p._record(row)))
        row=tables['storage_provisioning'][0];row['storage_root_id']=storage_root_id
        row['digest']=p._mac({k:v for k,v in row.items() if k!='digest'})
    with host._lock,p._lock:
        p._verify_all();p._verify_anchor()
        exists=p._db.execute('SELECT 1 FROM case_record WHERE case_id=?',(case,)).fetchone() is not None
        if exists and not dry_run:raise ValueError('Restore never overwrites active case')
        p._db.execute('BEGIN IMMEDIATE')
        try:
            ensure_schema(p)
            if exists:
                for table in reversed(TABLES):p._db.execute(f'DELETE FROM {table} WHERE case_id=?',(case,))
            for table in TABLES:
                columns={v['name'] for v in p._db.execute(f'PRAGMA table_info({table})')}
                for row in tables[table]:
                    if table=='case_document_index':
                        if not LEGACY_COLUMNS<=set(row)<=columns or columns-set(row)-set(EXTENSIONS):raise ValueError('Snapshot document schema mismatch')
                    elif set(row)!=columns:raise ValueError('Snapshot schema mismatch')
                    names=list(row)
                    p._db.execute(f'INSERT INTO {table} ({",".join(names)}) VALUES ({",".join("?" for _ in names)})',[row[k] for k in names])
            if not exists:p._audit('CASE_REGISTERED',case,p._mac({'restore_backup_id':bundle['record']['backup_id'],'manifest_digest':bundle['record']['manifest_digest']}))
            seal_collection(p,case)
            p._verify_all()
            if dry_run:
                p._db.rollback();p._verify_all();p._verify_anchor()
            else:
                p._db.commit();p._write_anchor();p._verify_anchor()
        except BaseException:
            if p._db.in_transaction:p._db.rollback()
            raise


def restore_selected_snapshot(host,drive,bundle):
    """Reuse existing scope creator, upload from verified backup, then commit rows."""
    import os
    s=bundle['state'];case=s['case_id'];year=s['tax_year']
    with host._lock,host.persistence._lock:
        host.persistence._verify_all();host.persistence._verify_anchor()
        if host.persistence._db.execute('SELECT 1 FROM case_record WHERE case_id=?',(case,)).fetchone():raise ValueError('Active case blocks restore')
        creator=GoogleDriveStorageScopeCreator(drive_service=drive,system_root_id=os.environ['AI_TAX_AGENT_DRIVE_ROOT_ID'],journal_path=host.root/'drive-api-provisioning.json',audit=InMemoryAuditSink())
        scope=creator.create_case_scope(TaxPeriod('CALENDAR_YEAR',year),case)
        journal=json.loads(creator.path.read_text())
        docs_root=journal['folders'][f'Tax_Years/{year}/Cases/{case}/Documents']
        if children(drive,docs_root):raise ValueError('Restore destination not empty')
        index={v['drive_file_id']:v for v in s['tables']['case_document_index']}
        remapped={}
        for doc in bundle['manifest']['documents']:
            remapped[doc['id']]=_upload_verified(drive,docs_root,doc['name'],bundle['contents'][doc['id']],index[doc['id']]['mime_type'])
        import_snapshot(host,bundle,storage_root_id=scope.root_id,document_ids=remapped)
        host._reload()
        actual=host.list_case_documents(case,year)
        if {v['id'] for v in actual['files']}!=set(remapped.values()):raise ValueError('Restored document readback mismatch')
        for doc in bundle['manifest']['documents']:
            _,raw=host.get_case_document(case,year,remapped[doc['id']])
            if sha256(raw).hexdigest()!=doc['sha256']:raise ValueError('Restored bytes mismatch')
        return remapped


def delete_selected_backup(host,drive,bundle):
    """Permanent exact-version deletion; retirement only after provider absence."""
    from googleapiclient.errors import HttpError
    from agent_lab.case_number_reservation_policy import ReservationEvidence,may_release_number
    record=bundle['record'];case=record['case_id'];p=host.persistence
    with host._lock,p._lock:
        p._verify_all();p._verify_anchor()
        if p._db.execute('SELECT 1 FROM case_record WHERE case_id=?',(case,)).fetchone():raise ValueError('Active case blocks number release')
        fresh=load_selected_snapshot(host,drive,case_id=case,tax_year=record['tax_year'],backup_id=record['backup_id'])
        if fresh['record']!=record:raise ValueError('Backup changed before deletion')
        parent=drive.files().get(fileId=record['folder_id'],fields='parents').execute()['parents'][0]
        drive.files().delete(fileId=record['folder_id']).execute()
        try:drive.files().get(fileId=record['folder_id'],fields='id,trashed').execute()
        except HttpError as exc:
            if exc.resp.status!=404:raise
        else:raise RuntimeError('Backup still recoverable; number stays reserved')
        # Include recoverable trash and unregistered folders; uncertainty blocks release.
        survivors=children(drive,parent)
        others=[r for r in list_reserved_backups(p,owner_id=host.owner_id,case_id=case) if r['backup_id']!=record['backup_id']]
        p._db.execute('BEGIN IMMEDIATE')
        try:
            changed=p._db.execute("UPDATE case_backup_registry SET state='RETIRED' WHERE backup_id=? AND owner_id=? AND case_id=? AND state='VERIFIED'",(record['backup_id'],host.owner_id,case)).rowcount
            if changed!=1:raise RuntimeError('Backup retirement conflict')
            p._audit('BACKUP_DELETED_VERIFIED',case,p._mac({'backup_id':record['backup_id'],'manifest_digest':record['manifest_digest']}))
            p._verify_all();p._db.commit();p._write_anchor();p._verify_anchor()
        except BaseException:
            if p._db.in_transaction:p._db.rollback()
            raise
        return may_release_number(ReservationEvidence(False,len(survivors)+len(others),False,False,True,True))
