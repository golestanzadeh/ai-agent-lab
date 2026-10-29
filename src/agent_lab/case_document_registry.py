"""State-aware extension of the existing canonical SQLite document index.

Folder observations are not extraction acceptance or permission to move files.
"""
from datetime import datetime, timezone
import hmac
import json

LEGACY_COLUMNS = {'case_id','tax_year','drive_file_id','name','mime_type','size','indexed_at'}
EXTENSIONS = {
    'registry_state': "TEXT NOT NULL DEFAULT 'UNRESOLVED'",
    'source_status': "TEXT NOT NULL DEFAULT 'UNRESOLVED'",
    'parent_id': "TEXT NOT NULL DEFAULT ''",
    'history_json': "TEXT NOT NULL DEFAULT '[]'",
    'registry_mac': "TEXT NOT NULL DEFAULT ''",
}
STATES = frozenset({'PENDING','ACTIVE_ANALYZED','DELETED_ANALYZED','UNRESOLVED'})
FOLDERS = {'Documents':'PENDING','Tax_Categories':'ACTIVE_ANALYZED','Deleted_Documents':'DELETED_ANALYZED'}


def ensure_schema(p):
    """Transactional, additive component migration; core schema v3 is unchanged."""
    p._db.execute('''CREATE TABLE IF NOT EXISTS case_document_index (
        case_id TEXT NOT NULL,tax_year INTEGER NOT NULL,drive_file_id TEXT NOT NULL,
        name TEXT NOT NULL,mime_type TEXT NOT NULL,size INTEGER,indexed_at TEXT NOT NULL,
        PRIMARY KEY(case_id,drive_file_id))''')
    columns={r['name'] for r in p._db.execute('PRAGMA table_info(case_document_index)')}
    if not LEGACY_COLUMNS<=columns or columns-(LEGACY_COLUMNS|set(EXTENSIONS)):
        raise ValueError('Unsupported document index schema')
    for name,definition in EXTENSIONS.items():
        if name not in columns:p._db.execute(f'ALTER TABLE case_document_index ADD COLUMN {name} {definition}')


def _rows(p,case_id):
    return [dict(r) for r in p._db.execute('SELECT * FROM case_document_index WHERE case_id=? ORDER BY drive_file_id',(case_id,))]


def verify_rows(p,case_id,tax_year):
    rows=_rows(p,case_id)
    for row in rows:
        if row['tax_year']!=tax_year or row['registry_state'] not in STATES or row['source_status'] not in {'ACTIVE','UNRESOLVED'}:
            raise ValueError('Document registry scope/state mismatch')
        history=json.loads(row['history_json'])
        if not isinstance(history,list):raise ValueError('Invalid document history')
        if row['registry_mac']:
            if not hmac.compare_digest(row['registry_mac'],p._mac({k:v for k,v in row.items() if k!='registry_mac'})):
                raise ValueError('Document registry integrity failure')
        elif any(row[k]!=v for k,v in {'registry_state':'UNRESOLVED','source_status':'UNRESOLVED','parent_id':'','history_json':'[]'}.items()):
            raise ValueError('Unsealed document state')
    last=p._db.execute("SELECT payload_digest FROM case_audit WHERE case_id=? AND action='DOCUMENT_REGISTRY_UPDATED' ORDER BY event_id DESC LIMIT 1",(case_id,)).fetchone()
    if last and not hmac.compare_digest(last[0],p._mac(rows)):raise ValueError('Document registry completeness failure')
    return rows


def seal_collection(p,case_id):
    p._audit('DOCUMENT_REGISTRY_UPDATED',case_id,p._mac(_rows(p,case_id)))


