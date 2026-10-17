from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent_lab.orchestrator_kernel import IntegrityError, OrchestratorKernel, PermissionDenied
from agent_lab.ui_dashboard import create_dashboard_app
from agent_lab.ui_functional_test_store import FunctionalTestStore
from agent_lab.ui_kernel_projection import ReadOnlyKernelProjection
from agent_lab.ui_synthetic_document_parser import (
    MAX_CONTENT_BYTES, PARSER_SCHEMA, parse_synthetic_wage_statement,
)
from agent_lab.ui_synthetic_kernel_execution import SyntheticCaseKernelExecutor


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "orchestrator" / "v1"
ORIGIN = "http://127.0.0.1:8766"
OWNER_RETEST_FIXTURE = ROOT / "tests" / "fixtures" / "ui25" / "synthetic-wage-statement-owner-retest.txt"
OWNER_RETEST_SHA256 = "fe830b1d6131d9ad420e164f928f03bb1a56b90abdf38b11ea7a63453d5c65e4"


def fixture(employer: str, gross: str, withheld: str) -> bytes:
    return (
        "DOCUMENT_TYPE=SYNTHETIC_WAGE_STATEMENT\n"
        "TAX_YEAR=2025\n"
        f"EMPLOYER_ID={employer}\n"
        f"GROSS_EMPLOYMENT_INCOME={gross}\n"
        f"WITHHELD_WAGE_TAX={withheld}\n"
        "CURRENCY=EUR\n"
    ).encode()


def client(store: FunctionalTestStore, kernel_database: Path) -> TestClient:
    executor = SyntheticCaseKernelExecutor(kernel_database, CONTRACT_ROOT)
    return TestClient(
        create_dashboard_app(
            test_store=store,
            read_kernel_projection=ReadOnlyKernelProjection(kernel_database).read,
            execute_kernel_task=executor.execute,
        ),
        base_url=ORIGIN,
        headers={"origin": ORIGIN},
    )


def test_owner_retest_fixture_is_canonical_and_stable():
    content = OWNER_RETEST_FIXTURE.read_bytes()
    assert b"\r" not in content
    assert content.endswith(b"\n")
    assert hashlib.sha256(content).hexdigest() == OWNER_RETEST_SHA256
    parsed = parse_synthetic_wage_statement(content, "text/plain")
    assert parsed.employer_id == "TEST-EMPLOYER-OWNER"
    assert parsed.gross_employment_income == "55000.00"
    assert parsed.withheld_wage_tax == "10250.00"


def test_two_actual_fixtures_extract_distinct_values_through_kernel(tmp_path):
    samples = (
        ("TEST-EMPLOYER-ALPHA", "55000.00", "10250.00"),
        ("TEST-EMPLOYER-BETA", "71234.56", "14567.89"),
    )
    for index, (employer, gross, withheld) in enumerate(samples):
        case_id = f"TEST-EXTRACT-{index}"
        store = FunctionalTestStore(tmp_path / f"ui-{index}.sqlite3")
        store.create_case(case_id, 2025)
        content = fixture(employer, gross, withheld)
        store.add_document(case_id, f"Fixture {index}", content, "text/plain")
        digest = hashlib.sha256(content).hexdigest()
        extracted = parse_synthetic_wage_statement(content, "text/plain")
        assert extracted.employer_id == employer
        assert extracted.field_lineage == (
            ("DOCUMENT_TYPE", 1), ("TAX_YEAR", 2), ("EMPLOYER_ID", 3),
            ("GROSS_EMPLOYMENT_INCOME", 4), ("WITHHELD_WAGE_TAX", 5),
            ("CURRENCY", 6),
        )
        kernel_database = tmp_path / f"kernel-{index}.sqlite3"
        response = client(store, kernel_database).post(
            "/test/kernel/documents/extract",
            data={"case_id": case_id, "run_id": f"RUN-EXTRACT-{index}", "document_digest": digest},
            follow_redirects=False,
        )
        assert response.status_code == 303
        page = client(store, kernel_database).get(response.headers["location"])
        for expected in (
            "استخراج محتوای مصنوعی — تحلیل مالیاتی نیست",
            PARSER_SCHEMA, employer, gross, withheld, "EUR",
        ):
            assert expected in page.text
        assert "SYNTHETIC_CONTENT_EXTRACTION=VALID" not in page.text
        with OrchestratorKernel(kernel_database, CONTRACT_ROOT) as kernel:
            kernel.verify_audit_chain()
            assert kernel.kill_switch_state() == "HALTED"
            task = json.loads(kernel._connection.execute(
                "SELECT payload_json FROM tasks"
            ).fetchone()[0])
            assert task["inputs"] == [
                f"test-document://{case_id}/sha256:{digest}", f"sha256:{digest}",
                f"parser://{PARSER_SCHEMA}", f"extraction://{extracted.digest}",
            ]
            response_payload = json.loads(kernel._connection.execute(
                "SELECT payload_json FROM responses"
            ).fetchone()[0])
            assert response_payload["tests"][0]["name"] == "deterministic-synthetic-content-extraction"
            assert response_payload["authority_used"] == [
                "human-authorization://UI25-07/synthetic-content-extraction"
            ]
        store.close()

        reopened = FunctionalTestStore(tmp_path / f"ui-{index}.sqlite3")
        document = reopened.resolve_document_content(case_id, digest)
        assert document.content == content
        restart_page = client(reopened, kernel_database).get(
            "/", params={"tab": "analysis", "case_id": case_id, "run_id": f"RUN-EXTRACT-{index}"}
        )
        assert employer in restart_page.text
        reopened.close()


