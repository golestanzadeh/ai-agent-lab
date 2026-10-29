"""Fail-closed case-scoped Drive move engine; no UI route or automatic dispatch.

The caller must supply a verified Kernel authorization callback and a canonical
SQLite connection. No actual case is touched unless execute_move is invoked.
"""
from dataclasses import dataclass
import json
from datetime import datetime, timezone


class MoveBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class MoveIntent:
    case_id: str
    tax_year: int
    file_id: str
    source_parent_id: str
    destination_parent_id: str
    intent_id: str


def validate_intent(intent, *, authorized_id, case_id, tax_year, file_id, parent_id):
    if not isinstance(intent, MoveIntent):
        raise MoveBlocked('Typed move intent required')
    if not all(isinstance(v, str) and v for v in (intent.case_id, intent.file_id,
            intent.source_parent_id, intent.destination_parent_id, intent.intent_id)):
        raise MoveBlocked('Incomplete move intent')
    if intent.source_parent_id == intent.destination_parent_id:
        raise MoveBlocked('Same source and destination')
    if intent.intent_id != authorized_id:
        raise PermissionError('Unauthorized intent')
    if (intent.case_id, intent.tax_year, intent.file_id, intent.source_parent_id) != (
            case_id, tax_year, file_id, parent_id):
        raise MoveBlocked('Stale or cross-case intent')
    return True


def _now():
    return datetime.now(timezone.utc).isoformat()


def _journal_schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS case_document_move_intent (
        intent_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, tax_year INTEGER NOT NULL,
        file_id TEXT NOT NULL, source_parent_id TEXT NOT NULL,
        destination_parent_id TEXT NOT NULL, status TEXT NOT NULL,
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")


def _drive_location(drive, file_id):
    result = drive.files().get(fileId=file_id, fields='id,parents,trashed').execute()
    if result.get('id') != file_id or result.get('trashed') is not False:
        raise MoveBlocked('Drive identity or trash state mismatch')
    parents = result.get('parents')
    if not isinstance(parents, list) or len(parents) != 1 or not isinstance(parents[0], str):
        raise MoveBlocked('Ambiguous Drive parent')
    return parents[0]


def execute_move(*, persistence, drive, intent, authorized_id, observed,
                 verify_folder_scope, verify_kernel_authority, reconcile_registry):
    """Execute or recover an idempotent move after durable journal and independent readback.

    All callbacks are mandatory. The authority callback must verify an existing
    Kernel permission decision, not merely compare an arbitrary caller token.
    Reconciliation must validate the full scoped Drive inventory and seal audit.
    """
    if not all(callable(fn) for fn in (verify_folder_scope, verify_kernel_authority, reconcile_registry)):
        raise MoveBlocked('Missing mandatory authorization or reconciliation')
    validate_intent(intent, authorized_id=authorized_id, case_id=observed.get('case_id'),
                    tax_year=observed.get('tax_year'), file_id=observed.get('drive_file_id'),
                    parent_id=observed.get('parent_id'))
    if observed.get('source_status') != 'ACTIVE' or observed.get('registry_state') == 'UNRESOLVED':
        raise MoveBlocked('Unverified registry state')
    verify_kernel_authority(intent)
    verify_folder_scope(intent.case_id, intent.tax_year, intent.source_parent_id,
                        intent.destination_parent_id)
    p = persistence
    with p._lock:
        p._verify_all()
        p._verify_anchor()
        p._authorize(p.owner_id if hasattr(p, 'owner_id') else observed['owner_id'],
                     intent.case_id, intent.tax_year)
        if p._db.in_transaction:
            raise MoveBlocked('Existing transaction')
        p._db.execute('BEGIN IMMEDIATE')
        try:
            _journal_schema(p._db)
            existing = p._db.execute(
                'SELECT * FROM case_document_move_intent WHERE intent_id=?', (intent.intent_id,)).fetchone()
            if existing:
                if any(existing[k] != getattr(intent, k) for k in (
                        'case_id', 'tax_year', 'file_id', 'source_parent_id', 'destination_parent_id')):
                    raise MoveBlocked('Intent ID reused with different parameters')
                if existing['status'] == 'COMPLETE':
                    p._db.commit()
                    return {'intent_id': intent.intent_id, 'status': 'COMPLETE', 'idempotent': True}
            else:
                conflicting = p._db.execute(
                    """SELECT 1 FROM case_document_move_intent WHERE case_id=? AND file_id=?
                       AND status!='COMPLETE' LIMIT 1""", (intent.case_id, intent.file_id)).fetchone()
                if conflicting:
                    raise MoveBlocked('Another move is unresolved')
                p._db.execute(
                    """INSERT INTO case_document_move_intent VALUES (?,?,?,?,?,?,?,?,?)""",
                    (intent.intent_id, intent.case_id, intent.tax_year, intent.file_id,
                     intent.source_parent_id, intent.destination_parent_id, 'PREPARED', _now(), _now()))
            p._db.commit()
        except BaseException:
            if p._db.in_transaction:
                p._db.rollback()
            raise
        # An uncertain Drive result is intentionally retained as PREPARED.
        current = _drive_location(drive, intent.file_id)
        if current == intent.source_parent_id:
            drive.files().update(fileId=intent.file_id,
                                 addParents=intent.destination_parent_id,
                                 removeParents=intent.source_parent_id,
                                 fields='id,parents,trashed').execute()
        elif current != intent.destination_parent_id:
            raise MoveBlocked('Unexpected Drive location; manual reconciliation required')
        if _drive_location(drive, intent.file_id) != intent.destination_parent_id:
            raise MoveBlocked('Drive readback failed; intent remains recoverable')
        reconcile_registry(intent)
        if _drive_location(drive, intent.file_id) != intent.destination_parent_id:
            raise MoveBlocked('Drive changed during registry reconciliation')
        p._db.execute('BEGIN IMMEDIATE')
        try:
            p._db.execute(
                """UPDATE case_document_move_intent SET status='COMPLETE',updated_at=?
                   WHERE intent_id=? AND status='PREPARED'""", (_now(), intent.intent_id))
            p._db.commit()
        except BaseException:
            if p._db.in_transaction:
                p._db.rollback()
            raise
        return {'intent_id': intent.intent_id, 'status': 'COMPLETE', 'idempotent': False}
