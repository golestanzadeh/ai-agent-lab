"""Native Windows Hello ceremonies. No HTTP approval or implicit enrollment.

ABI prefixes are version 1 from Microsoft webauthn.h. Platform attachment and
required UV are mandatory. Returned registration must pass possession verification
before the caller stores any public pin. Cancellation creates no application pin.
"""
import base64
import ctypes as c
import hashlib
import json
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from agent_lab.owner_identity_assertion import (
    RP_ID, ORIGIN, EnrolledOwnerCredential, OwnerAssertionError,
    intent_challenge, verify_challenge_assertion,
)

D=c.c_uint32; B=c.POINTER(c.c_ubyte); W=c.c_wchar_p

class RP(c.Structure):
    _fields_=[('version',D),('id',W),('name',W),('icon',W)]
class User(c.Structure):
    _fields_=[('version',D),('size',D),('id',B),('name',W),('icon',W),('display',W)]
class Parameter(c.Structure):
    _fields_=[('version',D),('type',W),('algorithm',c.c_int32)]
class Parameters(c.Structure):
    _fields_=[('count',D),('items',c.POINTER(Parameter))]
class Credential(c.Structure):
    _fields_=[('version',D),('size',D),('id',B),('type',W)]
class Credentials(c.Structure):
    _fields_=[('count',D),('items',c.POINTER(Credential))]
class Extensions(c.Structure):
    _fields_=[('count',D),('items',c.c_void_p)]
class Client(c.Structure):
    _fields_=[('version',D),('size',D),('json',B),('hash_algorithm',W)]
class MakeOptions(c.Structure):
    _fields_=[('version',D),('timeout',D),('exclude',Credentials),('extensions',Extensions),
              ('attachment',D),('resident',c.c_int32),('uv',D),('attestation',D),('flags',D)]
class GetOptions(c.Structure):
    _fields_=[('version',D),('timeout',D),('allow',Credentials),('extensions',Extensions),
              ('attachment',D),('uv',D),('flags',D),('appid',W),('appid_used',c.POINTER(c.c_int32))]
class Attestation(c.Structure):
    _fields_=[('version',D),('format',W),('auth_size',D),('auth',B),('att_size',D),('att',B),
              ('decode_type',D),('decode',c.c_void_p),('object_size',D),('object',B),('id_size',D),('id',B)]
class Assertion(c.Structure):
    _fields_=[('version',D),('auth_size',D),('auth',B),('sig_size',D),('sig',B),('credential',Credential),('user_size',D),('user',B)]

def _blob(value):
    return (c.c_ubyte*len(value)).from_buffer_copy(value)

def _copy(pointer,size,maximum):
    if not pointer or not 0<size<=maximum:raise OwnerAssertionError('invalid native result length')
    return c.string_at(pointer,size)

def _client(kind,challenge):
    raw=json.dumps(dict(type=kind,challenge=base64.urlsafe_b64encode(challenge).rstrip(b'=').decode(),
                        origin=ORIGIN,crossOrigin=False),separators=(',',':')).encode()
    buffer=_blob(raw)
    return raw,buffer,Client(1,len(raw),buffer,'SHA-256')

def _cose(data):
    """Closed five-field EC2 COSE key; bounded definite integers/byte strings only."""
    if not data or len(data)>256 or data[0]!=0xa5:raise OwnerAssertionError('closed P-256 COSE key required')
    offset=1
    def item():
        nonlocal offset
        if offset>=len(data):raise OwnerAssertionError('truncated COSE key')
        first=data[offset];offset+=1;major=first>>5;value=first&31
        if value==24:
            if offset>=len(data):raise OwnerAssertionError('truncated COSE length')
            value=data[offset];offset+=1
            if value<24:raise OwnerAssertionError('noncanonical COSE length')
        elif value>=24:raise OwnerAssertionError('unsupported COSE length')
        if major in (0,1):return value if major==0 else -1-value
        if major==2 and value<=32 and offset+value<=len(data):
            result=data[offset:offset+value];offset+=value;return result
        raise OwnerAssertionError('invalid COSE value')
    fields={}
    for _ in range(5):
        key=item()
        if type(key) is not int or key in fields:raise OwnerAssertionError('ambiguous COSE key')
        fields[key]=item()
    if offset!=len(data) or set(fields)!={1,3,-1,-2,-3} or fields[1]!=2 or fields[3]!=-7 or fields[-1]!=1:
        raise OwnerAssertionError('unsupported COSE key')
    if any(type(fields[k]) is not bytes or len(fields[k])!=32 for k in (-2,-3)):
        raise OwnerAssertionError('P-256 coordinates required')
    try:return ec.EllipticCurvePublicNumbers(int.from_bytes(fields[-2],'big'),int.from_bytes(fields[-3],'big'),ec.SECP256R1()).public_key()
    except ValueError:raise OwnerAssertionError('invalid P-256 point') from None

