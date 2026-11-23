"""Distinct application signing keys under existing per-user DPAPI custody.

No automatic startup creation: explicit approved enrollment calls provisioning.
Load never repairs/regenerates a missing key. This is not independent Witness
custody and makes no same-user malware isolation claim.
"""
import json
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from agent_lab.owner_identity_broker import APPROVAL
from agent_lab.owner_identity_assertion import OwnerAssertionError

ROLES=frozenset({'kernel','identity'})

def _path(root,role):
    if role not in ROLES:raise OwnerAssertionError('closed application key role required')
    return Path(root)/('owner-'+role+'-signing.dpapi')

def load_key(root,*,role,owner_id):
    import win32crypt
    path=_path(root,role)
    if not path.is_file():raise OwnerAssertionError('enrolled application key missing; no regeneration')
    raw=win32crypt.CryptUnprotectData(path.read_bytes(),('AI-Tax-Agent:'+role).encode(),None,None,0)[1]
    payload=json.loads(raw)
    if set(payload)!={'contract','role','owner_id','private_der'} or payload['contract']!='ai-tax-agent.option-b-key/1' or (payload['role'],payload['owner_id'])!=(role,owner_id):
        raise OwnerAssertionError('application key custody binding mismatch')
    key=serialization.load_der_private_key(bytes.fromhex(payload['private_der']),password=None)
    if not isinstance(key,ec.EllipticCurvePrivateKey) or not isinstance(key.curve,ec.SECP256R1):raise OwnerAssertionError('P-256 application key required')
    return key

def provision_keys(root,*,owner_id,approval):
    import win32crypt
    if approval!=APPROVAL:raise OwnerAssertionError('explicit key enrollment authorization required')
    if not Path(root).is_dir():raise OwnerAssertionError('existing application key directory required')
    for role in sorted(ROLES):
        path=_path(root,role)
        if not path.exists():
            key=ec.generate_private_key(ec.SECP256R1())
            raw=json.dumps(dict(contract='ai-tax-agent.option-b-key/1',role=role,owner_id=owner_id,
                private_der=key.private_bytes(serialization.Encoding.DER,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).hex())).encode()
            sealed=win32crypt.CryptProtectData(raw,'AI-Tax-Agent '+role,('AI-Tax-Agent:'+role).encode(),None,None,0)
            # Exclusive creation, no overwrite after a concurrent enrollment.
            try:
                with path.open('xb') as handle:
                    handle.write(sealed);handle.flush()
                    import os
                    os.fsync(handle.fileno())
            except FileExistsError:pass
        load_key(root,role=role,owner_id=owner_id)
