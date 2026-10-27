"""Compose existing SCM roles with their authorities; never install or enroll.

Factories are supplied by the governed deployment composition, not requests or
environment variables. SQLite authorities are opened and used on one worker.
"""
from __future__ import annotations

import threading
from agent_lab.c09_service_host import (
    ROLE_BINDINGS, ServiceRole, ServiceHost, ServiceHostError, current_process_sid,
)
from agent_lab.c09_named_pipe import (
    IDENTITY_PIPE, CUSTODIAN_PIPE, MAX_FRAME_BYTES, create_kernel_only_server,
    authorize_connected_kernel,
)
from agent_lab.c09_pipe_transport import OperationDeadline, PipeDeadlineError, overlapped_io


class AuthorityPipeRuntime:
    """One first-instance endpoint, one existing authority, bounded shutdown."""
    def __init__(self, config, authority_factory, *, allowed_case_ids=frozenset()):
        if config.role not in {ServiceRole.IDENTITY,ServiceRole.KEY_CUSTODIAN}:
            raise ServiceHostError("authority role required")
        name,sid=ROLE_BINDINGS[config.role]
        if (config.schema!="ai-tax-agent.c09-service-config/1.0" or
            config.service_name!=name or config.principal_sid!=sid or config.enabled is not True or
            not isinstance(config.deployment_id,str) or not config.deployment_id):
            raise ServiceHostError("closed deployment binding required")
        if not isinstance(allowed_case_ids,frozenset) or any(not isinstance(v,str) or not v or v=="*" for v in allowed_case_ids):
            raise ServiceHostError("explicit case allowlist required")
        self._config=config;self._factory=authority_factory;self._cases=allowed_case_ids
        self._stop=threading.Event();self._ready=threading.Event();self._thread=None
        self._error=None;self._handle=None;self._connection_error=None

    def start(self):
        if self._thread is not None:raise ServiceHostError("runtime already started")
        if current_process_sid()!=self._config.principal_sid:
            raise ServiceHostError("actual authority service token required before opening store")
        pipe=IDENTITY_PIPE if self._config.role is ServiceRole.IDENTITY else CUSTODIAN_PIPE
        self._handle=create_kernel_only_server(pipe,overlapped=True)
        self._thread=threading.Thread(target=self._serve,name=self._config.service_name,daemon=True)
        self._thread.start()
        if not self._ready.wait(6):
            self._stop.set()
            raise ServiceHostError("authority startup did not complete; reconciliation required")
        if self._error is not None:
            self._thread.join(1)
            raise ServiceHostError("authority startup failed closed") from self._error

    def _serve(self):
        import pywintypes
        import win32file
        import win32pipe
        from agent_lab.identity_persistence import IdentityPersistence
        from agent_lab.c09_custodian_operational import OperationalCustodianRuntime
        from agent_lab.c09_identity_dispatch import dispatch_stateful_identity_read
        from agent_lab.ipc_wire_primitives import decode_frame,encode_frame
        authority=None
        try:
            authority=self._factory(self._config)
            if self._config.role is ServiceRole.IDENTITY:
                if not isinstance(authority,IdentityPersistence):raise ServiceHostError("existing Identity authority required")
                logical=authority._logical_row()
                if logical is None or logical["deployment_id"]!=self._config.deployment_id:
                    raise ServiceHostError("explicit matching enrollment required; never initialize here")
            else:
                if not isinstance(authority,OperationalCustodianRuntime) or authority._deployment!=self._config.deployment_id:
                    raise ServiceHostError("matching existing Custodian authority required")
                authority.start()
            self._ready.set()
            while not self._stop.is_set():
                connected=False
                try:
                    try:
                        overlapped_io(self._handle,lambda ov:win32pipe.ConnectNamedPipe(self._handle,ov),OperationDeadline(5,self._stop))
                    except pywintypes.error as exc:
                        if exc.winerror!=535:raise
                    connected=True
                    deadline=OperationDeadline(5,self._stop)
                    def read_message(bound):
                        result,count=overlapped_io(self._handle,lambda ov:win32file.ReadFile(self._handle,bound,ov),deadline)
                        return bytes(result[1][:count])
                    # Impersonation uses the last message read by this pipe.
                    # Buffer bounded opaque bytes first; authenticate actual token
                    # and revert before any decoding, signature or domain work.
                    raw=read_message(MAX_FRAME_BYTES+1)
                    authorize_connected_kernel(self._handle)
                    if self._config.role is ServiceRole.IDENTITY:
                        reply=dispatch_stateful_identity_read(self._handle,lambda bound:raw,authority,allowed_case_ids=self._cases)
                    else:
                        reply=encode_frame(authority.handle(decode_frame(raw)))
                    _,count=overlapped_io(self._handle,lambda ov:win32file.WriteFile(self._handle,reply,ov),deadline)
                    if count!=len(reply):raise ServiceHostError("partial authority response")
                    # A write completion can precede peer consumption. Wait for
                    # peer close before DisconnectNamedPipe discards queued bytes.
                    try:
                        extra,received=overlapped_io(self._handle,lambda ov:win32file.ReadFile(self._handle,1,ov),deadline)
                        raise ServiceHostError("one request per connection required")
                    except pywintypes.error as exc:
                        if exc.winerror not in (109,232,233):raise
                except PipeDeadlineError:
                    from agent_lab.c09_pipe_transport import _halted
                    if _halted.is_set():raise ServiceHostError("native cancellation not acknowledged; host halted")
                except (ValueError,PermissionError):
                    # Malformed/unauthorized input confers no authority or reply.
                    pass
                except Exception as exc:
                    # Authenticator/dispatcher errors also deny this connection.
                    # Store corruption is rechecked by every authority operation.
                    if not connected:raise
                    self._connection_error=exc
                finally:
                    if connected:
                        try:win32pipe.DisconnectNamedPipe(self._handle)
                        except pywintypes.error:pass
        except BaseException as exc:self._error=exc
        finally:
            self._ready.set()
            if authority is not None:
                try:authority.close()
                except Exception:self._error=self._error or ServiceHostError("authority close failed")
            if self._handle is not None:
                from agent_lab.c09_pipe_transport import _quarantined
                if not any(entry[0]==self._handle for entry in _quarantined):win32file.CloseHandle(self._handle)
                self._handle=None

    def stop(self):
        self._stop.set()
        if self._thread is None:return
        self._thread.join(7)
        if self._thread.is_alive():raise ServiceHostError("authority shutdown incomplete; host halted")
        if self._error is not None:raise ServiceHostError("authority runtime halted") from self._error

    def check_health(self):
        if self._thread is None or not self._thread.is_alive() or self._error is not None:
            raise ServiceHostError("authority worker is not running")


