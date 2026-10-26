from dataclasses import replace
import pytest

from agent_lab.runtime_activation import CONFIG_FIELDS,GATES,RuntimeActivationConfiguration,ReadinessStatus
from agent_lab.case_persistence import SQLiteCasePersistence
from test_production_runtime import KEY,OWNER,seed,compose


def configuration(**changes):
    payload={"schema":"ai-tax-agent.runtime-activation-preparation/1.0","deployment_id":"DEPLOYMENT-A",
             "owner_id":OWNER,"case_id":"CASE-2023-A","tax_year":2023,"run_id":"RUN-REAL-PERSISTED",
             "references":{key:"sha256:"+"a"*64 for key in CONFIG_FIELDS}}
    payload.update(changes)
    return RuntimeActivationConfiguration.parse(payload)


def test_configuration_is_closed_nonsecret_and_deterministic():
    assert configuration()==configuration()
    for changes in ({"api_key":"secret"},{"tax_year":True},{"schema":"unknown"},{"references":{"password":"secret"}}):
        with pytest.raises(ValueError): configuration(**changes)


def test_direct_constructor_rejects_raw_secrets_oversize_and_forged_digest():
    valid=configuration()
    for changes in (
        {"deployment_id":"D"*1000},
        {"references":tuple((key,"raw-secret-value") for key in CONFIG_FIELDS)},
        {"digest":"forged-digest"},
        {"references":valid.references+(valid.references[0],)},
    ):
        with pytest.raises(ValueError): replace(valid,**changes)


def test_readiness_has_exact_scopes_no_mutations_and_never_enables_protected_operations(tmp_path):
    store=SQLiteCasePersistence(tmp_path/"cases.sqlite",integrity_key=KEY);seed(store)
    runtime,identity,kernel=compose(tmp_path,store)
    before=store._db.execute("SELECT count(*) FROM case_audit").fetchone()[0]
    scope={"case_id":"CASE-2023-A","tax_year":2023,"run_id":"RUN-REAL-PERSISTED"}
    missing=runtime.assess_readiness(**scope)
    assert missing[0].status is ReadinessStatus.READY
    assert all(item.status is ReadinessStatus.CONFIGURATION_MISSING for item in missing[1:])
    authority=runtime.assess_readiness(configuration(),**scope)
    assert all(item.status is ReadinessStatus.AUTHORITY_MISSING for item in authority[1:])
    refs={gate.operation:"sha256:"+"b"*64 for gate in GATES}
    blocked=runtime.assess_readiness(configuration(),authority_references=refs,**scope)
    assert all(item.status is ReadinessStatus.SECURITY_GATE_BLOCKED and not item.executable for item in blocked[1:])
    assert store._db.execute("SELECT count(*) FROM case_audit").fetchone()[0]==before
    tampered=configuration()
    object.__setattr__(tampered,"digest","forged-digest")
    with pytest.raises(ValueError,match="digest mismatch"):
        runtime.assess_readiness(tampered,**scope)
    for wrong in (configuration(owner_id="OTHER"),configuration(case_id="CASE-2023-B"),configuration(tax_year=2028),configuration(run_id="OTHER-RUN")):
        with pytest.raises(PermissionError): runtime.assess_readiness(wrong,**scope)
    with pytest.raises(PermissionError): runtime.assess_readiness(configuration(),case_id="CASE-2023-A",tax_year=2023,run_id="UNKNOWN")
    identity.close();kernel.close();store.close()


def test_readiness_restart_and_explicit_reconciliation(tmp_path):
    path=tmp_path/"cases.sqlite";store=SQLiteCasePersistence(path,integrity_key=KEY);seed(store)
    runtime,identity,kernel=compose(tmp_path,store)
    args={"case_id":"CASE-2023-A","tax_year":2023,"run_id":"RUN-REAL-PERSISTED"}
    first=runtime.assess_readiness(configuration(),**args)
    identity.close();kernel.close();store.close()
    store=SQLiteCasePersistence(path,integrity_key=KEY);runtime,identity,kernel=compose(tmp_path,store)
    assert runtime.assess_readiness(configuration(),**args)==first
    runtime.storage_requires_reconciliation=lambda case_id,tax_year:True
    assert all(item.status is ReadinessStatus.RECONCILIATION_REQUIRED for item in runtime.assess_readiness(configuration(),**args)[1:])
    identity.close();kernel.close();store.close()