def reconcile(p,*,owner_id,case_id,tax_year,snapshot):
    """Upsert verified observations; absence marks uncertainty, never deletion."""
    if snapshot.get('case_id')!=case_id or snapshot.get('tax_year')!=tax_year:raise PermissionError('Cross-scope document inventory')
    entries=snapshot.get('registry_files')
    if not isinstance(entries,list):raise ValueError('Complete case inventory required')
    ids=set()
    for item in entries:
        if (not isinstance(item,dict) or not isinstance(item.get('id'),str) or not item['id'] or item['id'] in ids or
            item.get('registry_state') not in FOLDERS.values() or not item.get('parent_id') or
            not isinstance(item.get('name'),str) or not item['name'] or not isinstance(item.get('mime_type'),str) or
            not item['mime_type'] or item.get('case_id')!=case_id or item.get('tax_year')!=tax_year):
            raise ValueError('Ambiguous document inventory')
        if item.get('size') is not None and (type(item['size']) is not int or item['size']<0):raise ValueError('Invalid document size')
        ids.add(item['id'])
    with p._lock:
        p._verify_all();p._verify_anchor();p._authorize(owner_id,case_id,tax_year)
        if p._db.in_transaction:raise ValueError('Ambiguous document transaction')
        p._db.execute('BEGIN IMMEDIATE')
        try:
            ensure_schema(p);existing={r['drive_file_id']:r for r in verify_rows(p,case_id,tax_year)}
            for item in entries:
                conflict=p._db.execute('SELECT 1 FROM case_document_index WHERE drive_file_id=? AND (case_id<>? OR tax_year<>?)',(item['id'],case_id,tax_year)).fetchone()
                if conflict:raise PermissionError('Document already owned by another scope')
            changed=False;now=datetime.now(timezone.utc).isoformat()
            observed={r['id']:r for r in entries}
            for file_id in set(existing)|set(observed):
                old=existing.get(file_id);item=observed.get(file_id)
                if item:
                    new={'case_id':case_id,'tax_year':tax_year,'drive_file_id':file_id,'name':item['name'],'mime_type':item['mime_type'],'size':item.get('size'),'indexed_at':now,'registry_state':item['registry_state'],'source_status':'ACTIVE','parent_id':item['parent_id']}
                else:
                    new={k:v for k,v in old.items() if k not in {'history_json','registry_mac'}}
                    new.update(source_status='UNRESOLVED',indexed_at=now)
                if old and all(new[k]==old[k] for k in new if k!='indexed_at') and old['registry_mac']:continue
                history=json.loads(old['history_json']) if old else []
                history.append({'at':now,'before':{k:v for k,v in old.items() if k not in {'history_json','registry_mac'}} if old else None,'after':dict(new)})
                new['history_json']=json.dumps(history,sort_keys=True,separators=(',',':'));new['registry_mac']=p._mac(new)
                names=list(new)
                p._db.execute(f'INSERT INTO case_document_index ({",".join(names)}) VALUES ({",".join("?" for _ in names)}) ON CONFLICT(case_id,drive_file_id) DO UPDATE SET '+','.join(f'{k}=excluded.{k}' for k in names if k not in {'case_id','drive_file_id'}),[new[k] for k in names])
                changed=True
            if changed:seal_collection(p,case_id)
            p._verify_all();p._db.commit()
            if changed:p._write_anchor()
            p._verify_anchor()
        except BaseException:
            if p._db.in_transaction:p._db.rollback()
            raise


def read_registry(p,*,owner_id,case_id,tax_year):
    with p._lock:
        p._verify_all();p._verify_anchor();p._authorize(owner_id,case_id,tax_year)
        return tuple(verify_rows(p,case_id,tax_year))


def assert_pending(row):
    history=json.loads(row['history_json'])
    if (row['registry_state']!='PENDING' or row['source_status']!='ACTIVE' or
        any(event.get('after',{}).get('registry_state') in {'ACTIVE_ANALYZED','DELETED_ANALYZED'} for event in history)):
        raise PermissionError('Analyzed or uncertain document cannot use pending trash')


def record_pending_trash(p,*,owner_id,case_id,tax_year,file_id):
    with p._lock:
        rows=read_registry(p,owner_id=owner_id,case_id=case_id,tax_year=tax_year)
        row=next((r for r in rows if r['drive_file_id']==file_id),None)
        if row is None:raise ValueError('Document registry entry unavailable')
        assert_pending(row)
        p._db.execute('BEGIN IMMEDIATE')
        try:
            p._audit('PENDING_DOCUMENT_TRASHED',case_id,p._mac(row))
            p._db.execute('DELETE FROM case_document_index WHERE case_id=? AND tax_year=? AND drive_file_id=?',(case_id,tax_year,file_id))
            seal_collection(p,case_id);p._verify_all();p._db.commit();p._write_anchor();p._verify_anchor()
        except BaseException:
            if p._db.in_transaction:p._db.rollback()
            raise


def remap_backup_row(p,row,new_file_id):
    """Compatibility for existing whole-case backup restore, not analyzed restore."""
    if set(row)==LEGACY_COLUMNS:
        result=dict(row);result['drive_file_id']=new_file_id
        return result  # Additive SQLite defaults remain unresolved until observed.
    if set(row)!=LEGACY_COLUMNS|set(EXTENSIONS):raise ValueError('Unknown backup document schema')
    if not row['registry_mac'] or not hmac.compare_digest(row['registry_mac'],p._mac({k:v for k,v in row.items() if k!='registry_mac'})):
        raise ValueError('Backup document integrity failure')
    if row['registry_state']!='PENDING' or row['source_status']!='ACTIVE':raise ValueError('Lifecycle backup restore is not enabled')
    if row['drive_file_id']==new_file_id:return dict(row)
    now=datetime.now(timezone.utc).isoformat()
    result={k:v for k,v in row.items() if k not in {'history_json','registry_mac'}}
    result.update(drive_file_id=new_file_id,registry_state='UNRESOLVED',source_status='UNRESOLVED',parent_id='',indexed_at=now)
    history=json.loads(row['history_json'])
    history.append({'at':now,'event':'CASE_RESTORE_REFERENCE_REMAP','before':{k:v for k,v in row.items() if k not in {'history_json','registry_mac'}},'after':dict(result)})
    result['history_json']=json.dumps(history,sort_keys=True,separators=(',',':'));result['registry_mac']=p._mac(result)
    return result
