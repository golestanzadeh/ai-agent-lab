from dataclasses import replace

import pytest

from agent_lab.eric_adapter_contract import (
    AdapterDesignOutcome,
    DENIED_CAPABILITIES,
    EricAdapterContract,
    EricAdapterContractError,
    OfficialMaterialKind,
    OfficialMaterialStatus,
    REQUIRED_OFFICIAL_MATERIALS,
    design_eric_adapter,
)
from agent_lab.elster_dry_run import SyntheticSubmissionEnvelope, SyntheticTaxSummary


def envelope() -> SyntheticSubmissionEnvelope:
    return SyntheticSubmissionEnvelope(
        case_id="SYNTH-CASE-0002",
        run_id="SYNTH-RUN-0002",
        tax_year=2024,
        procedure_code="UFA10",
        eric_version="44.3.6.0",
        purpose="synthetic adapter contract validation",
        data_classification="SYNTHETIC",
        payload=SyntheticTaxSummary(50000, 8000, 2500),
    )


def test_contract_has_stable_versioned_identity():
    contract = EricAdapterContract()
    assert contract.contract_version == "2"
    assert contract.artifact_identity == contract.artifact_identity
    assert contract.artifact_identity.reference.startswith("sha256:")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("contract_version", "1", "contract_version"),
        ("environment", "PRODUCTION", "NON_PRODUCTION_DESIGN"),
        ("eric_version", "43.2", "ERiC version"),
        ("procedure_code", "UFA12", "procedure_code"),
        ("tax_year", 2025, "tax_year"),
        ("envelope_schema_version", 2, "schema_version"),
    ],
)
def test_contract_fails_closed_outside_exact_versioned_route(field, value, message):
    with pytest.raises(EricAdapterContractError, match=message):
        replace(EricAdapterContract(), **{field: value})


def test_official_material_status_cannot_be_forged_by_the_design_package():
    with pytest.raises(EricAdapterContractError, match="governed local recovery"):
        replace(EricAdapterContract(), material_status="VERIFIED")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (
            "required_official_materials",
            REQUIRED_OFFICIAL_MATERIALS[:-1],
            "contract version change",
        ),
        (
            "denied_capabilities",
            DENIED_CAPABILITIES[:-1],
            "contract version change",
        ),
    ],
)
def test_contract_policy_cannot_drift_without_a_version_change(field, value, message):
    with pytest.raises(EricAdapterContractError, match=message):
        replace(EricAdapterContract(), **{field: value})


def test_contract_names_recovered_materials_without_claiming_mapping():
    contract = EricAdapterContract()
    assert (
        contract.material_status
        is OfficialMaterialStatus.RECOVERED_LOCAL_MAPPING_UNVERIFIED
    )
    assert contract.required_official_materials == (
        OfficialMaterialKind.INTERFACE_SPECIFICATION,
        OfficialMaterialKind.XML_SCHEMA,
        OfficialMaterialKind.PLAUSIBILITY_RULES,
    )


def test_design_plan_binds_contract_and_synthetic_envelope_identity():
    item = envelope()
    contract = EricAdapterContract()
    plan = design_eric_adapter(item, contract=contract)
    assert plan.outcome is AdapterDesignOutcome.BOUNDARY_READY_MAPPING_BLOCKED
    assert plan.contract_reference == contract.artifact_identity.reference
    assert plan.envelope_reference == item.artifact_identity.reference
    assert plan.contract_version == "2"
    assert len(plan.blockers) == 2


def test_boundary_ready_never_means_mapping_or_execution_ready():
    plan = design_eric_adapter(envelope())
    assert plan.mapping_permitted is False
    assert plan.validation_permitted is False
    assert plan.signing_permitted is False
    assert plan.transmission_permitted is False
    assert plan.credential_access is False
    assert plan.network_calls == ()
    assert "XML_MAPPING" in plan.denied_capabilities
    assert "NETWORK" in plan.denied_capabilities
    assert "TRANSMISSION" in plan.denied_capabilities


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("mapping_permitted", True, "cannot enable"),
        ("validation_permitted", True, "cannot enable"),
        ("signing_permitted", True, "cannot enable"),
        ("transmission_permitted", True, "cannot enable"),
        ("credential_access", True, "cannot enable"),
        ("network_calls", ("https://example.invalid",), "network calls"),
        ("denied_capabilities", DENIED_CAPABILITIES[:-1], "capability policy"),
    ],
)
def test_design_plan_cannot_be_forged_to_enable_a_capability(field, value, message):
    plan = design_eric_adapter(envelope())
    with pytest.raises(EricAdapterContractError, match=message):
        replace(plan, **{field: value})


def test_non_synthetic_or_unknown_input_is_rejected():
    with pytest.raises(EricAdapterContractError, match="SyntheticSubmissionEnvelope"):
        design_eric_adapter(object())


def test_contract_is_immutable():
    contract = EricAdapterContract()
    with pytest.raises(Exception):
        contract.tax_year = 2025