def test_document_actions_are_explicit_localized_and_hidden_without_kernel(tmp_path):
    store = FunctionalTestStore(tmp_path / "ui.sqlite3")
    store.create_case("TEST-UX", 2025)
    content = fixture("TEST-EMPLOYER-UX", "12.00", "1.00")
    store.add_document("TEST-UX", "Synthetic UX fixture", content, "text/plain")

    unavailable = TestClient(
        create_dashboard_app(test_store=store), base_url=ORIGIN,
    ).get("/", params={"tab": "documents", "case_id": "TEST-UX", "lang": "fa-IR"})
    assert "اجرای Kernel در این launcher فعال نیست" in unavailable.text
    assert 'action="/test/kernel/documents/extract"' not in unavailable.text

    available_client = client(store, tmp_path / "kernel.sqlite3")
    for lang, validate_label, extract_label in (
        ("fa-IR", "۲. فقط تطبیق digest در Kernel", "۳. استخراج فیلدهای fixture مصنوعی"),
        ("de-DE", "2. Nur Digest im Kernel prüfen", "3. Felder aus synthetischem Fixture extrahieren"),
    ):
        page = available_client.get(
            "/", params={"tab": "documents", "case_id": "TEST-UX", "lang": lang}
        )
        assert validate_label in page.text
        assert extract_label in page.text
        assert "PDF" in page.text
        assert 'action="/test/kernel/documents/validate"' in page.text
        assert 'action="/test/kernel/documents/extract"' in page.text
    store.close()


def test_unsupported_upload_and_fixture_show_actionable_localized_errors(tmp_path):
    store = FunctionalTestStore(tmp_path / "ui.sqlite3")
    store.create_case("TEST-UX", 2025)
    test_client = client(store, tmp_path / "kernel.sqlite3")
    rejected_upload = test_client.post(
        "/test/documents",
        data={"case_id": "TEST-UX", "label": "Unsupported", "lang": "de-DE"},
        files={"document": ("document.pdf", b"%PDF synthetic", "application/pdf")},
        follow_redirects=False,
    )
    assert rejected_upload.status_code == 303
    upload_page = test_client.get(rejected_upload.headers["location"])
    assert "Erlaubt sind nur synthetische text/plain-Dateien" in upload_page.text
    assert '<html lang="de-DE" dir="ltr">' in upload_page.text
    assert store.detail("TEST-UX")["documents"] == ()

    unsupported = b"not a supported synthetic fixture\n"
    store.add_document("TEST-UX", "Unsupported text", unsupported, "text/plain")
    digest = hashlib.sha256(unsupported).hexdigest()
    rejected_extraction = test_client.post(
        "/test/kernel/documents/extract",
        data={"case_id": "TEST-UX", "run_id": "RUN-UX", "document_digest": digest},
        follow_redirects=False,
    )
    assert rejected_extraction.status_code == 303
    extraction_page = test_client.get(rejected_extraction.headers["location"])
    assert "قرارداد شش‌فیلدی ui25.synthetic-wage-statement/1" in extraction_page.text
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", CONTRACT_ROOT) as kernel:
        assert kernel._connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 0
        assert kernel.kill_switch_state() == "HALTED"
        kernel.verify_audit_chain()
    store.close()


