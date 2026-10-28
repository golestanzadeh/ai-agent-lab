"""Windows local owner-scoped case creation using canonical workflow and SQLite.

Windows login SID identifies the application owner, not a verified tax person.
No external providers, ELSTER or document extraction are activated.
"""
from __future__ import annotations

import os
from pathlib import Path
import secrets
from threading import RLock
from uuid import uuid4

from agent_lab.case_creation_workflow import (
    CaseCreationRequest, CaseCreationWorkflow, InMemoryAuditSink, utc_now,
)
from agent_lab.case_identity_association import CaseIdentityAssociationService
from agent_lab.case_registry import (
    AssessmentMode, CaseRegistry, CaseType, OwnerType, StorageScopeReference, TaxPeriod,
)
from agent_lab.case_persistence import SQLiteCasePersistence
from agent_lab.person_entity_registry import PersonEntityRegistry, PersonRecord, RegistryStatus
from agent_lab.ui_dashboard import DashboardCase, create_dashboard_app
from agent_lab.google_drive_provisioning import GoogleDriveStorageScopeCreator
from agent_lab.google_drive_auth import get_drive_credentials
from googleapiclient.discovery import build
from agent_lab.storage_provisioning import DurableStorageProvisioningAdapter


def windows_owner_sid() -> str:
    import win32api
    import win32security
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)
    sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
    return win32security.ConvertSidToStringSid(sid)


def local_root() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", "")) / "AI-Tax-Agent" / "Cases"
    if not os.environ.get("LOCALAPPDATA"):
        raise RuntimeError("Windows LOCALAPPDATA is required")
    root.mkdir(parents=True, exist_ok=True)
    return root


def protected_integrity_key(root: Path) -> bytes:
    import win32crypt
    path = root / "case-integrity.dpapi"
    if path.exists():
        return win32crypt.CryptUnprotectData(path.read_bytes(), None, None, None, 0)[1]
    if (root / "cases.sqlite").exists():
        raise RuntimeError("integrity key missing for existing database; refusing replacement")
    key = secrets.token_bytes(32)
    encrypted = win32crypt.CryptProtectData(key, "AI-Tax-Agent case integrity", None, None, None, 0)
    with path.open("xb") as handle:
        handle.write(encrypted)
    return key


class LocalCaseScope:
    def __init__(self, root: Path):
        self.root = root

    def create_case_scope(self, period: TaxPeriod, case_id: str) -> StorageScopeReference:
        path = self.root / str(period.year) / case_id
        if path.exists():
            raise ValueError("case directory already exists; reconciliation required")
        path.mkdir(parents=True, exist_ok=False)
        for name in ("Documents", "Evidence", "Tax_Categories", "Calculations", "Reports", "Audit"):
            (path / name).mkdir()
        return StorageScopeReference("local-filesystem", str(path.resolve()))


