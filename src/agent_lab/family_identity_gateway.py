"""Dashboard adapter to the existing Kernel/Identity client; no approval authority.

Intent resolution is role-private startup injection of already authorized,
evidence-bound Kernel work. Browser input and loopback origin are not approval.
No live intent resolver, enrollment or credentials are installed here.
"""
from dataclasses import dataclass
from datetime import date
from uuid import uuid4

from agent_lab.case_registry import CaseRegistry
from agent_lab.c09_operational_service_runtime import KernelIdentityServiceClient
from agent_lab.ipc_wire_primitives import canonical_sha256
from agent_lab.orchestrator_kernel import PermissionDenied
from agent_lab.c09_service_host import ServiceHostError


class FamilyUnavailable(PermissionError):
    pass


class FamilyReadPending(FamilyUnavailable):
    def __init__(self, transaction_id):
        super().__init__("FAMILY_READ_RECONCILIATION_REQUIRED")
        self.transaction_id=transaction_id


@dataclass(frozen=True)
class FamilyScope:
    owner_id: str
    case_id: str
    tax_year: int
    run_id: str
    task_id: str
    manifest_id: str
    authorization_ref: str
    as_of_date: str


@dataclass(frozen=True)
class FamilyMutationIntent:
    scope: FamilyScope
    operation: str
    payload: dict
    transaction_id: str
    input_digest: str


