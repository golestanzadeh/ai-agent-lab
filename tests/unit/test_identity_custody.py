from pathlib import Path
import pytest
from agent_lab.identity_custody import IdentityCustodyError,SyntheticCustodyPlan

def plan(tmp_path,**changes):
    values=dict(deployment_id="SYNTHETIC-DEPLOYMENT",kernel_principal="SYNTHETIC\\kernel",identity_principal="SYNTHETIC\\identity",recovery_operator="SYNTHETIC\\recovery",kernel_root=tmp_path/"kernel",identity_root=tmp_path/"identity",key_reference="synthetic-keystore://identity-hmac",kernel_backup_root=tmp_path/"kernel-backup",identity_backup_root=tmp_path/"identity-backup")
    values.update(changes); return SyntheticCustodyPlan(**values)

def test_synthetic_custody_separation_and_acl_contract(tmp_path):
    result=plan(tmp_path); result.validate(); acl=result.acl_requirements(); assert acl[str((tmp_path/"kernel").resolve())][result.identity_principal]=="DENY_WRITE"

def test_rejects_shared_principal_nested_roots_and_literal_key(tmp_path):
    with pytest.raises(IdentityCustodyError): plan(tmp_path,identity_principal="SYNTHETIC\\kernel").validate()
    with pytest.raises(IdentityCustodyError): plan(tmp_path,identity_root=tmp_path/"kernel"/"identity").validate()
    with pytest.raises(IdentityCustodyError): plan(tmp_path,key_reference="literal:secret").validate()