def registration_public_key(authenticator_data,credential_id):
    """Validate native registration output, not hardware attestation/trust by itself."""
    data=authenticator_data
    if type(data) is not bytes or not 55<len(data)<=2048 or data[:32]!=hashlib.sha256(RP_ID.encode()).digest() or data[32]!=0x45:
        raise OwnerAssertionError('user-verified device-bound registration required')
    size=int.from_bytes(data[53:55],'big')
    if not 1<=size<=1024 or data[55:55+size]!=credential_id:
        raise OwnerAssertionError('registration credential mismatch')
    return _cose(data[55+size:]).public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)

class WindowsHello:
    def __init__(self,hwnd=None):
        if sys.platform!='win32':raise OwnerAssertionError('Windows Hello requires Windows')
        self.api=c.WinDLL('webauthn.dll')
        user=c.WinDLL('user32.dll');user.GetForegroundWindow.restype=c.c_void_p
        self.hwnd=hwnd or user.GetForegroundWindow()
        if not self.hwnd:raise OwnerAssertionError('interactive Owner window required')
        self.api.WebAuthNAuthenticatorMakeCredential.argtypes=[c.c_void_p,c.POINTER(RP),c.POINTER(User),c.POINTER(Parameters),c.POINTER(Client),c.POINTER(MakeOptions),c.POINTER(c.POINTER(Attestation))]
        self.api.WebAuthNAuthenticatorMakeCredential.restype=c.c_int32
        self.api.WebAuthNAuthenticatorGetAssertion.argtypes=[c.c_void_p,W,c.POINTER(Client),c.POINTER(GetOptions),c.POINTER(c.POINTER(Assertion))]
        self.api.WebAuthNAuthenticatorGetAssertion.restype=c.c_int32
        self.api.WebAuthNFreeCredentialAttestation.argtypes=[c.POINTER(Attestation)]
        self.api.WebAuthNFreeAssertion.argtypes=[c.POINTER(Assertion)]

    @staticmethod
    def _check(code):
        if code:raise OwnerAssertionError('Windows Hello cancelled or denied (HRESULT 0x%08X)'%(code&0xffffffff))

    def register(self,owner_id,challenge):
        if type(challenge) is not bytes or len(challenge)!=32:raise OwnerAssertionError('registration challenge required')
        raw,buffer,client=_client('webauthn.create',challenge)
        user_id=_blob(hashlib.sha256(owner_id.encode()).digest())
        rp=RP(1,RP_ID,'AI-Tax-Agent',None)
        user=User(1,32,user_id,'AI-Tax-Agent Owner',None,'AI-Tax-Agent Owner')
        parameter=Parameter(1,'public-key',-7);parameters=Parameters(1,c.pointer(parameter))
        options=MakeOptions(1,120000,Credentials(),Extensions(),1,0,1,1,0)
        result=c.POINTER(Attestation)()
        try:
            self._check(self.api.WebAuthNAuthenticatorMakeCredential(self.hwnd,c.byref(rp),c.byref(user),c.byref(parameters),c.byref(client),c.byref(options),c.byref(result)))
            data=result.contents
            credential=_copy(data.id,data.id_size,1024)
            auth=_copy(data.auth,data.auth_size,2048)
            return credential,registration_public_key(auth,credential)
        finally:
            if result:self.api.WebAuthNFreeCredentialAttestation(result)

    def assert_intent(self,intent,credential_id):
        return self.assert_challenge(intent_challenge(intent),credential_id)

    def assert_challenge(self,challenge,credential_id):
        raw,buffer,client=_client('webauthn.get',challenge)
        key_id=_blob(credential_id);credential=Credential(1,len(credential_id),key_id,'public-key')
        options=GetOptions(1,120000,Credentials(1,c.pointer(credential)),Extensions(),1,1,0,None,None)
        result=c.POINTER(Assertion)()
        try:
            self._check(self.api.WebAuthNAuthenticatorGetAssertion(self.hwnd,RP_ID,c.byref(client),c.byref(options),c.byref(result)))
            data=result.contents
            if data.credential.type!='public-key':raise OwnerAssertionError('native credential type mismatch')
            return dict(credential_id=_copy(data.credential.id,data.credential.size,1024),client_data_json=raw,
                        authenticator_data=_copy(data.auth,data.auth_size,2048),signature=_copy(data.sig,data.sig_size,80))
        finally:
            if result:self.api.WebAuthNFreeAssertion(result)

def enroll_with_possession(*,native,owner_id,challenge,nonce):
    """Two native ceremonies; no pin is returned unless fresh possession verifies.

    Registration uses the exact scoped challenge; a second required-UV assertion
    independently verifies the extracted public key and current private possession.
    No hardware/vendor attestation or real person identity is inferred.
    """
    credential,public=native.register(owner_id,challenge)
    enrollment=EnrolledOwnerCredential(owner_id,credential,public,0)
    proof=verify_challenge_assertion(challenge=challenge,nonce=nonce,owner_id=owner_id,
        enrollment=enrollment,**native.assert_challenge(challenge,credential))
    return enrollment,proof
