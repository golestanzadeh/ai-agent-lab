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


def test_local_prerequisite_order_is_diagnostic_only(tmp_path):
    from agent_lab.option_b_family_binding import local_family_prerequisite
    expected=[('identity.sqlite','FAMILY_CANONICAL_IDENTITY_ENROLLMENT_REQUIRED'),
        ('owner-kernel-signing.dpapi','FAMILY_KERNEL_KEY_ENROLLMENT_REQUIRED'),
        ('owner-identity-signing.dpapi','FAMILY_IDENTITY_KEY_ENROLLMENT_REQUIRED'),
        ('family-runtime-binding.json','FAMILY_ACCEPTED_DEPLOYMENT_BINDING_REQUIRED')]
    for name,code in expected:
        assert local_family_prerequisite(tmp_path)==code
        (tmp_path/name).write_bytes(b'not authority')
    assert local_family_prerequisite(tmp_path)=='FAMILY_ACCEPTED_RUNTIME_PORTS_REQUIRED'


def test_local_prerequisite_http_header_is_closed_and_private():
    async def check():
        app=create_dashboard_app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://127.0.0.1:8766') as client:
            app.state.family_blocker='FAMILY_CANONICAL_IDENTITY_ENROLLMENT_REQUIRED'
            result=await client.get('/family/persons')
            assert result.status_code==503
            assert result.headers['x-family-blocker']==app.state.family_blocker
            app.state.family_blocker='secret arbitrary exception'
            result=await client.get('/family/persons')
            assert result.headers['x-family-blocker']=='FAMILY_RUNTIME_BINDING_REQUIRED'
            assert 'secret' not in result.text
    asyncio.run(check())
