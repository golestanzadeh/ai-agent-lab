"""Local synthetic E10/2024 mapping profile with no ERiC execution capability."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from xml.etree import ElementTree as ET

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.elster_dry_run import SyntheticSubmissionEnvelope


MAPPING_PROFILE_VERSION = "6"
E10_NAMESPACE = "http://finkonsens.de/elster/elstererklaerung/est/e10/v2024"
E10_VERSION = "2024"
MAX_EURO_AMOUNT = 999_999_999_999
DENIED_CAPABILITIES = (
    "ERIC_FFI",
    "FULL_E10_DECLARATION",
    "OFFICIAL_ERIC_PLAUSIBILITY_ENGINE",
    "SIGNING",
    "MANUFACTURER_ID_ACCESS",
    "CREDENTIAL_OR_CERTIFICATE_ACCESS",
    "NETWORK",
    "TRANSMISSION",
)
REMAINING_BLOCKERS = (
    "FULL_E10_DECLARATION_NOT_IMPLEMENTED",
    "OFFICIAL_ERIC_PLAUSIBILITY_ENGINE_NOT_EXECUTED",
)


class E10MappingError(ValueError):
    """Raised when an E10 mapping request or result leaves the governed profile."""


class E10Person(str, Enum):
    PERSON_A = "PersonA"
    PERSON_B = "PersonB"


class DeductibleExpenseSemantics(str, Enum):
    OTHER_EMPLOYMENT_EXPENSES = "N_OTHER_EMPLOYMENT_EXPENSES"


class OtherExpenseCategory(str, Enum):
    WRITING_MATERIALS = "Schreibmaterial"


class WorkEquipmentType(str, Enum):
    COMPUTER = "Computer"


class HomeOfficeExpenseType(str, Enum):
    EQUIPMENT_EXCLUDING_FURNITURE_AND_COMPUTER = "Ausstattung (ohne Büromöbel und Computer)"


class MappingOutcome(str, Enum):
    LOCAL_PROFILE_VALIDATED_EXTERNAL_EXECUTION_BLOCKED = (
        "LOCAL_PROFILE_VALIDATED_EXTERNAL_EXECUTION_BLOCKED"
    )


@dataclass(frozen=True, slots=True)
class E10FieldBinding:
    source_field: str
    official_path: str
    field_id: str
    lexical_value: str


@dataclass(frozen=True, slots=True)
class E10MappingRequest:
    envelope: SyntheticSubmissionEnvelope
    person: E10Person
    tax_class: int
    deductible_expense_semantics: DeductibleExpenseSemantics
    other_expense_category: OtherExpenseCategory
    solidarity_surcharge_eur: int | None = None
    church_tax_eur: int | None = None
    partner_church_tax_eur: int | None = None
    professional_association_name: str | None = None
    professional_association_eur: int | None = None
    work_equipment_type: WorkEquipmentType | None = None
    work_equipment_eur: int | None = None
    home_office_expense_type: HomeOfficeExpenseType | None = None
    home_office_expense_eur: int | None = None
    profile_version: str = MAPPING_PROFILE_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.envelope, SyntheticSubmissionEnvelope):
            raise E10MappingError("a SyntheticSubmissionEnvelope is required")
        if not isinstance(self.person, E10Person):
            raise E10MappingError("person must be an explicit E10Person")
        if not isinstance(self.tax_class, int) or isinstance(self.tax_class, bool):
            raise E10MappingError("tax_class must be an integer")
        if self.tax_class not in range(1, 7):
            raise E10MappingError("tax_class must be between 1 and 6")
        if not isinstance(self.deductible_expense_semantics, DeductibleExpenseSemantics):
            raise E10MappingError(
                "deductible expenses require an explicit supported semantic classification"
            )
        if not isinstance(self.other_expense_category, OtherExpenseCategory):
            raise E10MappingError(
                "other employment expenses require an explicit supported official category"
            )
        for name, value in (
            ("solidarity_surcharge_eur", self.solidarity_surcharge_eur),
            ("church_tax_eur", self.church_tax_eur),
            ("partner_church_tax_eur", self.partner_church_tax_eur),
        ):
            if value is not None:
                _whole_euros(name, value)
        if (self.professional_association_name is None) is not (
            self.professional_association_eur is None
        ):
            raise E10MappingError("professional association name and amount must be provided together")
        if self.professional_association_name is not None:
            if not isinstance(self.professional_association_name, str) or not self.professional_association_name.strip():
                raise E10MappingError("professional association name must be non-empty")
            if len(self.professional_association_name) > 999:
                raise E10MappingError("professional association name exceeds the official boundary")
            _five_digit_euros("professional_association_eur", self.professional_association_eur)
        if (self.work_equipment_type is None) is not (self.work_equipment_eur is None):
            raise E10MappingError("work equipment type and amount must be provided together")
        if self.work_equipment_type is not None:
            if not isinstance(self.work_equipment_type, WorkEquipmentType):
                raise E10MappingError("work equipment requires an explicit supported official type")
            _whole_euros("work_equipment_eur", self.work_equipment_eur)
        if (self.home_office_expense_type is None) is not (
            self.home_office_expense_eur is None
        ):
            raise E10MappingError("home-office expense type and amount must be provided together")
        if self.home_office_expense_type is not None:
            if not isinstance(self.home_office_expense_type, HomeOfficeExpenseType):
                raise E10MappingError("home-office expense requires an explicit supported official type")
            _whole_euros("home_office_expense_eur", self.home_office_expense_eur)
        if self.profile_version != MAPPING_PROFILE_VERSION:
            raise E10MappingError("unsupported E10 mapping profile version")

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="ERIC_E10_2024_MAPPING_REQUEST",
            version=self.profile_version,
            payload=self,
        )


@dataclass(frozen=True, slots=True)
class E10MappingResult:
    outcome: MappingOutcome
    request_reference: str
    profile_version: str
    namespace: str
    schema_version: str
    field_bindings: tuple[E10FieldBinding, ...]
    fragment_xml: str
    blockers: tuple[str, ...]
    denied_capabilities: tuple[str, ...]
    synthetic_only: bool = True
    official_eric_plausibility_executed: bool = False
    credential_access: bool = False
    manufacturer_id_access: bool = False
    network_calls: tuple[str, ...] = ()
    transmission_permitted: bool = False

    def __post_init__(self) -> None:
        if self.outcome is not MappingOutcome.LOCAL_PROFILE_VALIDATED_EXTERNAL_EXECUTION_BLOCKED:
            raise E10MappingError("unsupported mapping outcome")
        _sha256_reference("request_reference", self.request_reference)
        if self.profile_version != MAPPING_PROFILE_VERSION:
            raise E10MappingError("mapping result profile mismatch")
        if self.namespace != E10_NAMESPACE or self.schema_version != E10_VERSION:
            raise E10MappingError("mapping result E10/2024 identity mismatch")
        if self.blockers != REMAINING_BLOCKERS:
            raise E10MappingError("mapping blockers cannot be weakened")
        if self.denied_capabilities != DENIED_CAPABILITIES:
            raise E10MappingError("mapping denied-capability policy mismatch")
        if self.synthetic_only is not True:
            raise E10MappingError("mapping result must remain synthetic-only")
        if any(
            value is not False
            for value in (
                self.official_eric_plausibility_executed,
                self.credential_access,
                self.manufacturer_id_access,
                self.transmission_permitted,
            )
        ):
            raise E10MappingError("external or protected capability cannot be enabled")
        if self.network_calls != ():
            raise E10MappingError("local mapping cannot contain network calls")
        _validate_fragment(self.fragment_xml, self.field_bindings)

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="ERIC_E10_2024_MAPPING_RESULT",
            version=self.profile_version,
            payload=self,
        )


def _sha256_reference(name: str, value: str) -> None:
    digest = value.removeprefix("sha256:") if isinstance(value, str) else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise E10MappingError(f"{name} must be a canonical sha256 reference")


def _whole_euros(name: str, value: int) -> str:
    if not isinstance(value, int) or isinstance(value, bool):
        raise E10MappingError(f"{name} must be an integer euro amount")
    if value < 0 or value > MAX_EURO_AMOUNT:
        raise E10MappingError(f"{name} exceeds the supported E10/2024 amount boundary")
    return str(value)


def _euros_with_cents(name: str, value: int) -> str:
    return f"{_whole_euros(name, value)},00"


def _five_digit_euros(name: str, value: int) -> str:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 99_999:
        raise E10MappingError(f"{name} exceeds the supported five-digit boundary")
    return str(value)


def _qname(local_name: str) -> str:
    return f"{{{E10_NAMESPACE}}}{local_name}"


def _expected_bindings(request: E10MappingRequest) -> tuple[E10FieldBinding, ...]:
    payload = request.envelope.payload
    if request.tax_class == 6:
        wage_group = "LStB_6_Sum"
        gross_id = "E0200203"
        tax_id = "E0200303"
        solidarity_id = "E0200403"
        church_tax_id = "E0200503"
        partner_church_tax_id = "E0200603"
        wage_bindings = ()
    else:
        wage_group = "LStB_1_5_Sum"
        gross_id = "E0200201"
        tax_id = "E0200301"
        solidarity_id = "E0200401"
        church_tax_id = "E0200501"
        partner_church_tax_id = "E0200601"
        wage_bindings = (
            E10FieldBinding(
                source_field="tax_class",
                official_path=f"/N/ArbL/{wage_group}/E0200002",
                field_id="E0200002",
                lexical_value=str(request.tax_class),
            ),
        )
    tax_bindings = (
        E10FieldBinding(
            source_field="gross_wages_eur",
            official_path=f"/N/ArbL/{wage_group}/{gross_id}",
            field_id=gross_id,
            lexical_value=_whole_euros("gross_wages_eur", payload.gross_wages_eur),
        ),
        E10FieldBinding(
            source_field="withheld_wage_tax_eur",
            official_path=f"/N/ArbL/{wage_group}/{tax_id}",
            field_id=tax_id,
            lexical_value=_euros_with_cents(
                "withheld_wage_tax_eur", payload.withheld_wage_tax_eur
            ),
        ),
    )
    if request.solidarity_surcharge_eur is not None:
        tax_bindings += (E10FieldBinding(
            source_field="solidarity_surcharge_eur",
            official_path=f"/N/ArbL/{wage_group}/{solidarity_id}",
            field_id=solidarity_id,
            lexical_value=_euros_with_cents("solidarity_surcharge_eur", request.solidarity_surcharge_eur),
        ),)
    if request.church_tax_eur is not None:
        tax_bindings += (E10FieldBinding(
            source_field="church_tax_eur",
            official_path=f"/N/ArbL/{wage_group}/{church_tax_id}",
            field_id=church_tax_id,
            lexical_value=_euros_with_cents("church_tax_eur", request.church_tax_eur),
        ),)
    if request.partner_church_tax_eur is not None:
        tax_bindings += (E10FieldBinding(
            source_field="partner_church_tax_eur",
            official_path=f"/N/ArbL/{wage_group}/{partner_church_tax_id}",
            field_id=partner_church_tax_id,
            lexical_value=_euros_with_cents(
                "partner_church_tax_eur", request.partner_church_tax_eur
            ),
        ),)
    association_bindings = ()
    if request.professional_association_name is not None:
        amount = _five_digit_euros(
            "professional_association_eur", request.professional_association_eur
        )
        association_bindings = (
            E10FieldBinding("professional_association_name", "/N/Wk/Berufsverb/Einz/E0204001", "E0204001", request.professional_association_name),
            E10FieldBinding("professional_association_eur", "/N/Wk/Berufsverb/Einz/E0204003", "E0204003", amount),
            E10FieldBinding("professional_association_eur", "/N/Wk/Berufsverb/Sum/E0204002", "E0204002", amount),
        )
    work_equipment_bindings = ()
    if request.work_equipment_type is not None:
        amount = _whole_euros("work_equipment_eur", request.work_equipment_eur)
        work_equipment_bindings = (
            E10FieldBinding("work_equipment_type", "/N/Wk/Arbeitsmittel/Einz/E0204401", "E0204401", request.work_equipment_type.value),
            E10FieldBinding("work_equipment_eur", "/N/Wk/Arbeitsmittel/Einz/E0204402", "E0204402", amount),
            E10FieldBinding("work_equipment_eur", "/N/Wk/Arbeitsmittel/Sum/E0204403", "E0204403", amount),
        )
    home_office_bindings = ()
    if request.home_office_expense_type is not None:
        amount = _whole_euros("home_office_expense_eur", request.home_office_expense_eur)
        home_office_bindings = (
            E10FieldBinding("home_office_expense_type", "/N/Wk/Arb_Zim/Einz/E0204503", "E0204503", request.home_office_expense_type.value),
            E10FieldBinding("home_office_expense_eur", "/N/Wk/Arb_Zim/Einz/E0204505", "E0204505", amount),
            E10FieldBinding("home_office_expense_eur", "/N/Wk/Arb_Zim/Sum/E0204504", "E0204504", amount),
        )
    return wage_bindings + tax_bindings + association_bindings + work_equipment_bindings + home_office_bindings + (
        E10FieldBinding(
            source_field="other_expense_category",
            official_path="/N/Wk/Weitere_Wk/Sonst/E0205405",
            field_id="E0205405",
            lexical_value=request.other_expense_category.value,
        ),
        E10FieldBinding(
            source_field="deductible_expenses_eur",
            official_path="/N/Wk/Weitere_Wk/Sonst/E0205406",
            field_id="E0205406",
            lexical_value=_whole_euros(
                "deductible_expenses_eur", payload.deductible_expenses_eur
            ),
        ),
        E10FieldBinding(
            source_field="deductible_expenses_eur",
            official_path="/N/Wk/Weitere_Wk/Sum/E0204803",
            field_id="E0204803",
            lexical_value=_whole_euros(
                "deductible_expenses_eur", payload.deductible_expenses_eur
            ),
        ),
    )


def _build_fragment(request: E10MappingRequest, bindings: tuple[E10FieldBinding, ...]) -> str:
    values = {binding.field_id: binding.lexical_value for binding in bindings}
    root = ET.Element(_qname("E10"), {"version": E10_VERSION})
    n = ET.SubElement(root, _qname("N"))
    ET.SubElement(n, _qname("Person")).text = request.person.value
    employment = ET.SubElement(n, _qname("ArbL"))
    if request.tax_class == 6:
        wage_group_name = "LStB_6_Sum"
        field_ids = ["E0200203", "E0200303"]
        optional_ids = (
            ("E0200403", request.solidarity_surcharge_eur),
            ("E0200503", request.church_tax_eur),
            ("E0200603", request.partner_church_tax_eur),
        )
    else:
        wage_group_name = "LStB_1_5_Sum"
        field_ids = ["E0200002", "E0200201", "E0200301"]
        optional_ids = (
            ("E0200401", request.solidarity_surcharge_eur),
            ("E0200501", request.church_tax_eur),
            ("E0200601", request.partner_church_tax_eur),
        )
    field_ids.extend(field_id for field_id, amount in optional_ids if amount is not None)
    wage_group = ET.SubElement(employment, _qname(wage_group_name))
    for field_id in field_ids:
        ET.SubElement(wage_group, _qname(field_id)).text = values[field_id]
    expenses = ET.SubElement(n, _qname("Wk"))
    if request.professional_association_name is not None:
        association = ET.SubElement(expenses, _qname("Berufsverb"))
        item = ET.SubElement(association, _qname("Einz"))
        ET.SubElement(item, _qname("E0204001")).text = values["E0204001"]
        ET.SubElement(item, _qname("E0204003")).text = values["E0204003"]
        association_sum = ET.SubElement(association, _qname("Sum"))
        ET.SubElement(association_sum, _qname("E0204002")).text = values["E0204002"]
    if request.work_equipment_type is not None:
        work_equipment = ET.SubElement(expenses, _qname("Arbeitsmittel"))
        item = ET.SubElement(work_equipment, _qname("Einz"))
        ET.SubElement(item, _qname("E0204401")).text = values["E0204401"]
        ET.SubElement(item, _qname("E0204402")).text = values["E0204402"]
        equipment_sum = ET.SubElement(work_equipment, _qname("Sum"))
        ET.SubElement(equipment_sum, _qname("E0204403")).text = values["E0204403"]
    if request.home_office_expense_type is not None:
        home_office = ET.SubElement(expenses, _qname("Arb_Zim"))
        item = ET.SubElement(home_office, _qname("Einz"))
        ET.SubElement(item, _qname("E0204503")).text = values["E0204503"]
        ET.SubElement(item, _qname("E0204505")).text = values["E0204505"]
        home_office_sum = ET.SubElement(home_office, _qname("Sum"))
        ET.SubElement(home_office_sum, _qname("E0204504")).text = values["E0204504"]
    other_expenses = ET.SubElement(expenses, _qname("Weitere_Wk"))
    other_expense_item = ET.SubElement(other_expenses, _qname("Sonst"))
    ET.SubElement(other_expense_item, _qname("E0205405")).text = values["E0205405"]
    ET.SubElement(other_expense_item, _qname("E0205406")).text = values["E0205406"]
    expense_sum = ET.SubElement(other_expenses, _qname("Sum"))
    ET.SubElement(expense_sum, _qname("E0204803")).text = values["E0204803"]
    ET.register_namespace("", E10_NAMESPACE)
    return ET.tostring(root, encoding="unicode", short_empty_elements=False)


def _validate_fragment(
    fragment_xml: str, bindings: tuple[E10FieldBinding, ...]
) -> None:
    if not isinstance(fragment_xml, str) or not fragment_xml:
        raise E10MappingError("mapping fragment is required")
    try:
        root = ET.fromstring(fragment_xml)
    except ET.ParseError as exc:
        raise E10MappingError("mapping fragment is not well-formed XML") from exc
    if root.tag != _qname("E10") or root.attrib != {"version": E10_VERSION}:
        raise E10MappingError("mapping fragment root must be exact E10/2024")
    observed: list[tuple[str, str]] = []
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if len(local_name) == 8 and local_name.startswith("E") and local_name[1:].isdigit():
            observed.append((local_name, element.text or ""))
    expected = [(binding.field_id, binding.lexical_value) for binding in bindings]
    if observed != expected:
        raise E10MappingError("mapping fragment and field bindings differ")
    if root.find(f"{_qname('N')}/{_qname('Person')}") is None:
        raise E10MappingError("mapping fragment requires an explicit E10 person")


def map_synthetic_summary_to_e10_2024(request: E10MappingRequest) -> E10MappingResult:
    """Map the supported synthetic subset; do not call ERiC or claim full validation."""
    if not isinstance(request, E10MappingRequest):
        raise E10MappingError("an E10MappingRequest is required")
    bindings = _expected_bindings(request)
    return E10MappingResult(
        outcome=MappingOutcome.LOCAL_PROFILE_VALIDATED_EXTERNAL_EXECUTION_BLOCKED,
        request_reference=request.artifact_identity.reference,
        profile_version=request.profile_version,
        namespace=E10_NAMESPACE,
        schema_version=E10_VERSION,
        field_bindings=bindings,
        fragment_xml=_build_fragment(request, bindings),
        blockers=REMAINING_BLOCKERS,
        denied_capabilities=DENIED_CAPABILITIES,
    )
