from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent_lab.orchestrator_kernel import OrchestratorKernel
from agent_lab.ui_dashboard import create_dashboard_app
from agent_lab.ui_functional_test_store import FunctionalTestStore
from agent_lab.ui_kernel_projection import (
    KernelRunProjection, KernelTaskProjection, ReadOnlyKernelProjection,
)
from agent_lab.ui_synthetic_kernel_execution import (
    SyntheticBudgetRejected,
    SyntheticCaseKernelExecutor,
    SyntheticIncompleteRun,
    SyntheticKillSwitchRejected,
    SyntheticPermissionMatrixRejected,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "orchestrator" / "v1"
ORIGIN = "http://127.0.0.1:8766"


def fixture(employer: str = "TEST-EMPLOYER-UI25-10") -> bytes:
    return (
        "DOCUMENT_TYPE=SYNTHETIC_WAGE_STATEMENT\n"
        "TAX_YEAR=2025\n"
        f"EMPLOYER_ID={employer}\n"
        "GROSS_EMPLOYMENT_INCOME=55000.00\n"
        "WITHHELD_WAGE_TAX=10250.00\n"
        "CURRENCY=EUR\n"
    ).encode()


def client(store: FunctionalTestStore, kernel_database: Path) -> TestClient:
    return TestClient(
        create_dashboard_app(
            test_store=store,
            read_kernel_projection=ReadOnlyKernelProjection(kernel_database).read,
            execute_kernel_task=SyntheticCaseKernelExecutor(
                kernel_database, CONTRACT_ROOT
            ).execute,
        ),
        base_url=ORIGIN, headers={"origin": ORIGIN},
    )


def prepare_completed_run(tmp_path):
    store = FunctionalTestStore(tmp_path / "ui.sqlite3")
    store.create_case("TEST-NAV-A", 2025)
    store.create_case("TEST-NAV-B", 2025)
    content = fixture()
    digest = hashlib.sha256(content).hexdigest()
    store.add_document("TEST-NAV-A", "Navigation fixture", content, "text/plain")
    kernel_database = tmp_path / "kernel.sqlite3"
    test_client = client(store, kernel_database)
    response = test_client.post(
        "/test/kernel/documents/extract",
        data={
            "case_id": "TEST-NAV-A", "run_id": "RUN-NAV-A",
            "document_digest": digest, "lang": "fa-IR",
        }, follow_redirects=False,
    )
    assert response.status_code == 303
    return store, kernel_database, test_client, digest


def kernel_counts(database: Path) -> tuple[int, int, int]:
    with sqlite3.connect(database) as connection:
        return tuple(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                     for table in ("tasks", "responses", "audit_events"))


def test_analysis_documents_analysis_preserves_exact_run_without_mutation(tmp_path):
    store, database, test_client, _digest = prepare_completed_run(tmp_path)
    before = kernel_counts(database)
    analysis = test_client.get("/", params={
        "tab": "analysis", "case_id": "TEST-NAV-A", "run_id": "RUN-NAV-A",
        "lang": "fa-IR",
    })
    assert analysis.status_code == 200
    assert "TEST-EMPLOYER-UI25-10" in analysis.text
    assert "run_id=RUN-NAV-A" in analysis.text
    assert "tab=documents" in analysis.text
    documents = test_client.get("/", params={
        "tab": "documents", "case_id": "TEST-NAV-A", "run_id": "RUN-NAV-A",
        "lang": "fa-IR",
    })
    assert "run_id=RUN-NAV-A" in documents.text
    assert "tab=analysis" in documents.text
    reopened = test_client.get("/", params={
        "tab": "analysis", "case_id": "TEST-NAV-A", "run_id": "RUN-NAV-A",
        "lang": "fa-IR",
    })
    assert "TEST-EMPLOYER-UI25-10" in reopened.text
    assert kernel_counts(database) == before
    store.close()


def test_missing_invalid_refresh_language_and_case_switch_are_safe(tmp_path):
    store, database, test_client, _digest = prepare_completed_run(tmp_path)
    before = kernel_counts(database)
    missing = test_client.get("/", params={
        "tab": "analysis", "case_id": "TEST-NAV-A", "lang": "de-DE",
    })
    assert missing.status_code == 200
    assert 'data-kernel-run-state="missing"' in missing.text
    assert "Geben Sie die genaue Kennung" in missing.text
    invalid = test_client.get("/", params={
        "tab": "analysis", "case_id": "TEST-NAV-B", "run_id": "RUN-NAV-A",
        "lang": "fa-IR",
    })
    assert invalid.status_code == 200
    assert 'data-kernel-run-state="invalid"' in invalid.text
    assert "TEST-EMPLOYER-UI25-10" not in invalid.text
    valid_de = test_client.get("/", params={
        "tab": "analysis", "case_id": "TEST-NAV-A", "run_id": "RUN-NAV-A",
        "lang": "de-DE",
    })
    assert '<html lang="de-DE" dir="ltr">' in valid_de.text
    assert "run_id=RUN-NAV-A" in valid_de.text
    case_b_link = next(
        part.split('"', 1)[0] for part in valid_de.text.split("href=\"")[1:]
        if "case_id=TEST-NAV-B" in part
    )
    assert "tab=analysis" in case_b_link
    assert "run_id=" not in case_b_link
    assert kernel_counts(database) == before
    store.close()


def test_replay_and_document_binding_have_distinct_safe_result_links(tmp_path):
    store, database, test_client, digest = prepare_completed_run(tmp_path)
    replay = test_client.post(
        "/test/kernel/documents/extract",
        data={
            "case_id": "TEST-NAV-A", "run_id": "RUN-NAV-A",
            "document_digest": digest, "lang": "fa-IR",
        }, follow_redirects=False,
    )
    assert "error=run_already_completed" in replay.headers["location"]
    assert "run_id=RUN-NAV-A" in replay.headers["location"]
    replay_page = test_client.get(replay.headers["location"])
    assert "قبلاً تکمیل شده" in replay_page.text
    assert "TEST-EMPLOYER-UI25-10" in replay_page.text

    rebound = test_client.post(
        "/test/kernel/documents/extract",
        data={
            "case_id": "TEST-NAV-A", "run_id": "RUN-NEW-NOT-AUTHORIZED",
            "document_digest": digest, "lang": "de-DE",
        }, follow_redirects=False,
    )
    assert "error=document_bound_run" in rebound.headers["location"]
    assert "run_id=RUN-NAV-A" in rebound.headers["location"]
    rebound_page = test_client.get(rebound.headers["location"])
    assert "Eine andere Lauf-ID erlaubt keine erneute Verarbeitung" in rebound_page.text
    assert "TEST-EMPLOYER-UI25-10" in rebound_page.text
    assert kernel_counts(database)[:2] == (1, 1)
    store.close()


@pytest.mark.parametrize(("failure", "code", "message"), (
    (SyntheticIncompleteRun("RUN-INCOMPLETE"), "incomplete_run", "ناقص است"),
    (SyntheticPermissionMatrixRejected("denied"), "permission_rejected", "Permission Matrix"),
    (SyntheticKillSwitchRejected("halted"), "kill_switch_rejected", "Kill Switch"),
    (SyntheticBudgetRejected("budget"), "budget_rejected", "بودجه"),
))
def test_typed_execution_denials_have_distinct_localized_messages(
    tmp_path, failure, code, message,
):
    store = FunctionalTestStore(tmp_path / "ui.sqlite3")
    store.create_case("TEST-DENIAL", 2025)
    content = fixture("TEST-EMPLOYER-DENIAL")
    digest = hashlib.sha256(content).hexdigest()
    store.add_document("TEST-DENIAL", "Fixture", content, "text/plain")

    def reject(**_kwargs):
        raise failure

    projection = lambda case_id, year, run_id: KernelRunProjection(
        case_id, year, run_id, "HALTED", (
            KernelTaskProjection("TASK-INCOMPLETE", "IMPLEMENTATION_AGENT", "REGISTERED"),
        ),
    )
    test_client = TestClient(
        create_dashboard_app(
            test_store=store, read_kernel_projection=projection,
            execute_kernel_task=reject,
        ), base_url=ORIGIN, headers={"origin": ORIGIN},
    )
    response = test_client.post(
        "/test/kernel/documents/extract",
        data={
            "case_id": "TEST-DENIAL", "run_id": "RUN-INCOMPLETE",
            "document_digest": digest, "lang": "fa-IR",
        }, follow_redirects=False,
    )
    assert f"error={code}" in response.headers["location"]
    page = test_client.get(response.headers["location"])
    assert message in page.text
    assert "denied" not in page.text
    store.close()


def test_same_run_bound_to_other_case_is_classified_without_leakage(tmp_path):
    store = FunctionalTestStore(tmp_path / "ui.sqlite3")
    store.create_case("TEST-SCOPE-A", 2025)
    store.create_case("TEST-SCOPE-B", 2025)
    a = fixture("TEST-EMPLOYER-A")
    b = fixture("TEST-EMPLOYER-B")
    digest_a = hashlib.sha256(a).hexdigest()
    digest_b = hashlib.sha256(b).hexdigest()
    store.add_document("TEST-SCOPE-A", "A", a, "text/plain")
    store.add_document("TEST-SCOPE-B", "B", b, "text/plain")
    database = tmp_path / "kernel.sqlite3"
    test_client = client(store, database)
    first = test_client.post(
        "/test/kernel/documents/extract",
        data={"case_id": "TEST-SCOPE-A", "run_id": "RUN-SHARED", "document_digest": digest_a},
        follow_redirects=False,
    )
    assert first.status_code == 303
    conflict = test_client.post(
        "/test/kernel/documents/extract",
        data={"case_id": "TEST-SCOPE-B", "run_id": "RUN-SHARED", "document_digest": digest_b},
        follow_redirects=False,
    )
    assert "error=run_scope_conflict" in conflict.headers["location"]
    assert "run_id=RUN-SHARED" not in conflict.headers["location"]
    page = test_client.get(conflict.headers["location"])
    assert "TEST-EMPLOYER-A" not in page.text
    assert kernel_counts(database)[:2] == (1, 1)
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        kernel.verify_audit_chain()
    store.close()
