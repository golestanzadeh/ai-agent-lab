"""Precise missing-composition diagnostics, without starting any authority."""
import asyncio

import httpx
import pytest

from agent_lab.ui_dashboard import create_dashboard_app


@pytest.mark.parametrize("path", ["/family/persons", "/family/pending"])
def test_unbound_family_reports_configuration_not_sqlite_failure(path):
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_dashboard_app()),
                base_url="http://127.0.0.1:8766") as client:
            response = await client.get(path)
            assert response.status_code == 503
            assert response.json() == {"detail": "FAMILY_AUTHORIZED_RUNTIME_UNAVAILABLE"}
            assert response.headers["x-family-readiness"] == "CONFIGURATION_MISSING"
            assert response.headers["x-family-blocker"] == "FAMILY_RUNTIME_BINDING_REQUIRED"
            assert response.headers["cache-control"] == "no-store"
    asyncio.run(check())


@pytest.mark.parametrize("attack", ["host", "origin", "remote"])
def test_diagnostics_do_not_relax_family_loopback_guards(attack):
    async def check():
        headers = {"Host": "hostile.invalid"} if attack == "host" else {}
        if attack == "origin":headers["Origin"] = "https://hostile.invalid"
        peer = ("192.0.2.1", 1000) if attack == "remote" else ("127.0.0.1", 1000)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_dashboard_app(), client=peer),
                base_url="http://127.0.0.1:8766") as client:
            response = await client.get("/family/persons", headers=headers)
            assert response.status_code == 403
            assert "x-family-blocker" not in response.headers
    asyncio.run(check())
