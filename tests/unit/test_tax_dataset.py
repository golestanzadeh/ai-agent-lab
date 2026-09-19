from agent_lab.tax_dataset import TaxDatasetField, validate_fields


def field(**changes):
    base = dict(key="gross", value="36470.23", document="lst.pdf", page=1,
                evidence="field 3", confidence=0.99, tax_category="EMPLOYMENT")
    base.update(changes)
    return TaxDatasetField(**base)


def test_valid_evidence_field_passes():
    assert validate_fields([field()]) == []


def test_route_requires_both_addresses():
    issues = validate_fields([field(route_relevant=True, address_from="Home")])
    assert "gross:ROUTE_ENDPOINTS_REQUIRED" in issues


def test_cross_year_is_review_not_silent_assignment():
    issues = validate_fields([field(payment_year=2025, service_year=2024)])
    assert "gross:CROSS_YEAR_REVIEW" in issues


def test_low_confidence_is_flagged():
    assert "gross:LOW_CONFIDENCE" in validate_fields([field(confidence=0.7)])
