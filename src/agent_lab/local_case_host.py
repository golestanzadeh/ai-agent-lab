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
            LocalCaseScope(self.root), InMemoryAuditSink(),
            durable_registrar=self.persistence)

    def read_cases(self):
        with self._lock:
            self._reload()
            return tuple(DashboardCase(r.case_id, r.tax_period.year, r.lifecycle_status.value)
                         for r in self.registry.all_records())

    def create_case(self, year: int, assessment: str):
        with self._lock:
            self._reload()
            result = self.workflow.create(CaseCreationRequest(
                request_id="LOCAL-" + uuid4().hex,
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
    app = create_dashboard_app(read_cases=host.read_cases, create_real_case=host.create_case)
    app.state.local_case_host = host
    app.state.product_case_source = "canonical-sqlite"
    return app


app = create_local_case_app()