class LocalCaseHost:
    def __init__(self):
        self._lock = RLock()
        self.root = local_root()
        self.owner_id = "WINDOWS-OWNER:" + windows_owner_sid()
        self.persistence = SQLiteCasePersistence(
            self.root / "cases.sqlite", integrity_key=protected_integrity_key(self.root))
        self._reload()

    def _reload(self):
        # The canonical durable SQLite authority is the source of truth on restart.
        # An empty allowlist cannot be passed to load_runtime, so discover only
        # IDs bound to this owner in the verified local database.
        db = self.persistence
        with db._lock:
            db._verify_all()
            rows = db._db.execute(
                "SELECT case_id FROM ui_case_authorization WHERE owner_id=? ORDER BY case_id",
                (self.owner_id,),
            ).fetchall()
        ids = frozenset(row["case_id"] for row in rows)
        self.registry = (db.load_runtime(owner_id=self.owner_id, allowed_case_ids=ids).registry
                         if ids else CaseRegistry())
        self.identities = PersonEntityRegistry()
        now = utc_now()
        self.identities.register_person(PersonRecord(
            self.owner_id, RegistryStatus.ACTIVE, None, now, now, 1))
        self.associations = CaseIdentityAssociationService(self.identities, self.registry)
        for record in self.registry.all_records():
            self.associations.associate(self.owner_id, record.case_id)
        self.workflow = CaseCreationWorkflow(
            self.identities, self.registry, self.associations,
            DurableStorageProvisioningAdapter(
                self.persistence,
                GoogleDriveStorageScopeCreator(
                    drive_service=build("drive", "v3", credentials=get_drive_credentials(), cache_discovery=False),
                    system_root_id=os.environ["AI_TAX_AGENT_DRIVE_ROOT_ID"],
                    journal_path=self.root / "drive-api-provisioning.json",
                    audit=InMemoryAuditSink(),
                ),
            ), InMemoryAuditSink(),
            durable_registrar=self.persistence,
            allow_multiple_cases_per_period=True)

    def read_cases(self):
        with self._lock:
            self._reload()
            return tuple(DashboardCase(r.case_id, r.tax_period.year, r.lifecycle_status.value)
                         for r in self.registry.all_records())

    def preview_empty_case_deletion(self, case_id: str, tax_year: int):
        from agent_lab.empty_case_preflight import inspect_empty_case
        with self._lock:
            self._reload()
            return inspect_empty_case(
                self.persistence,
                build("drive", "v3", credentials=get_drive_credentials(), cache_discovery=False),
                owner_id=self.owner_id, case_id=case_id, tax_year=tax_year,
            )

    def delete_empty_case(self, case_id: str, tax_year: int):
        from agent_lab.empty_case_preflight import inspect_empty_case
        with self._lock:
            self._reload()
            drive = build('drive', 'v3', credentials=get_drive_credentials(), cache_discovery=False)
            inspect_empty_case(self.persistence, drive, owner_id=self.owner_id,
                               case_id=case_id, tax_year=tax_year)
            with self.persistence._lock:
                row = self.persistence._db.execute(
                    'SELECT storage_root_id FROM case_record WHERE case_id=? AND owner_id=? AND tax_year=?',
                    (case_id, self.owner_id, tax_year)).fetchone()
                if row is None:
                    raise ValueError('case disappeared')
                root_id = row['storage_root_id']
            # Existing journal is the authority for the exact case folder.
            journal = GoogleDriveStorageScopeCreator(
                drive_service=drive, system_root_id=os.environ['AI_TAX_AGENT_DRIVE_ROOT_ID'],
                journal_path=self.root / 'drive-api-provisioning.json',
                audit=InMemoryAuditSink())
            state = __import__('json').loads(journal.path.read_text(encoding='utf-8'))
            prefix = f'Tax_Years/{tax_year}/Cases/{case_id}'
            if (state.get('pending') is not None or state.get('cases', {}).get(case_id) != tax_year
                    or state.get('folders', {}).get(prefix) != root_id):
                raise ValueError('Drive journal mismatch')
            # A second live check immediately before the destructive provider request.
            inspect_empty_case(self.persistence, drive, owner_id=self.owner_id,
                               case_id=case_id, tax_year=tax_year)
            # Move to Google Drive trash rather than irreversible permanent deletion.
            drive.files().update(fileId=root_id, body={'trashed': True}, fields='id,trashed').execute()
            metadata = drive.files().get(fileId=root_id, fields='id,trashed').execute()
            if metadata.get('id') != root_id or metadata.get('trashed') is not True:
                raise RuntimeError('Drive trash readback failed; SQLite unchanged')
            # Preserve case metadata if the provider deletion could not be verified.
            self.persistence.delete_verified_empty_case(
                owner_id=self.owner_id, case_id=case_id, tax_year=tax_year,
                storage_root_id=root_id)
            journal.forget_deleted_empty_case(tax_year=tax_year, case_id=case_id,
                                              case_root_id=root_id)
            self._reload()
            with self.persistence._lock:
                remaining = self.persistence._db.execute(
                    'SELECT 1 FROM case_record WHERE case_id=?', (case_id,)).fetchone()
            if remaining is not None:
                raise RuntimeError('SQLite deletion readback failed')
            return {'database_deleted': True, 'drive_trashed': True, 'case_id': case_id}

    def list_case_documents(self, case_id: str, tax_year: int):
        # Metadata-only inventory. Never infer scope from a filename or Drive-wide search.
        with self._lock:
            self._reload()
            with self.persistence._lock:
                self.persistence._verify_all()
                self.persistence._verify_anchor()
                self.persistence._authorize(self.owner_id, case_id, tax_year)
                row = self.persistence._db.execute(
                    'SELECT storage_provider,storage_root_id FROM case_record WHERE case_id=?',
                    (case_id,)).fetchone()
                if row is None or row['storage_provider'] != 'google_drive':
                    raise ValueError('invalid case storage scope')
                root_id = row['storage_root_id']
            drive = build('drive', 'v3', credentials=get_drive_credentials(), cache_discovery=False)
            root = drive.files().get(fileId=root_id, fields='id,name,mimeType,trashed').execute()
            if (root.get('id') != root_id or root.get('name') != case_id
                    or root.get('mimeType') != 'application/vnd.google-apps.folder'
                    or root.get('trashed') is not False):
                raise ValueError('case root mismatch')
            def children(folder_id):
                items, token = [], None
                while True:
                    response = drive.files().list(
                        q=f"'{folder_id}' in parents and trashed = false",
                        fields='nextPageToken,files(id,name,mimeType,parents,trashed,size)',
                        pageSize=1000, pageToken=token).execute()
                    items.extend(response.get('files', []))
                    token = response.get('nextPageToken')
                    if not token:
                        return items
            folders = children(root_id)
            docs = [x for x in folders if x.get('name') == 'Documents'
                    and x.get('mimeType') == 'application/vnd.google-apps.folder'
                    and x.get('parents') == [root_id] and x.get('trashed') is False]
            if len(docs) != 1:
                raise ValueError('Documents folder scope mismatch')
            files = children(docs[0]['id'])
            if any(x.get('parents') != [docs[0]['id']] or x.get('trashed') is not False
                   for x in files):
                raise ValueError('Document parent mismatch')
            result = {'case_id': case_id, 'tax_year': tax_year,
                    'documents_folder_id': docs[0]['id'],
                    'files': sorted([{'id': x['id'], 'name': x['name'],
                                      'mime_type': x['mimeType'], 'size': x.get('size')}
                                     for x in files if x['mimeType'] != 'application/vnd.google-apps.folder'],
                                    key=lambda x: (x['name'].casefold(), x['id']))}
            self._sync_document_index(case_id,tax_year,result)
            return result

    def upload_case_document(self, case_id: str, tax_year: int, filename: str, content: bytes):
        from io import BytesIO
        from hashlib import sha256
        from googleapiclient.http import MediaIoBaseUpload
        from agent_lab.empty_case_preflight import EmptyCaseBlocked

        if not content or len(content) > 20 * 1024 * 1024:
            raise ValueError('File must be between 1 byte and 20 MiB')
        if (not filename or filename in {'.', '..'} or '/' in filename
                or chr(92) in filename or any(ord(c) < 32 for c in filename)
                or len(filename) > 180):
            raise ValueError('Invalid filename')
        import mimetypes
        mime = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        if mime not in {'application/pdf', 'image/jpeg', 'image/png',
                        'image/tiff', 'image/webp'}:
            raise ValueError('Unsupported document type')
        with self._lock:
            # Resolve case and exact Documents folder through existing authenticated
            # case-scoped read path. No Drive-wide search or manual folder IDs.
            snapshot = self.list_case_documents(case_id, tax_year)
            for entry in snapshot['files']:
                if entry['name'] == filename:
                    raise ValueError('Filename already exists in this case')
            folder_id = snapshot['documents_folder_id']
            drive = build('drive', 'v3', credentials=get_drive_credentials(), cache_discovery=False)
            media = MediaIoBaseUpload(BytesIO(content), mimetype=mime, resumable=False)
            created = drive.files().create(
                body={'name': filename, 'parents': [folder_id]},
                media_body=media, fields='id,name,parents,mimeType,trashed').execute()
            if (created.get('name') != filename or created.get('parents') != [folder_id]
                    or created.get('trashed') is not False or not created.get('id')):
                raise RuntimeError('Upload response did not confirm scoped ownership')
            # Readback and ensure the uploaded object appears in the selected case.
            readback = self.list_case_documents(case_id, tax_year)
            if not any(f['id'] == created['id'] and f['name'] == filename
                       for f in readback['files']):
                raise RuntimeError('Uploaded document not found on readback')
            return {'case_id': case_id, 'tax_year': tax_year,
                    'document_id': created['id'], 'name': filename,
                    'size': len(content), 'sha256': sha256(content).hexdigest()}

    def _sync_document_index(self, case_id, tax_year, snapshot):
        # Drive is authoritative. SQLite stores only case-scoped metadata.
        import sqlite3
        from datetime import datetime, timezone
        db = self.persistence._db
        db.execute("""CREATE TABLE IF NOT EXISTS case_document_index (
            case_id TEXT NOT NULL, tax_year INTEGER NOT NULL,
            drive_file_id TEXT NOT NULL, name TEXT NOT NULL,
            mime_type TEXT NOT NULL, size INTEGER,
            indexed_at TEXT NOT NULL,
            PRIMARY KEY(case_id, drive_file_id))""")
        now = datetime.now(timezone.utc).isoformat()
        for file in snapshot['files']:
            db.execute("""INSERT INTO case_document_index
                (case_id,tax_year,drive_file_id,name,mime_type,size,indexed_at)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(case_id,drive_file_id) DO UPDATE SET
                name=excluded.name,mime_type=excluded.mime_type,
                size=excluded.size,indexed_at=excluded.indexed_at""",
                (case_id,tax_year,file['id'],file['name'],
                 file['mime_type'],file.get('size'),now))
        ids = [file['id'] for file in snapshot['files']]
        if ids:
            placeholders = ','.join('?' for _ in ids)
            db.execute('DELETE FROM case_document_index WHERE case_id=? AND drive_file_id NOT IN ('+placeholders+')',
                       (case_id,*ids))
        else:
            db.execute('DELETE FROM case_document_index WHERE case_id=?',(case_id,))
        db.commit()

    def get_case_document(self, case_id, tax_year, document_id):
        from io import BytesIO
        from googleapiclient.http import MediaIoBaseDownload
        with self._lock:
            snapshot = self.list_case_documents(case_id,tax_year)
            entry = next((x for x in snapshot['files'] if x['id']==document_id),None)
            if entry is None:
                raise ValueError('Document does not belong to this case')
            drive = build('drive','v3',credentials=get_drive_credentials(),cache_discovery=False)
            buffer = BytesIO()
            request = drive.files().get_media(fileId=document_id)
            downloader = MediaIoBaseDownload(buffer,request)
            done = False
            while not done:
                _,done=downloader.next_chunk()
                if buffer.tell()>25*1024*1024:
                    raise ValueError('Document exceeds preview limit')
            return entry,buffer.getvalue()

    def trash_case_document(self,case_id,tax_year,document_id):
        with self._lock:
            snapshot=self.list_case_documents(case_id,tax_year)
            entry=next((x for x in snapshot['files'] if x['id']==document_id),None)
            if entry is None:
                raise ValueError('Document does not belong to this case')
            drive=build('drive','v3',credentials=get_drive_credentials(),cache_discovery=False)
            updated=drive.files().update(fileId=document_id,body={'trashed':True},
                                         fields='id,trashed').execute()
            if updated.get('id')!=document_id or updated.get('trashed') is not True:
                raise RuntimeError('Drive trash readback mismatch')
            self._sync_document_index(case_id,tax_year,self.list_case_documents(case_id,tax_year))
            return {'deleted':True,'document_id':document_id}

    def preview_next_case_id(self, year: int):
        from agent_lab.case_backup_registry import number_is_reserved
        with self._lock:
            self._reload()
            self.workflow._case_number_reserved = lambda candidate: number_is_reserved(
                self.persistence, owner_id=self.owner_id, case_id=candidate)
            return self.workflow._generate_case_id(year)

    def create_case(self, year: int, assessment: str):
        with self._lock:
            self._reload()
            # Only resume a failed intent for the next unregistered case ID.
            # Completed earlier cases must not block a second case in the year.
            from agent_lab.case_backup_registry import number_is_reserved
            self.workflow._case_number_reserved = lambda candidate: number_is_reserved(self.persistence, owner_id=self.owner_id, case_id=candidate)
            next_case_id = self.workflow._generate_case_id(year)
            if number_is_reserved(
                self.persistence, owner_id=self.owner_id, case_id=next_case_id
            ):
                raise ValueError("Case number reserved by verified backup")
            with self.persistence._lock:
                pending = self.persistence._db.execute(
                    "SELECT request_id,status FROM storage_provisioning "
                    "WHERE owner_id=? AND tax_year=? AND case_id=?",
                    (self.owner_id, year, next_case_id),
                ).fetchone()
            if pending and pending["status"] != "RETRYABLE_FAILURE":
                raise ValueError("existing storage intent requires reconciliation")
            request_id = pending["request_id"] if pending else "LOCAL-" + uuid4().hex
            result = self.workflow.create(CaseCreationRequest(
                request_id=request_id,
                owner_type=OwnerType.PERSON,
                owner_reference=self.owner_id,
                tax_period=TaxPeriod("CALENDAR_YEAR", year),
                case_type=CaseType.INDIVIDUAL,
                assessment_mode=AssessmentMode(assessment),
                requested_by=self.owner_id,
                requested_at=utc_now(),
            ))
            self._reload()
            return result.case_id