def create_identity_service_host(authority_factory,*,allowed_case_ids):
    return ServiceHost(ServiceRole.IDENTITY,lambda config:AuthorityPipeRuntime(config,authority_factory,allowed_case_ids=allowed_case_ids))


def create_custodian_service_host(authority_factory):
    return ServiceHost(ServiceRole.KEY_CUSTODIAN,lambda config:AuthorityPipeRuntime(config,authority_factory))


class KernelIdentityServiceClient:
    """Existing Kernel coordinates proof, Identity read, Witness, then release.

No UI-provided proof, callback head or authentication boolean is accepted.
This interface does not dispatch agents or enable any domain mutation.
"""
    def __init__(self,kernel,*,deployment_id,identity_server,custodian,provider,signing_key,key_id):
        from agent_lab.orchestrator_kernel import OrchestratorKernel
        from agent_lab.c09_named_pipe import PinnedProcess
        from agent_lab.c09_custodian_operational import CustodianServiceClient
        from agent_lab.c09_gcs_witness_adapter import GCSWitnessAdapter
        from cryptography.hazmat.primitives.asymmetric import ec
        if not isinstance(kernel,OrchestratorKernel):raise ServiceHostError("existing Kernel required")
        if not isinstance(identity_server,PinnedProcess) or identity_server.sid!=ROLE_BINDINGS[ServiceRole.IDENTITY][1]:raise ServiceHostError("pinned Identity principal required")
        if not isinstance(custodian,CustodianServiceClient) or custodian.deployment_id!=deployment_id or not isinstance(provider,GCSWitnessAdapter):raise ServiceHostError("concrete deployment ports required")
        if not isinstance(signing_key,ec.EllipticCurvePrivateKey) or not isinstance(signing_key.curve,ec.SECP256R1) or not isinstance(key_id,str) or not key_id:raise ServiceHostError("protected Kernel signer binding required")
        self._kernel=kernel;self._deployment=deployment_id;self._identity=identity_server
        self._custodian=custodian;self._provider=provider;self._signer=signing_key;self._key_id=key_id

    def read(self,*,manifest_id,task_id,run_id,case_id,tax_year,operation,payload,authorization_references,transaction_id=None,cancellation=None):
        from datetime import datetime,timezone
        from agent_lab.c09_identity_client import exchange_operational_identity_read
        from agent_lab.ipc_wire_primitives import encode_frame
        request=self._kernel.issue_identity_read(deployment_id=self._deployment,manifest_id=manifest_id,task_id=task_id,run_id=run_id,case_id=case_id,tax_year=tax_year,operation=operation,payload=payload,authorization_references=authorization_references,transaction_id=transaction_id,signing_key=self._signer,key_id=self._key_id)
        state=self._kernel._identity_payload("identity_kernel_state","deployment_id",self._deployment)
        scope={name:request[name] for name in "deployment_id case_id tax_year run_id task_id manifest_id actor_instance_id role_id".split()}
        deadline=OperationDeadline(5,cancellation)
        response=exchange_operational_identity_read(encode_frame(request),self._identity,self._signer.public_key(),expected_scope=scope,now=datetime.now(timezone.utc).replace(tzinfo=None),expected_key_id=self._key_id,deadline=deadline,contract_version="oi0002.kernel-identity-c09/1.1",bootstrap_artifact=state["artifact"] if request["message_type"]=="GET_ENROLLMENT_STATUS" else None)
        deadline.milliseconds()
        if response["outcome"] in {"DENIED","CONFLICT"}:return response
        pending=self._kernel.stage_identity_audit_checkpoint(request,response)
        deadline.milliseconds()
        result=self._kernel.witness_identity_checkpoint(pending["receipt"]["checkpoint_id"],custodian=self._custodian,provider=self._provider,signing_key=self._signer,kernel_key_id=self._key_id)
        deadline.milliseconds()  # A cancelled caller cannot publish a held result.
        return result

    def reconcile(self,checkpoint_id):
        """Retry exact held checkpoint; never dispatch Identity a second time."""
        return self._kernel.witness_identity_checkpoint(checkpoint_id,custodian=self._custodian,provider=self._provider,signing_key=self._signer,kernel_key_id=self._key_id)


