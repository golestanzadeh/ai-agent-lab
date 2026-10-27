"""SCM composition seam remains fail-closed unless explicitly injected."""
import inspect

from agent_lab.c09_service_host import run_scm_service, unavailable_runtime


def test_scm_runtime_factory_is_explicit_and_defaults_to_none():
    signature = inspect.signature(run_scm_service)
    assert signature.parameters["runtime_factory"].default is None


def test_unavailable_runtime_still_denies_implicit_activation():
    from agent_lab.c09_service_host import ServiceHostError
    import pytest
    with pytest.raises(ServiceHostError, match="not implemented"):
        unavailable_runtime(None)