def create_local_case_app():
    host = LocalCaseHost()
    app = create_dashboard_app(read_cases=host.read_cases, create_real_case=host.create_case, preview_next_case_id=host.preview_next_case_id)
    from fastapi import Form, HTTPException, Request
    from fastapi.responses import JSONResponse

    @app.post("/cases/delete/preview")
    async def preview_empty_case(request: __import__("fastapi").Request, case_id: str = Form(...), tax_year: int = Form(...)):
        if request.headers.get("origin") != "http://127.0.0.1:8766" or request.headers.get("host") != "127.0.0.1:8766":
            raise HTTPException(status_code=403, detail="Origin rejected")
        try:
            result = host.preview_empty_case_deletion(case_id, tax_year)
        except Exception:
            return JSONResponse({"ready": False, "database_ready": False,
                                 "drive_ready": False, "reason": "Verification failed or case not empty"},
                                status_code=409, headers={"Cache-Control": "no-store"})
        return JSONResponse({"ready": True, "database_ready": result.sqlite_ready,
                             "drive_ready": result.drive_ready, "case_id": result.case_id,
                             "tax_year": result.tax_year,
                             "deletion_enabled": True}, headers={"Cache-Control": "no-store"})

    @app.post('/cases/delete/confirm')
    async def confirm_empty_case(request: __import__('fastapi').Request,
                                 case_id: str = Form(...), tax_year: int = Form(...),
                                 confirmation: str = Form(...)):
        if (request.headers.get('origin') != 'http://127.0.0.1:8766'
                or request.headers.get('host') != '127.0.0.1:8766'):
            raise HTTPException(status_code=403, detail='Origin rejected')
        if confirmation != case_id:
            raise HTTPException(status_code=400, detail='Confirmation mismatch')
        try:
            result = host.delete_empty_case(case_id, tax_year)
        except Exception:
            return JSONResponse({'deleted': False, 'reason': 'Deletion failed or requires reconciliation',
                                 'verify_both_sources': True}, status_code=409,
                                headers={'Cache-Control': 'no-store'})
        return JSONResponse({'deleted': True, **result}, headers={'Cache-Control': 'no-store'})

    @app.get('/cases/documents/inventory')
    async def case_documents_inventory(case_id: str, tax_year: int):
        try:
            result = host.list_case_documents(case_id, tax_year)
        except Exception:
            return JSONResponse({'ready': False, 'reason': 'Case document scope unavailable'},
                                status_code=409, headers={'Cache-Control': 'no-store'})
        return JSONResponse({'ready': True, **result}, headers={'Cache-Control': 'no-store'})

    @app.post('/cases/documents/upload')
    async def case_document_upload(request: __import__("fastapi").Request, case_id: str = Form(...),
                                   tax_year: int = Form(...), document: __import__('fastapi').UploadFile = __import__('fastapi').File(...)):
        if (request.headers.get('origin') != 'http://127.0.0.1:8766'
                or request.headers.get('host') != '127.0.0.1:8766'):
            raise HTTPException(status_code=403, detail='Origin rejected')
        if document.size is not None and document.size > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail='Document too large')
        content = await document.read(20 * 1024 * 1024 + 1)
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail='Document too large')
        try:
            result = host.upload_case_document(case_id, tax_year, document.filename or '', content)
        except ValueError as exc:
            return JSONResponse({'uploaded': False, 'reason': str(exc)}, status_code=400,
                                headers={'Cache-Control': 'no-store'})
        except Exception:
            return JSONResponse({'uploaded': False, 'reason': 'Upload failed or requires verification'},
                                status_code=409, headers={'Cache-Control': 'no-store'})
        return JSONResponse({'uploaded': True, **result}, headers={'Cache-Control': 'no-store'})

    @app.get('/cases/documents/view')
    async def view_case_document(case_id: str,tax_year: int,document_id: str):
        from fastapi.responses import Response
        try:
            entry,content=host.get_case_document(case_id,tax_year,document_id)
        except Exception:
            raise HTTPException(status_code=404,detail='Document unavailable')
        mime=entry['mime_type']
        if mime not in {'application/pdf','image/jpeg','image/png','image/webp','image/tiff'}:
            raise HTTPException(status_code=415,detail='Preview not supported')
        return Response(content,media_type=mime,headers={
            'Content-Disposition':'inline',
            'Cache-Control':'no-store',
            'X-Content-Type-Options':'nosniff',
            'Content-Security-Policy':"default-src 'none'; sandbox",
        })

    @app.post('/cases/documents/delete')
    async def delete_case_document(request: __import__('fastapi').Request,
                                   case_id: str = Form(...),tax_year: int = Form(...),
                                   document_id: str = Form(...)):
        if (request.headers.get('origin') != 'http://127.0.0.1:8766'
                or request.headers.get('host') != '127.0.0.1:8766'):
            raise HTTPException(status_code=403,detail='Origin rejected')
        try:
            result=host.trash_case_document(case_id,tax_year,document_id)
        except Exception:
            return JSONResponse({'deleted':False,'reason':'Document scope or deletion verification failed'},
                                status_code=409,headers={'Cache-Control':'no-store'})
        return JSONResponse(result,headers={'Cache-Control':'no-store'})

    from agent_lab.case_backup_dashboard import attach_case_backup_routes
    attach_case_backup_routes(app, host)
    app.state.local_case_host = host
    app.state.product_case_source = "canonical-sqlite"
    return app


app = create_local_case_app()
