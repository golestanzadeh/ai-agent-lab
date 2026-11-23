"""Closed Kernel-signed delivery of durable Owner approval to Identity.

Identity trusts its EXISTING pinned Kernel key, not a caller-selected Owner key.
The distinct Windows Hello assertion credential is carried under that authority;
it is not equated with the constitutional continuity/restore signing key.
"""
import base64
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec,utils
from agent_lab.ipc_wire_primitives import canonical_json_bytes as C
from agent_lab.owner_identity_assertion import P256_ORDER,OwnerAssertionError

DOMAIN=b'AI-TAX-AGENT\0OWNER-APPROVAL-DELIVERY\0V1\0'
FIELDS={'contract','key_id','deployment_id','store_id','approval_status','approval','intent','assertion','owner_credential'}
def digest(value):return 'sha256:'+hashlib.sha256(C(value)).hexdigest()

def sign(payload,key):
    if set(payload)!=FIELDS:raise OwnerAssertionError('closed Kernel Owner approval delivery required')
    r,s=utils.decode_dss_signature(key.sign(DOMAIN+C(payload),ec.ECDSA(hashes.SHA256(),deterministic_signing=True)))
    return {**payload,'signature':base64.b64encode(utils.encode_dss_signature(r,min(s,P256_ORDER-s))).decode()}

def verify(delivery,*,kernel_public_key,key_id,deployment_id,store_id):
    if type(delivery) is not dict or set(delivery)!=FIELDS|{'signature'}:
        raise OwnerAssertionError('signed Kernel approval delivery required')
    payload={k:v for k,v in delivery.items() if k!='signature'}
    if (payload['contract'],payload['key_id'],payload['deployment_id'],payload['store_id'])!=('ai-tax-agent.owner-approval-delivery/1',key_id,deployment_id,store_id):
        raise OwnerAssertionError('Kernel approval delivery scope mismatch')
    if payload['approval_status']!='APPROVED':raise OwnerAssertionError('durable approved Kernel nonce required')
    try:
        signature=base64.b64decode(delivery['signature'],validate=True)
        r,s=utils.decode_dss_signature(signature)
        if not 0<r<P256_ORDER or not 0<s<=P256_ORDER//2 or utils.encode_dss_signature(r,s)!=signature:raise ValueError()
        kernel_public_key.verify(signature,DOMAIN+C(payload),ec.ECDSA(hashes.SHA256()))
    except Exception:raise OwnerAssertionError('Kernel approval delivery signature denied') from None
    return payload
