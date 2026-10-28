"""Dashboard case backup and document-bearing deletion workflow."""
from __future__ import annotations
import os
import secrets
import time
from uuid import uuid4
from hashlib import sha256
from fastapi import Form, HTTPException, Request
from fastapi.responses import JSONResponse
from googleapiclient.discovery import build
from agent_lab.google_drive_auth import get_drive_credentials
from agent_lab.case_backup_contract import BackupRequest, BackupTrigger, create_backup
from agent_lab.case_backup_drive_writer import write_document_snapshot
from agent_lab.case_backup_registry import register_verified_backup, list_reserved_backups
from agent_lab.case_backup_preflight import verify_case_backup_source
from agent_lab.case_backup_restore import load_selected_snapshot, import_snapshot, restore_selected_snapshot, delete_selected_backup

def attach_case_backup_routes(app, host):
    pending = {}
    def origin(request):
        if request.headers.get('origin') != 'http://127.0.0.1:8766' or request.headers.get('host') != '127.0.0.1:8766':
            raise HTTPException(403, 'Origin rejected')
    def drive():
        return build('drive','v3',credentials=get_drive_credentials(),cache_discovery=False)
    def result(data, status=200):
        return JSONResponse(data,status_code=status,headers={'Cache-Control':'no-store'})
    def preflight(case_id, tax_year):
        source=verify_case_backup_source(host,case_id,tax_year)
        return source
    def matching_bundle(case_id,tax_year,source,backup_id=None):
        records=list_reserved_backups(host.persistence,owner_id=host.owner_id,case_id=case_id)
        if backup_id:
            records=[r for r in records if r['backup_id']==backup_id]
        for record in records:
            try:
                bundle=load_selected_snapshot(host,drive(),case_id=case_id,tax_year=tax_year,backup_id=record['backup_id'])
                docs=bundle['manifest']['documents']
                if bundle['manifest']['source_root_id']!=source['storage_root_id']:continue
                if {x['id']:x['sha256'] for x in docs}!={x['id']:x['sha256'] for x in source['documents']}:continue
                if len(docs)!=len(source['documents']):continue
                import_snapshot(host,bundle,storage_root_id=source['storage_root_id'],document_ids={x['id']:x['id'] for x in docs},dry_run=True)
                return bundle
            except Exception:
                if backup_id:raise
        return None
    @app.post('/cases/backup/create')
    async def backup_create(request:Request,case_id:str=Form(...),tax_year:int=Form(...),trigger:str=Form('MANUAL')):
        origin(request)
        if trigger not in ('MANUAL','PRE_DELETE'):raise HTTPException(400,'Unknown trigger')
        try:
            with host._lock:
                source=preflight(case_id,tax_year)
                req=BackupRequest(case_identity=case_id,case_id=case_id,tax_year=tax_year,backup_id=str(uuid4()),trigger=BackupTrigger(trigger))
                receipt=create_backup(req,lambda r,p:write_document_snapshot(host,r,p))
                register_verified_backup(host.persistence,owner_id=host.owner_id,case_id=case_id,tax_year=tax_year,identity=case_id,receipt=receipt)
                bundle=matching_bundle(case_id,tax_year,source,receipt['backup_id'])
                if not bundle:raise RuntimeError('Backup independent verification failed')
                pending.clear()
                return result({'verified':True,'backup_id':receipt['backup_id'],'document_count':receipt['document_count']})
        except Exception as exc:
            return result({'verified':False,'reason':str(exc)},409)
    @app.post('/cases/backup/readiness')
    async def backup_readiness(request:Request,case_id:str=Form(...),tax_year:int=Form(...)):
        origin(request)
        pending.clear()
        try:
            with host._lock:
                source=preflight(case_id,tax_year)
                if not source['documents']:
                    empty=host.preview_empty_case_deletion(case_id,tax_year)
                    token=secrets.token_urlsafe(24)
                    pending[token]=(case_id,tax_year,None,time.monotonic()+180)
                    return result({'ready':True,'needs_backup':False,'deletion_enabled':bool(empty.sqlite_ready and empty.drive_ready),'token':token,'document_count':0})
                bundle=matching_bundle(case_id,tax_year,source)
                if bundle:
                    token=secrets.token_urlsafe(24)
                    pending[token]=(case_id,tax_year,bundle['record']['backup_id'],time.monotonic()+180)
                    return result({'ready':True,'needs_backup':False,'deletion_enabled':True,'token':token,'backup_id':bundle['record']['backup_id'],'document_count':len(source['documents'])})
                return result({'ready':False,'needs_backup':True,'deletion_enabled':False,'document_count':len(source['documents'])})
        except Exception as exc:
            return result({'ready':False,'deletion_enabled':False,'reason':str(exc)},409)
    @app.post('/cases/backup/delete-confirm')
    async def backup_delete_confirm(request:Request,case_id:str=Form(...),tax_year:int=Form(...),confirmation:str=Form(...),token:str=Form(...)):
        origin(request)
        if confirmation!=case_id:raise HTTPException(400,'Confirmation mismatch')
        session=pending.pop(token,None)
        if not session or session[:2]!=(case_id,tax_year) or time.monotonic()>session[3]:
            return result({'deleted':False,'reason':'Readiness expired; check again'},409)
        try:
            with host._lock:
                source=preflight(case_id,tax_year)
                if session[2] is None:
                    if source['documents']:raise RuntimeError('Documents appeared')
                    host.preview_empty_case_deletion(case_id,tax_year)
                else:
                    bundle=matching_bundle(case_id,tax_year,source,session[2])
                    if not bundle:raise RuntimeError('Verified backup no longer matches')
                for entry in source['documents']:
                    host.trash_case_document(case_id,tax_year,entry['id'])
                host.preview_empty_case_deletion(case_id,tax_year)
                deletion=host.delete_empty_case(case_id,tax_year)
                return result({'deleted':True,**deletion})
        except Exception as exc:
            return result({'deleted':False,'reason':str(exc),'verify_both_sources':True},409)

    @app.get('/cases/backup/available')
    async def backup_available(request:Request,tax_year:int=2025):
        if request.headers.get('host') != '127.0.0.1:8766':
            raise HTTPException(403,'Host rejected')
        try:
            with host._lock,host.persistence._lock:
                host.persistence._verify_all()
                host.persistence._verify_anchor()
                rows=host.persistence._db.execute(
                    "SELECT DISTINCT case_id FROM case_backup_registry WHERE owner_id=? AND tax_year=? AND state='VERIFIED' ORDER BY case_id",
                    (host.owner_id,tax_year)).fetchall()
                available=[]
                for row in rows:
                    case_id=row['case_id']
                    if host.persistence._db.execute('SELECT 1 FROM case_record WHERE case_id=?',(case_id,)).fetchone():
                        continue
                    for entry in list_reserved_backups(host.persistence,owner_id=host.owner_id,case_id=case_id):
                        if entry['tax_year']==tax_year:
                            available.append({'case_id':case_id,'tax_year':tax_year,'backup_id':entry['backup_id']})
                return result({'backups':available})
        except Exception:
            return result({'backups':[],'reason':'Backup inventory unavailable'},409)

    @app.post('/cases/backup/restore')
    async def backup_restore(request:Request,case_id:str=Form(...),tax_year:int=Form(...),
                             backup_id:str=Form(...),confirmation:str=Form(...)):
        origin(request)
        if confirmation!=case_id:raise HTTPException(400,'Confirmation mismatch')
        try:
            with host._lock:
                with host.persistence._lock:
                    host.persistence._verify_all()
                    host.persistence._verify_anchor()
                    if host.persistence._db.execute('SELECT 1 FROM case_record WHERE case_id=?',(case_id,)).fetchone():
                        raise ValueError('Active case blocks restore')
                service=drive()
                bundle=load_selected_snapshot(host,service,case_id=case_id,tax_year=tax_year,backup_id=backup_id)
                import_snapshot(host,bundle,storage_root_id=bundle['manifest']['source_root_id'],
                                document_ids={x['id']:x['id'] for x in bundle['manifest']['documents']},dry_run=True)
                remapped=restore_selected_snapshot(host,service,bundle)
                return result({'restored':True,'case_id':case_id,'document_count':len(remapped)})
        except Exception as exc:
            return result({'restored':False,'reason':str(exc),'requires_reconciliation':True},409)

    @app.post('/cases/backup/delete')
    async def backup_delete(request:Request,case_id:str=Form(...),tax_year:int=Form(...),
                            backup_id:str=Form(...),confirmation:str=Form(...)):
        origin(request)
        if confirmation != f'DELETE {case_id} {backup_id}':
            raise HTTPException(400,'Exact backup deletion confirmation required')
        try:
            with host._lock:
                bundle=load_selected_snapshot(host,drive(),case_id=case_id,tax_year=tax_year,backup_id=backup_id)
                release=delete_selected_backup(host,drive(),bundle)
                remaining=list_reserved_backups(host.persistence,owner_id=host.owner_id,case_id=case_id)
                return result({'deleted':True,'case_id':case_id,'backup_id':backup_id,
                               'number_released':not bool(remaining),
                               'release_policy':str(release)})
        except Exception as exc:
            return result({'deleted':False,'reason':str(exc),'requires_reconciliation':True},409)