class FamilyIdentityGateway:
    """Use only accepted Kernel grants; missing evidence/authority fails closed."""

    def __init__(self, *, cases, owner_id, client, read_scope, resolve_intents=None):
        if not isinstance(cases, CaseRegistry) or not isinstance(client, KernelIdentityServiceClient):
            raise TypeError("canonical Case Registry and real Kernel Identity client required")
        self._cases = cases
        self._owner = owner_id
        self._client = client
        self._read_scope = read_scope
        self._resolve = resolve_intents

    def _scope(self, scope, case_id, tax_year, run_id):
        case = self._cases.get(case_id)
        if (not isinstance(scope, FamilyScope) or case is None
                or case.owner_id != self._owner
                or (scope.owner_id, scope.case_id, scope.tax_year, scope.run_id)
                != (self._owner, case_id, tax_year, run_id)
                or case.tax_period.year != tax_year or not run_id):
            raise FamilyUnavailable("FAMILY_SCOPE_DENIED")
        if date.fromisoformat(scope.as_of_date).year != tax_year or date.fromisoformat(scope.as_of_date).isoformat()!=scope.as_of_date:
            raise FamilyUnavailable("FAMILY_SCOPE_DENIED")
        return dict(case_id=case_id, tax_year=tax_year, run_id=run_id,
                    task_id=scope.task_id, manifest_id=scope.manifest_id,
                    authorization_references=[scope.authorization_ref])

    def read(self, case_id, tax_year, run_id, *, recovery=None):
        scope = self._read_scope(case_id, tax_year, run_id)
        args = self._scope(scope, case_id, tax_year, run_id)

        from agent_lab.ipc_operational_read import UUID
        if recovery is not None and (type(recovery) is not str or not UUID.fullmatch(recovery)):
            raise FamilyUnavailable("FAMILY_RECOVERY_REFERENCE_INVALID")
        transaction_id=recovery or "tx:v1:"+str(uuid4())
        def items(operation, subject=""):
            try:
                method=self._client.recover_read if recovery else self._client.read
                final=method(**args,transaction_id=transaction_id,operation=operation,
                    payload=dict(subject_id=subject,as_of_date=scope.as_of_date))
            except PermissionDenied:
                raise FamilyUnavailable("FAMILY_READ_AUTHORITY_REQUIRED") from None
            except ServiceHostError:
                raise FamilyUnavailable("FAMILY_READ_AUTHORITY_OR_RECOVERY_REQUIRED") from None
            except Exception:
                raise FamilyReadPending(transaction_id) from None
            # Only Witness-final released results may reach the Dashboard.
            if final.get("outcome") != "READ_OK":
                raise FamilyUnavailable("FAMILY_RECONCILIATION_REQUIRED")
            result = final["result"]
            if (result["case_id"], result["tax_year"], result["run_id"], result["domain_operation"]) != (case_id, str(tax_year), run_id, operation):
                raise FamilyUnavailable("FAMILY_SCOPE_DENIED")
            return result["items"]

        snapshot=items("READ_FAMILY")[0]
        people=[]
        for pair in snapshot["people"]:
            person=pair["person"];party=pair["party"]
            attributes=dict(person["lookup_attributes"])
            if len(attributes)!=len(person["lookup_attributes"]):raise FamilyUnavailable("FAMILY_AMBIGUOUS_ATTRIBUTES")
            attributes={key:value for key,value in attributes.items() if key in {"first_name","last_name","birth_date","tax_id"}}
            people.append(dict(person_id=person["person_id"],name=person["preferred_display_name"],
                               attributes=attributes,role=party["role"],binding_id=party["binding_id"]))
        return dict(case_id=case_id,tax_year=tax_year,run_id=run_id,people=people,
                    relationships=snapshot["relationships"],relationship_writes_available=False,
                    writes_available=self._resolve is not None)

    def mutate(self, case_id, tax_year, run_id, action, values):
        operations = {"create": ("REGISTER_IDENTITY", "BIND_PARTY"),
                      "correct": ("CORRECT_PERSON",), "associate": ("BIND_PARTY",)}
        allowed={"create":{"first_name","last_name","birth_date","tax_id","role"},
                 "correct":{"person_id","first_name","last_name","birth_date","tax_id"},
                 "associate":{"person_id","role"}}
        if action not in operations or self._resolve is None:
            raise FamilyUnavailable("FAMILY_AUTHENTICATED_EVIDENCE_REQUIRED")
        if (type(values) is not dict or set(values)-allowed[action] or
                any(type(value) is not str or not 1<=len(value.encode("utf-8"))<=256 for value in values.values())):
            raise FamilyUnavailable("FAMILY_INPUT_INVALID")
        required=allowed[action]-{"tax_id"}
        if not required<=set(values):raise FamilyUnavailable("FAMILY_INPUT_INVALID")
        if "birth_date" in values and date.fromisoformat(values["birth_date"]).isoformat()!=values["birth_date"]:raise FamilyUnavailable("FAMILY_INPUT_INVALID")
        if "role" in values and values["role"] not in {"PRIMARY_TAXPAYER","SPOUSE_OR_PARTNER","CHILD","OTHER_DEPENDENT_OR_RELEVANT_PERSON"}:raise FamilyUnavailable("FAMILY_INPUT_INVALID")
        self._scope(self._read_scope(case_id,tax_year,run_id),case_id,tax_year,run_id)
        # Resolve existing work only. This callback cannot grant Kernel permission,
        # consume approvals, write Identity or replace the protected source.
        intents = self._resolve(case_id, tax_year, run_id, action, values)
        if (type(intents) is not tuple or tuple(item.operation for item in intents) != operations[action]):
            raise FamilyUnavailable("FAMILY_AUTHENTICATED_EVIDENCE_REQUIRED")
        for intent in intents:
            if not isinstance(intent, FamilyMutationIntent) or intent.input_digest != canonical_sha256(values):
                raise FamilyUnavailable("FAMILY_EVIDENCE_INPUT_MISMATCH")
            self._scope(intent.scope, case_id, tax_year, run_id)
        if len({item.transaction_id for item in intents})!=len(intents):
            raise FamilyUnavailable("FAMILY_INTENT_CONFLICT")
        if action=="create" and intents[0].payload.get("subject_id")!=intents[1].payload.get("subject_id"):
            raise FamilyUnavailable("FAMILY_INTENT_CONFLICT")
        for intent in intents:
            if "person_id" in values and intent.payload.get("subject_id")!=values["person_id"]:
                raise FamilyUnavailable("FAMILY_INTENT_CONFLICT")
        for intent in intents:
            args = self._scope(intent.scope, case_id, tax_year, run_id)
            args.update(operation=intent.operation, transaction_id=intent.transaction_id)
            payload=dict(intent.payload)
            input_values={key:value for key,value in values.items() if key not in {"person_id","role"}}
            payload["owner_input_digest"]=canonical_sha256({"role":values["role"]} if intent.operation=="BIND_PARTY" else input_values)
            prepared = self._client.mutation_stage(**args, message_type="PREPARE_MUTATION", payload=payload)
            if prepared["outcome"] != "PREPARED":
                raise FamilyUnavailable("FAMILY_RECONCILIATION_REQUIRED")
            committed = self._client.mutation_stage(**args, message_type="COMMIT_MUTATION", payload=payload)
            if committed["outcome"] != "IDENTITY_COMMITTED":
                raise FamilyUnavailable("FAMILY_RECONCILIATION_REQUIRED")
            final = self._client.reconcile("MUTATION:" + intent.transaction_id)
            receipt = final["receipt"]
            verification = final["custodian_verification"]["response"]
            payload = dict(staged_receipt_digest=canonical_sha256(receipt),
                witness_object_key=final["object_key"], witness_generation=final["generation"],
                witness_preimage_digest=receipt["witness_preimage_digest"],
                signed_record_digest=verification["signed_record_digest"],
                custodian_verification_digest=canonical_sha256(verification), custodian_nonce=verification["nonce"])
            reply = self._client.mutation_stage(**args, message_type="FINALIZE_MUTATION", payload=payload)
            if reply["outcome"] != "COMMITTED_FINAL":
                raise FamilyUnavailable("FAMILY_RECONCILIATION_REQUIRED")
        return dict(status="COMMITTED_FINAL")