def test_german_success_redirect_and_replay_error_preserve_locale(tmp_path):
    store = FunctionalTestStore(tmp_path / "ui.sqlite3")
    store.create_case("TEST-UX", 2025)
    content = fixture("TEST-EMPLOYER-UX", "12.00", "1.00")
    store.add_document("TEST-UX", "Fixture", content, "text/plain")
    digest = hashlib.sha256(content).hexdigest()
    test_client = client(store, tmp_path / "kernel.sqlite3")
    payload = {
        "case_id": "TEST-UX", "run_id": "RUN-UX", "document_digest": digest,
        "lang": "de-DE",
    }

    successful = test_client.post(
        "/test/kernel/documents/extract", data=payload, follow_redirects=False,
    )
    assert successful.status_code == 303
    assert "lang=de-DE" in successful.headers["location"]
    analysis = test_client.get(successful.headers["location"])
    assert '<html lang="de-DE" dir="ltr">' in analysis.text
    assert "Verifizierte extrahierte Felder" in analysis.text

    replay = test_client.post(
        "/test/kernel/documents/extract", data=payload, follow_redirects=False,
    )
    assert replay.status_code == 303
    assert "error=execution_conflict" in replay.headers["location"]
    assert "lang=de-DE" in replay.headers["location"]
    replay_page = test_client.get(replay.headers["location"])
    assert "Diese Lauf-ID wurde bereits verwendet" in replay_page.text
    assert "kein unterstütztes synthetisches Fixture" not in replay_page.text
    assert '<html lang="de-DE" dir="ltr">' in replay_page.text
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", CONTRACT_ROOT) as kernel:
        assert kernel._connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 1
        assert kernel.kill_switch_state() == "HALTED"
        kernel.verify_audit_chain()
    store.close()