class KernelServiceRuntime:
    """SCM lifetime for the existing Kernel and concrete Identity service client."""
    def __init__(self,config,kernel_factory,*,identity_server,custodian,provider,signing_key,key_id):
        name,sid=ROLE_BINDINGS[ServiceRole.KERNEL]
        if (config.schema!="ai-tax-agent.c09-service-config/1.0" or config.role is not ServiceRole.KERNEL or
            config.service_name!=name or config.principal_sid!=sid or config.enabled is not True or
            not isinstance(config.deployment_id,str) or not config.deployment_id or len(config.deployment_id.encode())>128):
            raise ServiceHostError("fixed Kernel deployment required")
        self._config=config;self._factory=kernel_factory;self._kernel=None;self.client=None
        self._bindings=dict(identity_server=identity_server,custodian=custodian,provider=provider,signing_key=signing_key,key_id=key_id)

    def start(self):
        if self._kernel is not None or current_process_sid()!=self._config.principal_sid:
            raise ServiceHostError("actual Kernel service token required before store access")
        kernel=self._factory(self._config)
        try:
            client=KernelIdentityServiceClient(kernel,deployment_id=self._config.deployment_id,**self._bindings)
            kernel.verify_audit_chain();kernel._verify_identity_protocol_state()
        except BaseException:kernel.close();raise
        self._kernel=kernel;self.client=client

    def check_health(self):
        if self._kernel is None:raise ServiceHostError("Kernel is stopped")
        self._kernel.verify_audit_chain();self._kernel._verify_identity_protocol_state()

    def stop(self):
        self.client=None
        if self._kernel is not None:self._kernel.close();self._kernel=None


def create_kernel_service_host(kernel_factory,**bindings):
    return ServiceHost(ServiceRole.KERNEL,lambda config:KernelServiceRuntime(config,kernel_factory,**bindings))
