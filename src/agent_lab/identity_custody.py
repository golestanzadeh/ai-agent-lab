"""Synthetic-only custody topology validation; performs no OS mutations."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

class IdentityCustodyError(RuntimeError): pass

@dataclass(frozen=True,slots=True)
class SyntheticCustodyPlan:
    deployment_id:str; kernel_principal:str; identity_principal:str; recovery_operator:str
    kernel_root:Path; identity_root:Path; key_reference:str
    kernel_backup_root:Path; identity_backup_root:Path

    def validate(self) -> None:
        strings=(self.deployment_id,self.kernel_principal,self.identity_principal,self.recovery_operator,self.key_reference)
        if not all(isinstance(v,str) and v.strip() for v in strings): raise IdentityCustodyError("complete synthetic custody identities required")
        if len({self.kernel_principal,self.identity_principal,self.recovery_operator})!=3: raise IdentityCustodyError("service and recovery principals must be distinct")
        roots=[p.resolve() for p in (self.kernel_root,self.identity_root,self.kernel_backup_root,self.identity_backup_root)]
        if len(set(roots))!=4: raise IdentityCustodyError("Kernel, identity and backup custody roots must be distinct")
        if any(a in b.parents or b in a.parents for i,a in enumerate(roots) for b in roots[i+1:]): raise IdentityCustodyError("custody roots must not be nested")
        if self.key_reference.startswith(("literal:","env-value:")): raise IdentityCustodyError("key material must not appear in configuration")

    def acl_requirements(self) -> dict[str,dict[str,str]]:
        self.validate()
        return {
            str(self.kernel_root.resolve()):{self.kernel_principal:"MODIFY",self.identity_principal:"DENY_WRITE",self.recovery_operator:"READ"},
            str(self.identity_root.resolve()):{self.identity_principal:"MODIFY",self.kernel_principal:"READ",self.recovery_operator:"READ"},
            str(self.kernel_backup_root.resolve()):{self.kernel_principal:"WRITE",self.identity_principal:"DENY",self.recovery_operator:"READ"},
            str(self.identity_backup_root.resolve()):{self.identity_principal:"WRITE",self.kernel_principal:"DENY_WRITE",self.recovery_operator:"READ"},
        }
