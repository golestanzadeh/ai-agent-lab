"""Create-only StorageScopeCreator with exact private local reference retention.

One journal per configured system root is required. A process-crash lock or
uncertain create fails closed; this is not a distributed storage transaction.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from agent_lab.case_creation_workflow import InMemoryStorageScopeCreator
from agent_lab.case_registry import StorageScopeReference, TaxPeriod


class ProvisioningError(RuntimeError):
    """Safe diagnostic: never contains provider IDs or raw provider errors."""


@dataclass(frozen=True)
class ProvisioningEvent:
    case_id: str
    tax_period_year: int
    operation: str
    path: str
    outcome: str
    occurred_at: str


class GoogleDriveStorageScopeCreator:
    REQUIRED_SUBFOLDERS = InMemoryStorageScopeCreator.REQUIRED_SUBFOLDERS
    MIME = "application/vnd.google-apps.folder"

    def __init__(self, *, drive_service, system_root_id: str, journal_path: Path, audit):
        if not isinstance(system_root_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", system_root_id):
            raise ProvisioningError("explicit system root required")
        self.drive = drive_service
        self.root = system_root_id
        self.path = Path(journal_path)
        self.audit = audit

    def _save(self, state):
        temp = self.path.with_suffix(self.path.suffix + ".writing")
        with temp.open("w", encoding="utf-8") as stream:
            json.dump(state, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, self.path)

    def _metadata(self, object_id):
        return self.drive.files().get(
            fileId=object_id, fields="id,name,mimeType,parents,trashed,capabilities(canAddChildren)",
        ).execute()

    def _verify(self, metadata, object_id, parent=None, name=None):
        if (metadata.get("id") != object_id or metadata.get("mimeType") != self.MIME
                or metadata.get("trashed") is not False
                or (parent is not None and metadata.get("parents") != [parent])
                or (name is not None and metadata.get("name") != name)):
            raise ProvisioningError("stored folder identity or placement mismatch")

    def _event(self, state, case_id, year, path, outcome):
        event = ProvisioningEvent(case_id, year, "provision_case_storage", path, outcome,
                                  datetime.now(timezone.utc).isoformat())
        state["events"].append(asdict(event))
        self._save(state)
        self.audit.record(event)

    def create_case_scope(self, tax_period: TaxPeriod, case_id: str) -> StorageScopeReference:
        if not isinstance(tax_period, TaxPeriod) or not re.fullmatch(r"CASE-[A-Za-z0-9-]+", case_id):
            raise ProvisioningError("invalid case identity or tax period")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.path.with_suffix(self.path.suffix + ".lock")
        try:
            handle = lock.open("x")
        except FileExistsError:
            raise ProvisioningError("provisioning locked; inspect prior execution before retry") from None
        try:
            state = json.loads(self.path.read_text()) if self.path.exists() else {
                "version": 1, "root": self.root, "folders": {}, "cases": {}, "events": [], "pending": None,
            }
            if state["version"] != 1 or state["root"] != self.root or state["pending"] is not None:
                raise ProvisioningError("journal scope mismatch or uncertain prior creation")
            if case_id in state["cases"] and state["cases"][case_id] != tax_period.year:
                raise ProvisioningError("case already bound to another year")
            state["cases"][case_id] = tax_period.year
            self._save(state)
            self._verify(self._metadata(self.root), self.root)
            parent = self.root
            components = ["Tax_Years", str(tax_period.year), "Cases", case_id]
            path = ""
            for name in components:
                path = f"{path}/{name}".lstrip("/")
                parent = self._folder(state, case_id, tax_period.year, path, parent, name)
            case_root = parent
            for name in self.REQUIRED_SUBFOLDERS:
                self._folder(state, case_id, tax_period.year, f"{path}/{name}", case_root, name)
            self._event(state, case_id, tax_period.year, path, "COMPLETE")
            return StorageScopeReference("google_drive", case_root)
        except ProvisioningError:
            raise
        except Exception:
            raise ProvisioningError("provisioning failed; private journal requires inspection") from None
        finally:
            handle.close()
            lock.unlink()

    def _folder(self, state, case_id, year, path, parent, name):
        if path in state["folders"]:
            object_id = state["folders"][path]
            self._verify(self._metadata(object_id), object_id, parent, name)
            return object_id
        # Exact name within an exact known parent is a conflict check, never
        # authority to adopt an unrecorded folder or search another case.
        found = self.drive.files().list(
            q=f"'{parent}' in parents and name = '{name}' and trashed = false",
            fields="files(id),nextPageToken", pageSize=1,
        ).execute()
        if found.get("files") or found.get("nextPageToken"):
            raise ProvisioningError("unrecorded folder at intended placement; explicit reconciliation required")
        if self._metadata(parent).get("capabilities", {}).get("canAddChildren") is not True:
            raise ProvisioningError("configured parent does not permit folder creation")
        state["pending"] = {"path": path, "parent": parent}
        self._event(state, case_id, year, path, "CREATE_INTENT")
        metadata = self.drive.files().create(
            body={"name": name, "mimeType": self.MIME, "parents": [parent]},
            fields="id,name,mimeType,parents,trashed",
        ).execute()
        object_id = metadata.get("id")
        if not isinstance(object_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", object_id):
            raise ProvisioningError("provider did not return a valid folder reference")
        self._verify(metadata, object_id, parent, name)
        if object_id == self.root or object_id in state["folders"].values():
            raise ProvisioningError("provider returned a reused folder identity")
        state["folders"][path] = object_id
        state["pending"] = None
        self._event(state, case_id, year, path, "CREATED")
        return object_id

    def documents_scope(self, tax_period: TaxPeriod, case_id: str) -> StorageScopeReference:
        self.create_case_scope(tax_period, case_id)
        state = json.loads(self.path.read_text())
        return StorageScopeReference("google_drive", state["folders"][f"Tax_Years/{tax_period.year}/Cases/{case_id}/Documents"])