@pytest.mark.parametrize(("failure", "code", "message"), [
    (PermissionDenied("synthetic denial"), "kernel_denied", "Kernel این اجرا را"),
    (IntegrityError("synthetic integrity failure"), "kernel_unavailable", "یکپارچگی یا وضعیت Kernel"),
])
def test_kernel_failures_have_closed_privacy_safe_messages(tmp_path, failure, code, message):
    store = FunctionalTestStore(tmp_path / "ui.sqlite3")
    store.create_case("TEST-UX", 2025)
    content = fixture("TEST-EMPLOYER-UX", "12.00", "1.00")
    store.add_document("TEST-UX", "Fixture", content, "text/plain")
    digest = hashlib.sha256(content).hexdigest()

    def reject(**_kwargs):
        raise failure

    test_client = TestClient(
        create_dashboard_app(
            test_store=store, read_kernel_projection=lambda *_args: None,
            execute_kernel_task=reject,
        ),
        base_url=ORIGIN, headers={"origin": ORIGIN},
    )
    response = test_client.post(
        "/test/kernel/documents/extract",
        data={
            "case_id": "TEST-UX", "run_id": "RUN-UX",
            "document_digest": digest, "lang": "fa-IR",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert f"error={code}" in response.headers["location"]
    page = test_client.get(response.headers["location"])
    assert message in page.text
    assert str(failure) not in page.text
    store.close()


def test_document_mutations_reject_unknown_locale(tmp_path):
    store = FunctionalTestStore(tmp_path / "ui.sqlite3")
    store.create_case("TEST-UX", 2025)
    response = client(store, tmp_path / "kernel.sqlite3").post(
        "/test/documents",
        data={"case_id": "TEST-UX", "label": "Fixture", "lang": "en-US"},
        files={"document": ("fixture.txt", fixture("TEST-EMPLOYER-UX", "12.00", "1.00"), "text/plain")},
    )
    assert response.status_code == 400
    assert store.detail("TEST-UX")["documents"] == ()
    store.close()


def test_german_digest_validation_failure_is_localized_and_fail_closed(tmp_path):
    store = FunctionalTestStore(tmp_path / "ui.sqlite3")
    store.create_case("TEST-UX", 2025)
    test_client = client(store, tmp_path / "kernel.sqlite3")
    response = test_client.post(
        "/test/kernel/documents/validate",
        data={
            "case_id": "TEST-UX", "run_id": "RUN-VALIDATE",
            "document_digest": "0" * 64, "lang": "de-DE",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "error=unknown_document" in response.headers["location"]
    assert "lang=de-DE" in response.headers["location"]
    page = test_client.get(response.headers["location"])
    assert '<html lang="de-DE" dir="ltr">' in page.text
    assert "Dokument oder Digest ist im ausgewählten Fall nicht registriert" in page.text
    assert "Synthetic document evidence rejected" not in page.text
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", CONTRACT_ROOT) as kernel:
        assert kernel._connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 0
        assert kernel.kill_switch_state() == "HALTED"
        kernel.verify_audit_chain()
    store.close()


def test_legacy_digest_only_document_cannot_offer_extraction(tmp_path):
    database = tmp_path / "ui.sqlite3"
    store = FunctionalTestStore(database)
    store.create_case("TEST-UX", 2025)
    content = fixture("TEST-EMPLOYER-UX", "12.00", "1.00")
    store.add_document("TEST-UX", "Legacy metadata", content, "text/plain")
    digest = hashlib.sha256(content).hexdigest()
    store._db.execute(
        "UPDATE test_document SET content=NULL,content_type=NULL WHERE case_id=? AND digest=?",
        ("TEST-UX", digest),
    )
    store._db.commit()
    test_client = client(store, tmp_path / "kernel.sqlite3")

    page = test_client.get(
        "/", params={"tab": "documents", "case_id": "TEST-UX", "lang": "fa-IR"}
    )
    assert "محتوای این رکورد قدیمی ذخیره نشده است" in page.text
    assert 'action="/test/kernel/documents/validate"' in page.text
    assert 'action="/test/kernel/documents/extract"' not in page.text

    forced = test_client.post(
        "/test/kernel/documents/extract",
        data={
            "case_id": "TEST-UX", "run_id": "RUN-LEGACY",
            "document_digest": digest, "lang": "fa-IR",
        },
        follow_redirects=False,
    )
    assert forced.status_code == 303
    assert "error=missing_content" in forced.headers["location"]
    forced_page = test_client.get(forced.headers["location"])
    assert "byteهای محتوا ذخیره نشده‌اند" in forced_page.text
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", CONTRACT_ROOT) as kernel:
        assert kernel._connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
        assert kernel._connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 0
        assert kernel.kill_switch_state() == "HALTED"
        kernel.verify_audit_chain()
    store.close()


@pytest.mark.parametrize(("mutation", "error_code"), [
    (("content_type", "application/pdf"), "unsupported_format"),
    (("content", b"altered"), "digest_mismatch"),
])
def test_persisted_format_and_digest_failures_are_distinct(tmp_path, mutation, error_code):
    store = FunctionalTestStore(tmp_path / f"{error_code}.sqlite3")
    store.create_case("TEST-UX", 2025)
    content = fixture("TEST-EMPLOYER-UX", "12.00", "1.00")
    store.add_document("TEST-UX", "Fixture", content, "text/plain")
    digest = hashlib.sha256(content).hexdigest()
    column, value = mutation
    store._db.execute(
        f"UPDATE test_document SET {column}=? WHERE case_id=? AND digest=?",
        (value, "TEST-UX", digest),
    )
    store._db.commit()
    test_client = client(store, tmp_path / f"kernel-{error_code}.sqlite3")
    response = test_client.post(
        "/test/kernel/documents/extract",
        data={
            "case_id": "TEST-UX", "run_id": "RUN-FAIL",
            "document_digest": digest, "lang": "de-DE",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert f"error={error_code}" in response.headers["location"]
    assert "lang=de-DE" in response.headers["location"]
    page = test_client.get(response.headers["location"])
    assert '<html lang="de-DE" dir="ltr">' in page.text
    assert str(value) not in page.text
    store.close()


@pytest.mark.parametrize("content", [
    b"\xff\n",
    fixture("TEST-EMPLOYER-A", "1.00", "0.00").replace(b"TAX_YEAR=2025", b"TAX_YEAR=2024"),
    fixture("TEST-EMPLOYER-A", "1.00", "0.00").replace(b"CURRENCY=EUR", b"CURRENCY=USD"),
    fixture("TEST-EMPLOYER-A", "1.00", "0.00").replace(b"1.00", b"one"),
    fixture("TEST-EMPLOYER-A", "1.00", "0.00").replace(
        b"CURRENCY=EUR\n", b"CURRENCY=EUR\nCURRENCY=EUR\n"
    ),
    fixture("TEST-EMPLOYER-A", "1.00", "0.00").replace(b"EMPLOYER_ID=TEST-EMPLOYER-A\n", b""),
    fixture("TEST-EMPLOYER-A", "1.00", "2.00"),
])
def test_parser_rejects_malformed_conflicting_or_unsupported_content(content):
    with pytest.raises(ValueError):
        parse_synthetic_wage_statement(content, "text/plain")


def test_parser_rejects_content_type_size_order_and_ambiguous_lines():
    valid = fixture("TEST-EMPLOYER-A", "1.00", "0.00")
    with pytest.raises(ValueError, match="content type"):
        parse_synthetic_wage_statement(valid, "application/pdf")
    with pytest.raises(ValueError, match="size"):
        parse_synthetic_wage_statement(b"A" * (MAX_CONTENT_BYTES + 1), "text/plain")
    lines = valid.splitlines(keepends=True)
    with pytest.raises(ValueError, match="reordered"):
        parse_synthetic_wage_statement(lines[1] + lines[0] + b"".join(lines[2:]), "text/plain")
    with pytest.raises(ValueError, match="ambiguous"):
        parse_synthetic_wage_statement(valid.replace(b"CURRENCY=EUR", b"CURRENCY=EUR=BAD"), "text/plain")


def test_content_resolution_rejects_cross_case_digest_mismatch_and_legacy_rows(tmp_path):
    database = tmp_path / "ui.sqlite3"
    store = FunctionalTestStore(database)
    store.create_case("TEST-A", 2025)
    store.create_case("TEST-B", 2025)
    content = fixture("TEST-EMPLOYER-A", "10.00", "1.00")
    store.add_document("TEST-A", "A", content)
    digest = hashlib.sha256(content).hexdigest()
    with pytest.raises(ValueError, match="owned"):
        store.resolve_document_content("TEST-B", digest)
    store._db.execute(
        "UPDATE test_document SET content=? WHERE case_id=? AND digest=?",
        (b"altered", "TEST-A", digest),
    )
    store._db.commit()
    with pytest.raises(ValueError, match="does not match"):
        store.resolve_document_content("TEST-A", digest)
    store.close()

    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE test_document SET content=NULL,content_type=NULL WHERE case_id='TEST-A'"
        )
    reopened = FunctionalTestStore(database)
    with pytest.raises(ValueError, match="unavailable"):
        reopened.resolve_document_content("TEST-A", digest)
    reopened.close()


def test_document_cannot_be_reused_across_runs_and_failure_leaves_no_partial_result(tmp_path):
    content = fixture("TEST-EMPLOYER-A", "10.00", "1.00")
    digest = hashlib.sha256(content).hexdigest()
    reference = f"test-document://TEST-A/sha256:{digest}"
    database = tmp_path / "kernel.sqlite3"
    executor = SyntheticCaseKernelExecutor(database, CONTRACT_ROOT)
    executor.execute(
        case_id="TEST-A", tax_year=2025, run_id="RUN-A",
        document_reference=reference, document_digest=digest,
        document_content=content, content_type="text/plain",
    )
    with pytest.raises(PermissionDenied, match="another run"):
        executor.execute(
            case_id="TEST-A", tax_year=2025, run_id="RUN-B",
            document_reference=reference, document_digest=digest,
            document_content=content, content_type="text/plain",
        )
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        assert kernel.kill_switch_state() == "HALTED"
        kernel.verify_audit_chain()
        assert kernel._connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 1


def test_production_dashboard_has_no_synthetic_extraction_access(tmp_path):
    production = TestClient(create_dashboard_app(), base_url=ORIGIN)
    assert production.post(
        "/test/kernel/documents/extract",
        data={"case_id": "TEST-A", "run_id": "RUN-A", "document_digest": "0" * 64},
        headers={"origin": ORIGIN},
    ).status_code == 404
